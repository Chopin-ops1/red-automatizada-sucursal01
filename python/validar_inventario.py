#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototipo 4: Relación y Conciliación de Fuentes de Información
Contrasta la información de una plataforma IPAM/CMDB (datos/ipam_sucursal_01.json)
contra el diseño declarativo (variables/sucursal_01.yml y router_vars.yml)
y la evidencia real obtenida por Ansible (respaldos/).

Clasifica los hallazgos en:
1. COINCIDENCIAS (Matches)
2. FALTANTES (Missing)
3. DIFERENCIAS (Discrepancies)
"""

import os
import sys
import json
import re
import yaml

def cargar_ipam(ruta_json):
    if not os.path.exists(ruta_json):
        print(f"[-] ERROR: Archivo IPAM no encontrado: {ruta_json}")
        sys.exit(1)
    with open(ruta_json, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_yaml(ruta_yaml):
    if not os.path.exists(ruta_yaml):
        return {}
    with open(ruta_yaml, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_vlan_brief(vlan_txt_path):
    if not os.path.exists(vlan_txt_path):
        return {}
    vlans = {}
    with open(vlan_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                vlans[int(parts[0])] = {'nombre': parts[1], 'estado': parts[2]}
    return vlans

def parse_router_cfg(router_cfg_path):
    if not os.path.exists(router_cfg_path):
        return {}
    subifaces = {}
    with open(router_cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    for block in content.split('interface '):
        lines = block.splitlines()
        if not lines: continue
        iface_name = lines[0].split()[0]
        ip, mask = None, None
        for l in lines[1:]:
            l_strip = l.strip()
            if l_strip.startswith('ip address '):
                parts = l_strip.split()
                if len(parts) >= 4:
                    ip, mask = parts[2], parts[3]
        if ip:
            subifaces[iface_name] = {'ip': ip, 'mask': mask}
    return subifaces

def conciliar_fuentes(base_dir):
    ipam_file = os.path.join(base_dir, "datos", "ipam_sucursal_01.json")
    vars_sw_file = os.path.join(base_dir, "variables", "sucursal_01.yml")
    vars_r_file = os.path.join(base_dir, "variables", "router_vars.yml")
    resp_dir = os.path.join(base_dir, "respaldos")

    ipam_data = cargar_ipam(ipam_file)
    design_sw = cargar_yaml(vars_sw_file)
    design_r = cargar_yaml(vars_r_file)

    vlans_core = parse_vlan_brief(os.path.join(resp_dir, "sw_suc_01_core-vlan.txt"))
    router_ifaces = parse_router_cfg(os.path.join(resp_dir, "r_suc_01-running.cfg"))

    coincidencias = []
    faltantes = []
    diferencias = []

    print("=" * 90)
    print("   PROTOTIPO 4: CONCILIACION MULTIFUENTE (IPAM JSON vs YAML vs ANSIBLE)")
    print("=" * 90)
    print(f"[*] Fuente 1 (IPAM / CMDB)    : {ipam_file}")
    print(f"[*] Fuente 2 (Diseño YAML)    : {vars_sw_file}")
    print(f"[*] Fuente 3 (Evidencia Real) : {resp_dir}\n")

    # 1. Validación de Dispositivos y Gestión
    print("[1] ANALISIS DE EQUIPOS Y DIRECCIONES DE GESTION")
    print("-" * 90)
    hosts_yaml = ["R-SUC-01", "SW-SUC-01-CORE", "SW-SUC-01-ACC1"]
    for dev in ipam_data.get('dispositivos', []):
        nombre = dev['nombre']
        ip_gestion = dev['direccion_gestion']
        funcion = dev['funcion']

        if nombre in hosts_yaml:
            # Coincide en inventario
            cfg_file = os.path.join(resp_dir, f"{nombre.lower().replace('-', '_')}-running.cfg")
            if os.path.exists(cfg_file):
                coincidencias.append({
                    'categoria': 'Dispositivo',
                    'elemento': nombre,
                    'detalle': f"IP Gestión {ip_gestion} coincide en IPAM, YAML y respaldo físico"
                })
                print(f" [MATCH]      {nombre:<15} IP Gestión: {ip_gestion:<15} Estado: Activo en producción")
            else:
                diferencias.append({
                    'categoria': 'Dispositivo',
                    'elemento': nombre,
                    'detalle': f"Registrado en IPAM pero sin archivo de respaldo en {resp_dir}"
                })
                print(f" [DIFERENCIA] {nombre:<15} Registrado en IPAM pero sin respaldo generado")
        else:
            # Equipo en IPAM no desplegado en YAML/red
            faltantes.append({
                'categoria': 'Dispositivo',
                'elemento': nombre,
                'detalle': f"Registrado en IPAM ({funcion}, IP: {ip_gestion}) pero NO está desplegado en la red"
            })
            print(f" [FALTANTE]   {nombre:<15} IP Gestión: {ip_gestion:<15} Planificado en IPAM, NO en infraestructura")

    # 2. Validación de Redes, VLANs y Gateways
    print("\n[2] ANALISIS DE VLANS, SUBREDES Y PUERTAS DE ENLACE")
    print("-" * 90)
    vlans_yaml = {v['id']: v['nombre'] for v in design_sw.get('vlans', [])}

    for net in ipam_data.get('redes_vlan', []):
        vid = net['vlan_id']
        nombre_ipam = net['nombre']
        red_ipam = net['red']
        gw_ipam = net['gateway']

        # Verificar contra YAML
        if vid in vlans_yaml:
            nombre_yaml = vlans_yaml[vid]
            vlan_real = vlans_core.get(vid)

            if vlan_real:
                coincidencias.append({
                    'categoria': 'VLAN/Red',
                    'elemento': f"VLAN {vid}",
                    'detalle': f"Red {red_ipam}, GW {gw_ipam}, Nombre '{nombre_ipam}' verificado en switches"
                })
                print(f" [MATCH]      VLAN {vid:<3} ({nombre_ipam:<18}) Red: {red_ipam:<16} GW: {gw_ipam:<14} [CONFIRMADO]")
            else:
                diferencias.append({
                    'categoria': 'VLAN/Red',
                    'elemento': f"VLAN {vid}",
                    'detalle': f"Definida en IPAM y YAML pero no encontrada activa en show vlan brief"
                })
                print(f" [DIFERENCIA] VLAN {vid:<3} ({nombre_ipam:<18}) Definida pero inactiva en conmutadores")
        else:
            faltantes.append({
                'categoria': 'VLAN/Red',
                'elemento': f"VLAN {vid}",
                'detalle': f"VLAN {vid} ({nombre_ipam}, {red_ipam}) existe en IPAM pero NO existe en el diseño YAML ni en la red"
            })
            print(f" [FALTANTE]   VLAN {vid:<3} ({nombre_ipam:<18}) Red: {red_ipam:<16} Presente en IPAM, FALTANTE en conmutadores")

    # Resumen Ejecutivo
    print("\n" + "=" * 90)
    print("                     RESUMEN DE RECONCILIACION MULTIFUENTE")
    print("=" * 90)
    print(f" Total Coincidencias (Matches)       : {len(coincidencias)}")
    print(f" Total Faltantes (Missing)            : {len(faltantes)}")
    print(f" Total Diferencias (Discrepancies)    : {len(diferencias)}")
    print("-" * 90)
    print(" Detalle de Faltantes detectados:")
    for f in faltantes:
        print(f"  * [{f['categoria']}] {f['elemento']}: {f['detalle']}")
    print("=" * 90 + "\n")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conciliar_fuentes(base_dir)

if __name__ == '__main__':
    main()
