# Automatización y Auditoría de Red - Sucursal 01

Este repositorio contiene la solución completa de **Infraestructura como Código (IaC)** con Ansible y **Auditoría de Cumplimiento Offline** con Python para la topología de la Sucursal 01.

---

## 1. Función de Ansible y Python dentro de la Solución

### Función de Ansible (Aprovisionamiento, Respaldo e Idempotencia)
* **Aprovisionamiento Declarativo**: Aplica el estado deseado definido en `variables/sucursal_01.yml` y `variables/router_vars.yml` sobre los equipos Cisco IOS (`R-SUC-01`, `SW-SUC-01-CORE` y `SW-SUC-01-ACC1`).
* **Respaldo Automático Preventivo**: Ejecuta y almacena copias de `show running-config` y `show vlan brief` en el directorio `respaldos/` del servidor de automatización.
* **Garantía de Idempotencia**: Comprueba la configuración en ejecución. Si el diseño ya se cumple, una segunda ejecución reporta `changed=0`, garantizando que no se aplican cambios redundantes.

### Función de Python (Auditoría Offline de Cumplimiento)
* **Auditoría Zero-Touch SSH**: Python no interactúa por SSH ni modifica configuraciones en los dispositivos de red.
* **Validación de Cumplimiento**: Lee el estado esperado desde YAML y lo audita contra la evidencia obtenida por Ansible en `respaldos/*.cfg` y `respaldos/*-vlan.txt`.
* **Elementos Auditados**:
  1. Existencia, nombres asignados y estado de las VLAN 10, 20 y 99.
  2. Asignación y descripción de puertos de acceso.
  3. Parámetros troncales: encapsulamiento 802.1Q, VLAN nativa (99), VLANs permitidas (10, 20, 99) y descripciones.
* **Veredicto Explícito**: Indica para cada componente si `[CUMPLE]` o `[NO CUMPLE]` y calcula el porcentaje global de conformidad.

---

## 2. Topología y Dispositivos de la Sucursal 01

| Dispositivo | Rol | IP de Gestión (VLAN 99) | Función |
| :--- | :--- | :--- | :--- |
| **R-SUC-01** | Router Gateway | 192.168.99.1 | Enrutamiento Inter-VLAN (ROAS) |
| **SW-SUC-01-CORE** | Switch Núcleo | 192.168.99.2 | Enlaces troncales y distribución de VLANs |
| **SW-SUC-01-ACC1** | Switch de Acceso | 192.168.99.3 | Conexión de usuarios y enlace a Switch1 |
| **Switch1** | Switch Capa 2 | No administrado | Switch no gestionado (excluido de Ansible) |

---

## 3. Instrucciones de Ejecución

1. **Verificar conectividad SSH:**
   `ansible-playbook playbooks/01_test_connectivity.yml`

2. **Obtener respaldos de configuración y VLANs:**
   `ansible-playbook playbooks/02_respaldo_configuracion.yml`

3. **Configurar switches y router:**
   `ansible-playbook playbooks/site.yml`

4. **Demostración de Idempotencia (Segunda ejecución):**
   `ansible-playbook playbooks/site.yml`
   *(Verificar que reporte `changed=0`)*

5. **Ejecutar auditoría en Python:**
   `python3 auditoria.py`
