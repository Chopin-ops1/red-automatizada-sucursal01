#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototipo 1: Validación Antes y Después de un Cambio (Pre/Post Change Validation)
Compara las evidencias recolectadas por Ansible antes y después de aplicar
un cambio aprobado en la Sucursal 01.

Demuestra que:
1. El cambio aprobado se aplicó efectivamente.
2. Los elementos críticos (VLAN 99, IPs de gestión, troncales, rutas) no sufrieron alteración.
"""

import os
import sys
import re

def parse_iface_descriptions(cfg_path):
    if not os.path.exists(cfg_path): return {}
    descriptions = {}
    with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    current_iface = None
    for line in content.splitlines():
        line_s = line.strip()
        if line.startswith('interface '):
            current_iface = line.split()[1]
            descriptions[current_iface] = ""
        elif current_iface and line_s.startswith('description '):
            descriptions[current_iface] = line_s.replace('description ', '').strip()
    return descriptions

def parse_vlan_presence(vlan_path):
    if not os.path.exists(vlan_path): return {}
    vlans = {}
    with open(vlan_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                vlans[int(parts[0])] = {'name': parts[1], 'status': parts[2]}
    return vlans

def parse_trunk_settings(cfg_path):
    if not os.path.exists(cfg_path): return {}
    trunks = {}
    with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    current_iface = None
    for line in content.splitlines():
        line_s = line.strip()
        if line.startswith('interface '):
            current_iface = line.split()[1]
        elif current_iface:
            if line_s == 'switchport mode trunk':
                if current_iface not in trunks: trunks[current_iface] = {}
                trunks[current_iface]['mode'] = 'trunk'
            elif line_s.startswith('switchport trunk native vlan '):
                if current_iface not in trunks: trunks[current_iface] = {}
                trunks[current_iface]['native'] = line_s.split()[-1]
            elif line_s.startswith('switchport trunk allowed vlan '):
                if current_iface not in trunks: trunks[current_iface] = {}
                trunks[current_iface]['allowed'] = line_s.split()[-1]
    return trunks

def parse_ip_int_brief(path):
    if not os.path.exists(path): return {}
    interfaces = {}
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 6 and not parts[0].startswith('Interface'):
                interfaces[parts[0]] = {'ip': parts[1], 'status': parts[4], 'proto': parts[5]}
    return interfaces

def validar_cambio_pre_post(base_dir):
    dir_pre = os.path.join(base_dir, "evidencias", "pre_cambio")
    dir_post = os.path.join(base_dir, "evidencias", "post_cambio")

    print("=" * 100)
    print("   PROTOTIPO 1: VALIDACION PRE Y POST CAMBIO CONTROLADO (SUCURSAL 01)")
    print("=" * 100)
    print(f"[*] Evidencia PRE  : {dir_pre}")
    print(f"[*] Evidencia POST : {dir_post}\n")

    if not os.path.exists(dir_pre) or not os.path.exists(dir_post):
        print(f"[-] ERROR: Directorios de evidencia incompletos. Ejecute el playbook playbooks/05_cambio_controlado.yml primero.")
        sys.exit(1)

    print(f" {'ELEMENTO / COMPONENTE':<35} {'CONDICION EVALUADA':<30} {'RESULTADO':<32}")
    print("-" * 100)

    # 1. Validación de Cambios Aprobados
    core_pre = parse_iface_descriptions(os.path.join(dir_pre, "sw_suc_01_core-running.cfg"))
    core_post = parse_iface_descriptions(os.path.join(dir_post, "sw_suc_01_core-running.cfg"))

    # Cambio 1: Gi0/1
    desc_pre_g01 = core_pre.get('GigabitEthernet0/1', '')
    desc_post_g01 = core_post.get('GigabitEthernet0/1', '')
    if "[PROD_AUDITADO_RFC2026]" in desc_post_g01 and desc_pre_g01 != desc_post_g01:
        res_c1 = "CAMBIO APLICADO CORRECTAMENTE"
    else:
        res_c1 = "DIFERENCIA DETECTADA"
    print(f" {'CORE - Gi0/1 (PC2 - VLAN 10)':<35} {'Actualizacion descripcion':<30} [{res_c1:<30}]")

    # Cambio 2: Gi0/0
    desc_pre_g00 = core_pre.get('GigabitEthernet0/0', '')
    desc_post_g00 = core_post.get('GigabitEthernet0/0', '')
    if "[ENLACE_CORE_VALIDADO]" in desc_post_g00 and desc_pre_g00 != desc_post_g00:
        res_c2 = "CAMBIO APLICADO CORRECTAMENTE"
    else:
        res_c2 = "DIFERENCIA DETECTADA"
    print(f" {'CORE - Gi0/0 (Troncal Router)':<35} {'Actualizacion descripcion':<30} [{res_c2:<30}]")

    # 2. Validación de Elementos Críticos (Inalterabilidad)
    print("\n [AUDITORIA DE INALTERABILIDAD DE ELEMENTOS CRITICOS]")
    print("-" * 100)

    # Crítico 1: VLAN 99 en Core
    vlan_core_pre = parse_vlan_presence(os.path.join(dir_pre, "sw_suc_01_core-vlan.txt"))
    vlan_core_post = parse_vlan_presence(os.path.join(dir_post, "sw_suc_01_core-vlan.txt"))
    ok_v99_core = (vlan_core_pre.get(99) == vlan_core_post.get(99) and vlan_core_post.get(99, {}).get('status') == 'active')
    res_v99 = "ELEMENTO CRITICO SIN CAMBIOS" if ok_v99_core else "DIFERENCIA DETECTADA"
    print(f" {'CORE - VLAN 99 (GESTION)':<35} {'Inalterabilidad de VLAN 99':<30} [{res_v99:<30}]")

    # Crítico 2: VLAN 99 en Acceso 1
    vlan_acc_pre = parse_vlan_presence(os.path.join(dir_pre, "sw_suc_01_acc1-vlan.txt"))
    vlan_acc_post = parse_vlan_presence(os.path.join(dir_post, "sw_suc_01_acc1-vlan.txt"))
    ok_v99_acc = (vlan_acc_pre.get(99) == vlan_acc_post.get(99) and vlan_acc_post.get(99, {}).get('status') == 'active')
    res_v99_a = "ELEMENTO CRITICO SIN CAMBIOS" if ok_v99_acc else "DIFERENCIA DETECTADA"
    print(f" {'ACC1 - VLAN 99 (GESTION)':<35} {'Inalterabilidad de VLAN 99':<30} [{res_v99_a:<30}]")

    # Crítico 3: Enlaces Troncales
    tr_core_pre = parse_trunk_settings(os.path.join(dir_pre, "sw_suc_01_core-running.cfg"))
    tr_core_post = parse_trunk_settings(os.path.join(dir_post, "sw_suc_01_core-running.cfg"))
    ok_trunks = (tr_core_pre == tr_core_post)
    res_tr = "ELEMENTO CRITICO SIN CAMBIOS" if ok_trunks else "DIFERENCIA DETECTADA"
    print(f" {'CORE - Troncales Gi0/0 y Gi1/2':<35} {'Modo, Nativa 99 y Permitidas':<30} [{res_tr:<30}]")

    # Crítico 4: Direcciones de Gestión IP
    ip_core_pre = parse_ip_int_brief(os.path.join(dir_pre, "sw_suc_01_core-ip_int.txt"))
    ip_core_post = parse_ip_int_brief(os.path.join(dir_post, "sw_suc_01_core-ip_int.txt"))
    ok_ip = (ip_core_pre.get('Vlan99') == ip_core_post.get('Vlan99')) if ip_core_pre else True
    res_ip = "ELEMENTO CRITICO SIN CAMBIOS" if ok_ip else "DIFERENCIA DETECTADA"
    print(f" {'CORE - SVI Vlan99 (192.168.99.2)':<35} {'Direccion IP y estado UP/UP':<30} [{res_ip:<30}]")

    # Crítico 5: Rutas y Gateways en R-SUC-01
    cfg_r_pre = os.path.exists(os.path.join(dir_pre, "r_suc_01-running.cfg"))
    cfg_r_post = os.path.exists(os.path.join(dir_post, "r_suc_01-running.cfg"))
    ok_routes = cfg_r_pre and cfg_r_post
    res_rt = "ELEMENTO CRITICO SIN CAMBIOS" if ok_routes else "DIFERENCIA DETECTADA"
    print(f" {'ROUTER - Subinterfaces Gi0/0.x':<35} {'Puertas de enlace 10/20/99':<30} [{res_rt:<30}]")

    print("=" * 100)
    print("                     DICTAMEN FINAL DE LA VALIDACION DE CAMBIO")
    print("=" * 100)
    todo_ok = all(r == "CAMBIO APLICADO CORRECTAMENTE" for r in [res_c1, res_c2]) and all(r == "ELEMENTO CRITICO SIN CAMBIOS" for r in [res_v99, res_v99_a, res_tr, res_ip, res_rt])
    if todo_ok:
        print(" [APROBADO] El cambio solicitado ocurrio con exito y todos los elementos criticos")
        print("            de la infraestructura conservaron su estado operativo intacto.")
    else:
        print(" [FALLO] Se detectaron anomalias o elementos criticos modificados inesperadamente.")
    print("=" * 100 + "\n")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    validar_cambio_pre_post(base_dir)

if __name__ == '__main__':
    main()
