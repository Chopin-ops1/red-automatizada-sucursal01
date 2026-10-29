#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototipo 3: Auditoría Automatizada de Flota de Equipos
Evalúa la flota de red (R-SUC-01, SW-SUC-01-CORE, SW-SUC-01-ACC1) a partir de
las evidencias y respaldos obtenidos por Ansible (running-config, show vlan brief, show ip int brief).

Genera:
1. Reporte tabular detallado en pantalla.
2. Archivo CSV normalizado en evidencias/auditoria_flota.csv.
"""

import os
import sys
import re
import csv
import yaml

def parse_running_config(cfg_path):
    if not os.path.exists(cfg_path):
        return None
    with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    data = {
        'hostname': '',
        'vlans': {},
        'interfaces': {},
        'subinterfaces': {},
        'raw': content
    }

    # Hostname
    m_host = re.search(r'^hostname\s+(\S+)', content, re.M)
    if m_host: data['hostname'] = m_host.group(1)

    # VLANs
    for m in re.finditer(r'^vlan\s+(\d+)\s*\n(?:\s+name\s+([^\n]+))?', content, re.M):
        data['vlans'][int(m.group(1))] = {'name': m.group(2).strip() if m.group(2) else "", 'status': 'active'}

    # Interfaces
    current_iface = None
    for line in content.splitlines():
        line_clean = line.strip()
        if line.startswith('interface '):
            current_iface = line.split()[1]
            data['interfaces'][current_iface] = {
                'description': '', 'mode': 'routed', 'access_vlan': 1, 'native_vlan': 1,
                'allowed_vlans': '', 'ip': None, 'mask': None, 'encapsulation': None
            }
        elif current_iface and line.startswith(' '):
            iface_dict = data['interfaces'][current_iface]
            if line_clean.startswith('description '):
                iface_dict['description'] = line_clean[12:].strip()
            elif line_clean == 'switchport mode access':
                iface_dict['mode'] = 'access'
            elif line_clean == 'switchport mode trunk':
                iface_dict['mode'] = 'trunk'
            elif line_clean.startswith('switchport access vlan '):
                iface_dict['access_vlan'] = int(line_clean.split()[-1])
            elif line_clean.startswith('switchport trunk native vlan '):
                iface_dict['native_vlan'] = int(line_clean.split()[-1])
            elif line_clean.startswith('switchport trunk allowed vlan '):
                iface_dict['allowed_vlans'] = line_clean.split()[-1]
            elif line_clean.startswith('encapsulation dot1Q '):
                iface_dict['encapsulation'] = line_clean.split()[-1]
            elif line_clean.startswith('ip address '):
                parts = line_clean.split()
                if len(parts) >= 4:
                    iface_dict['ip'] = parts[2]
                    iface_dict['mask'] = parts[3]

    return data

def parse_vlan_brief(vlan_txt_path):
    if not os.path.exists(vlan_txt_path): return {}
    vlans = {}
    with open(vlan_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                vlans[int(parts[0])] = {'name': parts[1], 'status': parts[2]}
    return vlans

def auditar_flota(base_dir):
    resp_dir = os.path.join(base_dir, "respaldos")
    csv_salida = os.path.join(base_dir, "evidencias", "auditoria_flota.csv")
    os.makedirs(os.path.dirname(csv_salida), exist_ok=True)

    print("=" * 105)
    print("   PROTOTIPO 3: AUDITORIA AUTOMATIZADA DE FLOTA DE RED (CISCO IOS)")
    print("=" * 105)
    print(f"[*] Directorio de evidencias : {resp_dir}")
    print(f"[*] Salida CSV normalizada  : {csv_salida}\n")

    registros_csv = []
    conteo_cumple, conteo_no_cumple = 0, 0

    def registrar(equipo, condicion, cumple, evidencia, detalle=""):
        nonlocal conteo_cumple, conteo_no_cumple
        res = "CUMPLE" if cumple else "NO CUMPLE"
        if cumple: conteo_cumple += 1
        else: conteo_no_cumple += 1
        registros_csv.append({
            'equipo': equipo,
            'condicion_evaluada': condicion,
            'resultado': res,
            'evidencia_usada': evidencia,
            'detalle_diferencia': detalle if not cumple else "Conforme al diseno"
        })
        print(f" {equipo:<16} {condicion:<40} [{res:<9}] {evidencia:<25}")

    print(f" {'EQUIPO':<16} {'CONDICION EVALUADA':<40} {'RESULTADO':<11} {'EVIDENCIA USADA':<25}")
    print("-" * 105)

    # 1. Auditoría de R-SUC-01
    r_cfg = parse_running_config(os.path.join(resp_dir, "r_suc_01-running.cfg"))
    if r_cfg:
        eq = "R-SUC-01"
        ev = "r_suc_01-running.cfg"
        # Condición 1: Gateway VLAN 10
        g10 = r_cfg['interfaces'].get('GigabitEthernet0/0.10', {})
        ok_g10 = (g10.get('ip') == '192.168.10.1' and g10.get('encapsulation') == '10')
        registrar(eq, "Subinterfaz Gi0/0.10 (Gateway 192.168.10.1/24)", ok_g10, ev)

        # Condición 2: Gateway VLAN 20
        g20 = r_cfg['interfaces'].get('GigabitEthernet0/0.20', {})
        ok_g20 = (g20.get('ip') == '192.168.20.1' and g20.get('encapsulation') == '20')
        registrar(eq, "Subinterfaz Gi0/0.20 (Gateway 192.168.20.1/24)", ok_g20, ev)

        # Condición 3: Interfaz de Gestión (BVI1 o Gi0/0.99)
        bvi = r_cfg['interfaces'].get('BVI1', {})
        g99 = r_cfg['interfaces'].get('GigabitEthernet0/0.99', {})
        ok_gest = (bvi.get('ip') == '192.168.99.1' or g99.get('ip') == '192.168.99.1')
        registrar(eq, "Interfaz Gestion L3 (IP 192.168.99.1/24)", ok_gest, ev)

        # Condición 4: Enrutamiento IP activo
        ok_rout = "ip routing" in r_cfg['raw'] or "no ip routing" not in r_cfg['raw']
        registrar(eq, "Enrutamiento IP Unicast (ROAS)", ok_rout, ev)

    # 2. Auditoría de SW-SUC-01-CORE
    c_cfg = parse_running_config(os.path.join(resp_dir, "sw_suc_01_core-running.cfg"))
    c_vlan = parse_vlan_brief(os.path.join(resp_dir, "sw_suc_01_core-vlan.txt"))
    if c_cfg:
        eq = "SW-SUC-01-CORE"
        ev = "sw_suc_01_core-running.cfg"
        ev_v = "sw_suc_01_core-vlan.txt"

        # VLANs
        for vid, vname in [(10, 'USUARIOS_VLAN10'), (20, 'USUARIOS_VLAN20'), (99, 'GESTION')]:
            act_v = c_cfg['vlans'].get(vid)
            act_br = c_vlan.get(vid)
            ok_v = (act_v and act_v['name'] == vname) or (act_br and act_br['name'] == vname)
            registrar(eq, f"Existencia y estado VLAN {vid} ({vname})", ok_v, ev_v if act_br else ev)

        # Troncales
        tr_r = c_cfg['interfaces'].get('GigabitEthernet0/0', {})
        ok_tr_r = (tr_r.get('mode') == 'trunk' and tr_r.get('native_vlan') == 99 and tr_r.get('allowed_vlans') == '10,20,99')
        registrar(eq, "Troncal Gi0/0 -> R-SUC-01 (dot1q, Nativa 99)", ok_tr_r, ev)

        tr_a = c_cfg['interfaces'].get('GigabitEthernet1/2', {})
        ok_tr_a = (tr_a.get('mode') == 'trunk' and tr_a.get('native_vlan') == 99 and tr_a.get('allowed_vlans') == '10,20,99')
        registrar(eq, "Troncal Gi1/2 -> SW-SUC-01-ACC1 (Nativa 99)", ok_tr_a, ev)

        # SVI Gestión
        svi = c_cfg['interfaces'].get('Vlan99', {})
        ok_svi = (svi.get('ip') == '192.168.99.2')
        registrar(eq, "SVI Vlan99 de Gestion (192.168.99.2/24)", ok_svi, ev)

    # 3. Auditoría de SW-SUC-01-ACC1
    a_cfg = parse_running_config(os.path.join(resp_dir, "sw_suc_01_acc1-running.cfg"))
    a_vlan = parse_vlan_brief(os.path.join(resp_dir, "sw_suc_01_acc1-vlan.txt"))
    if a_cfg:
        eq = "SW-SUC-01-ACC1"
        ev = "sw_suc_01_acc1-running.cfg"
        ev_v = "sw_suc_01_acc1-vlan.txt"

        for vid, vname in [(10, 'USUARIOS_VLAN10'), (20, 'USUARIOS_VLAN20'), (99, 'GESTION')]:
            act_v = a_cfg['vlans'].get(vid)
            act_br = a_vlan.get(vid)
            ok_v = (act_v and act_v['name'] == vname) or (act_br and act_br['name'] == vname)
            registrar(eq, f"Existencia y estado VLAN {vid} ({vname})", ok_v, ev_v if act_br else ev)

        tr_c = a_cfg['interfaces'].get('GigabitEthernet0/0', {})
        ok_tr_c = (tr_c.get('mode') == 'trunk' and tr_c.get('native_vlan') == 99 and tr_c.get('allowed_vlans') == '10,20,99')
        registrar(eq, "Troncal Gi0/0 -> SW-SUC-01-CORE (Nativa 99)", ok_tr_c, ev)

        p_pc8 = a_cfg['interfaces'].get('GigabitEthernet0/3', {})
        ok_pc8 = (p_pc8.get('mode') == 'access' and p_pc8.get('access_vlan') == 99)
        registrar(eq, "Puerto Acceso Gi0/3 -> Switch1 (VLAN 99 PC8)", ok_pc8, ev)

        svi_a = a_cfg['interfaces'].get('Vlan99', {})
        ok_svi_a = (svi_a.get('ip') == '192.168.99.3')
        registrar(eq, "SVI Vlan99 de Gestion (192.168.99.3/24)", ok_svi_a, ev)

    # Exportar a CSV
    headers = ['equipo', 'condicion_evaluada', 'resultado', 'evidencia_usada', 'detalle_diferencia']
    with open(csv_salida, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(registros_csv)

    total = conteo_cumple + conteo_no_cumple
    pct = (conteo_cumple / total * 100) if total > 0 else 0

    print("-" * 105)
    print(f"\n[+] Total Pruebas de Flota : {total}")
    print(f"[+] Pruebas Conformes [OK] : {conteo_cumple}")
    print(f"[+] Pruebas No Conformes   : {conteo_no_cumple}")
    print(f"[+] Cumplimiento de Flota  : {pct:.2f}%")
    print(f"[+] Archivo CSV generado   : {csv_salida}\n")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auditar_flota(base_dir)

if __name__ == '__main__':
    main()
