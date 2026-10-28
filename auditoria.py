#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, sys, yaml

def parse_running_config(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    data = {'vlans': {}, 'interfaces': {}}
    for m in re.finditer(r'^vlan\s+(\d+)\s*\n(?:\s+name\s+([^\n]+))?', content, re.MULTILINE):
        data['vlans'][int(m.group(1))] = {'name': m.group(2).strip() if m.group(2) else "", 'status': 'active'}
    current_iface = None
    for line in content.splitlines():
        line_clean = line.strip()
        if line.startswith('interface '):
            current_iface = line.split()[1]
            data['interfaces'][current_iface] = {
                'description': '', 'mode': 'routed', 'access_vlan': 1, 'native_vlan': 1, 'allowed_vlans': ''
            }
        elif current_iface and line.startswith(' '):
            if line_clean.startswith('description '):
                data['interfaces'][current_iface]['description'] = line_clean.replace('description ', '').strip()
            elif line_clean == 'switchport mode access':
                data['interfaces'][current_iface]['mode'] = 'access'
            elif line_clean == 'switchport mode trunk':
                data['interfaces'][current_iface]['mode'] = 'trunk'
            elif line_clean.startswith('switchport access vlan '):
                data['interfaces'][current_iface]['access_vlan'] = int(line_clean.split()[-1])
            elif line_clean.startswith('switchport trunk native vlan '):
                data['interfaces'][current_iface]['native_vlan'] = int(line_clean.split()[-1])
            elif line_clean.startswith('switchport trunk allowed vlan '):
                data['interfaces'][current_iface]['allowed_vlans'] = line_clean.split()[-1]
    return data

def parse_vlan_brief(vlan_txt_path):
    if not os.path.exists(vlan_txt_path): return {}
    vlan_status = {}
    with open(vlan_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                vlan_status[int(parts[0])] = {'name': parts[1], 'status': parts[2]}
    return vlan_status

def audit_switch(switch_name, expected_vlans, expected_conf, respaldos_dir):
    cfg_file = os.path.join(respaldos_dir, f"{switch_name}-running.cfg")
    vlan_file = os.path.join(respaldos_dir, f"{switch_name}-vlan.txt")
    if not os.path.exists(cfg_file):
        print(f"[-] ERROR: No se encontró el respaldo: {cfg_file}")
        return [], 0, 1

    parsed = parse_running_config(cfg_file)
    vlan_brief = parse_vlan_brief(vlan_file)
    cumple_count, no_cumple_count = 0, 0

    print(f"\n{'='*80}\n DISPOSITIVO: {switch_name.upper()} ({os.path.basename(cfg_file)})\n{'='*80}")
    print("\n [1] AUDITORIA DE BASE DE DATOS DE VLANS (10, 20, 99)")
    print(f" {'ID':<6} {'VLAN ESPERADA':<20} {'ESTADO':<12} {'RESULTADO':<12} {'DETALLES'}")
    print(f" {'-'*5} {'-'*18} {'-'*10} {'-'*10} {'-'*26}")
    for vlan in expected_vlans:
        vid, vname = vlan['id'], vlan['nombre']
        act_vlan = parsed['vlans'].get(vid)
        brief = vlan_brief.get(vid)
        actual_name = act_vlan['name'] if act_vlan else (brief['name'] if brief else "")
        status = brief.get('status', 'active') if brief else 'active'
        if actual_name == vname:
            print(f" {vid:<6} {vname:<20} {status:<12} {'[CUMPLE]':<12} Nombre: {actual_name} | Estado: {status}")
            cumple_count += 1
        else:
            print(f" {vid:<6} {vname:<20} {status:<12} {'[NO CUMPLE]':<12} Esperado '{vname}', Encontrado '{actual_name}'")
            no_cumple_count += 1

    print("\n [2] AUDITORIA DE ENLACES TRONCALES")
    print(f" {'INTERFAZ':<22} {'MODO':<10} {'NATIVA':<10} {'PERMITIDAS':<12} {'RESULTADO':<12}")
    print(f" {'-'*20} {'-'*8} {'-'*8} {'-'*10} {'-'*10}")
    for tr in expected_conf.get('troncales', []):
        iface = tr['interfaz']
        act_if = parsed['interfaces'].get(iface, {})
        ok = (act_if.get('mode') == 'trunk' and 
              act_if.get('native_vlan') == tr['vlan_nativa'] and 
              act_if.get('allowed_vlans') == tr['vlans_permitidas'])
        res = "[CUMPLE]" if ok else "[NO CUMPLE]"
        if ok: cumple_count += 1
        else: no_cumple_count += 1
        print(f" {iface:<22} {'trunk':<10} {str(tr['vlan_nativa']):<10} {tr['vlans_permitidas']:<12} {res:<12}")

    print("\n [3] AUDITORIA DE PUERTOS DE ACCESO")
    print(f" {'INTERFAZ':<22} {'VLAN ESP':<10} {'MODO':<10} {'RESULTADO':<12} {'DESCRIPCION'}")
    print(f" {'-'*20} {'-'*8} {'-'*8} {'-'*10} {'-'*25}")
    for acc in expected_conf.get('puertos_acceso', []):
        iface = acc['interfaz']
        act_if = parsed['interfaces'].get(iface, {})
        ok = (act_if.get('mode') == 'access' and act_if.get('access_vlan') == acc['vlan'])
        res = "[CUMPLE]" if ok else "[NO CUMPLE]"
        if ok: cumple_count += 1
        else: no_cumple_count += 1
        desc = act_if.get('description', '')
        print(f" {iface:<22} {str(acc['vlan']):<10} {'access':<10} {res:<12} '{desc}'")

    return cumple_count, no_cumple_count

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    vars_file = os.path.join(base, "variables", "sucursal_01.yml")
    resp_dir = os.path.join(base, "respaldos")
    print("\n" + "="*80 + "\n   AUDITORIA AUTOMATIZADA DE CUMPLIMIENTO DE RED - SUCURSAL 01\n" + "="*80)
    with open(vars_file, 'r') as f: design = yaml.safe_load(f)
    vlans = design.get('vlans', [])
    c_tot, nc_tot = 0, 0
    for sw, conf in design.get('switches_config', {}).items():
        c, nc = audit_switch(sw, vlans, conf, resp_dir)
        c_tot += c
        nc_tot += nc
    total = c_tot + nc_tot
    pct = (c_tot / total * 100) if total > 0 else 0
    print(f"\n{'='*80}\n                RESUMEN EJECUTIVO DE AUDITORIA\n{'='*80}")
    print(f" Total Evaluados       : {total}\n Cumplen [OK]          : {c_tot}\n No Cumplen [FALLO]    : {nc_tot}\n Porcentaje Cumplimiento: {pct:.2f}%\n Dictamen Final        : {'APROBADO (100% CONFORME)' if pct == 100 else 'NO CONFORME'}\n{'='*80}\n")

if __name__ == '__main__':
    main()
