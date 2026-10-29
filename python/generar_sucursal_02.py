#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototipo 2: Generación de datos de diseño para una nueva sede (Sucursal 02)
Calcula subredes VLSM sin solapamiento a partir de datos/sucursal_02_entrada.yml
y genera variables/sucursal_02_generada.yml para su uso con Ansible.
"""

import os
import sys
import math
import ipaddress
import yaml

def calcular_prefijo_requerido(hosts_requeridos):
    # Total de IPs requeridas: hosts + 1 gateway + 1 red + 1 broadcast
    total_ips_necesarias = hosts_requeridos + 3
    bits_host = math.ceil(math.log2(total_ips_necesarias))
    prefijo = 32 - bits_host
    return prefijo, (2 ** bits_host) - 2

def generar_diseno_sucursal_02(archivo_entrada, archivo_salida):
    if not os.path.exists(archivo_entrada):
        print(f"[-] ERROR: No se encontró el archivo de entrada: {archivo_entrada}")
        sys.exit(1)

    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        datos = yaml.safe_load(f)

    sede = datos.get('sede', 'Sucursal 02')
    bloque_str = datos.get('bloque_disponible', '10.20.0.0/23')
    red_base = ipaddress.ip_network(bloque_str)

    print("=" * 85)
    print(f"   PROTOTIPO 2: GENERADOR DE DATOS DE DISENO VLSM - {sede.upper()}")
    print("=" * 85)
    print(f"[*] Bloque de red disponible : {red_base} ({red_base.num_addresses} IPs totales)")
    print(f"[*] Archivo de requerimientos: {archivo_entrada}\n")

    # Ordenar requerimientos de mayor a menor número de hosts (regla de oro VLSM)
    requerimientos = datos.get('requerimientos_usuarios', [])
    requerimientos_ordenados = sorted(
        requerimientos, 
        key=lambda x: x['dispositivos_requeridos'], 
        reverse=True
    )

    ip_actual = int(red_base.network_address)
    subredes_generadas = []

    for req in requerimientos_ordenados:
        vlan_id = req['vlan_id']
        nombre = req['nombre']
        hosts_pedidos = req['dispositivos_requeridos']
        prefijo, hosts_usables = calcular_prefijo_requerido(hosts_pedidos)

        tamano_subred = 2 ** (32 - prefijo)
        
        # Alinear a la frontera de subred requerida
        if ip_actual % tamano_subred != 0:
            ip_actual = ((ip_actual // tamano_subred) + 1) * tamano_subred

        subred = ipaddress.ip_network((ip_actual, prefijo))
        gateway = subred.network_address + 1
        primer_host = subred.network_address + 2
        ultimo_host = subred.broadcast_address - 1

        info_subred = {
            'vlan_id': vlan_id,
            'nombre': nombre,
            'tipo': req.get('tipo', ''),
            'red': str(subred.network_address),
            'prefijo': prefijo,
            'mascara': str(subred.netmask),
            'gateway': str(gateway),
            'rango_inicio': str(primer_host),
            'rango_fin': str(ultimo_host),
            'hosts_solicitados': hosts_pedidos,
            'hosts_previstos': hosts_usables,
            'broadcast': str(subred.broadcast_address)
        }
        subredes_generadas.append(info_subred)
        ip_actual += tamano_subred

    # Ordenar por VLAN ID para el archivo final de variables
    subredes_por_vlan = sorted(subredes_generadas, key=lambda x: x['vlan_id'])

    # Presentación en pantalla
    print(f"{'VLAN':<6} {'NOMBRE':<16} {'SUBRED':<18} {'MASCARA':<16} {'GATEWAY':<15} {'HOSTS':<10}")
    print("-" * 85)
    for s in subredes_por_vlan:
        subred_cidr = f"{s['red']}/{s['prefijo']}"
        hosts_str = f"{s['hosts_solicitados']} -> {s['hosts_previstos']}"
        print(f"{s['vlan_id']:<6} {s['nombre']:<16} {subred_cidr:<18} {s['mascara']:<16} {s['gateway']:<15} {hosts_str:<10}")
    print("-" * 85)

    ip_restante = ipaddress.ip_address(ip_actual)
    ips_utilizadas = ip_actual - int(red_base.network_address)
    ips_libres = red_base.num_addresses - ips_utilizadas
    print(f"[+] Total IPs asignadas   : {ips_utilizadas} direcciones")
    print(f"[+] Bloque restante libre : {ip_restante} - {red_base.broadcast_address} ({ips_libres} direcciones disponibles)")

    # Estructura del YAML para Ansible
    yaml_output = {
        'sucursal_02_config': {
            'sede': sede,
            'bloque_origen': bloque_str,
            'vlans': [
                {
                    'id': s['vlan_id'],
                    'nombre': s['nombre'],
                    'red': s['red'],
                    'prefijo': s['prefijo'],
                    'mascara': s['mascara'],
                    'gateway': s['gateway'],
                    'rango_hosts': f"{s['rango_inicio']} - {s['rango_fin']}",
                    'capacidad_hosts': s['hosts_previstos']
                } for s in subredes_por_vlan
            ],
            'resumen_asignacion': {
                'ips_utilizadas': ips_utilizadas,
                'ips_disponibles': ips_libres
            }
        }
    }

    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n[OK] Variables exportadas con exito para Ansible en: {archivo_salida}\n")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    entrada = os.path.join(base_dir, "datos", "sucursal_02_entrada.yml")
    salida = os.path.join(base_dir, "variables", "sucursal_02_generada.yml")
    generar_diseno_sucursal_02(entrada, salida)

if __name__ == '__main__':
    main()
