# Automatización, Auditoría y Telemetría de Red (NetDevOps)

**Proyecto:** Automatización de Infraestructura de Red y Prototipos de Operación NetDevOps  
**Topología:** Sucursal 01 (Operativa en GNS3) y Sucursal 02 (Diseño y Aprovisionamiento Dinámico)  
**Estudiante:** Daniel Barraza  
**Docente:** Miler Baldovino  
**Asignatura:** Gestión de Infraestructura de Red  
**Programa:** Ingeniería Informática — Corporación Universitaria Reformada  

---

## 1. Versiones del Repositorio (Trazabilidad y Entregas)

El repositorio almacena el ciclo de vida completo de automatización de la infraestructura, estructurado formalmente en ramas y etiquetas de Git para facilitar la revisión de cada entrega:

* **Versión Actual (`master` / Tag `v2.0-actividad2`):**
  Solución integral consolidada. Incluye la infraestructura automatizada de la Sucursal 01 y los **cinco prototipos de Python** para validación de cambios controlados, cálculo dinámico de diseño VLSM para la Sucursal 02, auditoría masiva de flota, conciliación trifuente (IPAM/YAML/Ansible) y telemetría activa ICMP.
* **Versión Anterior (Rama `actividad-1-sucursal-01` / Tag `v1.0-actividad1`):**
  Instantánea histórica de la **Actividad 1**. Contiene los playbooks de Ansible para aprovisionamiento declarativo, respaldos automáticos, comprobación de idempotencia y el script inicial de auditoría de cumplimiento en Python (`auditoria.py`).

Para consultar o clonar una versión específica desde la terminal:
```bash
# Cambiar a la versión de la Actividad 1 (Sucursal 01 básica)
git checkout actividad-1-sucursal-01

# Regresar a la versión consolidada de la Actividad 2 (Prototipos Python + Sucursal 02)
git checkout master
```

---

## 2. Arquitectura de Solución y División de Responsabilidades

| Componente | Motor Tecnológico | Responsabilidad Operativa |
| :--- | :--- | :--- |
| **Aprovisionamiento y Estado Deseado** | **Ansible** | Aplica configuraciones declarativas sobre routers y switches (`cisco.ios`), garantizando idempotencia y cero intervención CLI interactiva. |
| **Orquestación de Cambios y Evidencias** | **Ansible** | Gestiona el flujo de cambio en 3 fases (`05_cambio_controlado.yml`) y recolecta evidencias basales en `evidencias/` y `respaldos/`. |
| **Lógica Algorítmica y Particionamiento** | **Python 3** | Ejecuta el cálculo matemático de subredes VLSM sin solapamiento para la Sucursal 02 (`python/generar_sucursal_02.py`). |
| **Guardarraíles y Validación Pre/Post** | **Python 3** | Analiza mediante expresiones regulares las diferencias entre estados y asegura la inalterabilidad de elementos críticos (`python/validar_cambio.py`). |
| **Auditoría Offline de Flota** | **Python 3** | Evalúa 16 reglas de diseño (Golden Config) sobre los respaldos descargados sin consumir CPU de los equipos en producción (`python/auditar_flota.py`). |
| **Conciliación Trifuente de Inventario** | **Python 3** | Detecta derivas (*drift*) entre IPAM JSON, variables YAML y el estado real (`python/validar_inventario.py`). |
| **Telemetría Activa y SLAs** | **Python 3** | Realiza sondeos ICMP, calcula métricas de latencia/pérdida y clasifica el cumplimiento de SLA (`python/medir_conectividad.py`). |

---

## 3. Estructura Completa del Repositorio

```
.
├── README.md                                 # Documentación maestra del repositorio
├── ansible.cfg                               # Configuración de timeouts y conexión de Ansible
├── inventario/
│   └── hosts.yml                             # Inventario de dispositivos gestionados
├── variables/
│   ├── sucursal_01.yml                       # Variables de configuración de conmutadores (Sucursal 01)
│   ├── router_vars.yml                       # Variables de enrutamiento y subinterfaces ROAS
│   └── sucursal_02_generada.yml              # Variables generadas por Python para la Sucursal 02
├── datos/
│   ├── sucursal_02_entrada.yml               # Requerimientos de negocio para nueva sede (50, 25, 10 hosts)
│   └── ipam_sucursal_01.json                 # Simulación de inventario / API IPAM empresarial
├── playbooks/
│   ├── 01_test_connectivity.yml             # Verificación de conectividad SSH
│   ├── 02_respaldo_configuracion.yml         # Extracción de respaldos de configuración
│   ├── 03_configurar_switches.yml            # Configuración de VLANs y puertos en switches
│   ├── 04_configurar_router.yml              # Configuración de subinterfaces ROAS en router
│   ├── 05_cambio_controlado.yml              # Flujo de cambio controlado en 3 fases (Pre, Cambio, Post)
│   └── site.yml                              # Playbook maestro de aprovisionamiento
├── python/
│   ├── validar_cambio.py                     # Prototipo 1: Validación pre/post cambio e inalterabilidad
│   ├── generar_sucursal_02.py                # Prototipo 2: Cálculo matemático y generador VLSM
│   ├── auditar_flota.py                      # Prototipo 3: Auditoría offline de 16 reglas sobre la flota
│   ├── validar_inventario.py                 # Prototipo 4: Conciliación IPAM vs YAML vs Ansible
│   └── medir_conectividad.py                 # Prototipo 5: Telemetría ICMP y cumplimiento de SLAs
├── evidencias/
│   ├── auditoria_flota.csv                   # Resultados de auditoría de flota (100% cumplimiento)
│   ├── mediciones_conectividad.csv           # Telemetría de latencias y pérdidas de paquetes
│   ├── pre_cambio/                           # Respaldos basales previos al cambio controlado
│   └── post_cambio/                          # Respaldos posteriores a la aplicación del cambio
├── respaldos/                                # Copias de seguridad de configuración en ejecución
│   ├── r_suc_01-running.cfg
│   ├── sw_suc_01_core-running.cfg
│   ├── sw_suc_01_acc1-running.cfg
│   ├── sw_suc_01_core-vlan.txt
│   └── sw_suc_01_acc1-vlan.txt
├── documentacion/
│   ├── README.md                             # Especificación técnica de los cinco prototipos
│   └── topologia_y_diseño.md                 # Parámetros y diagrama de la topología GNS3
└── auditoria.py                              # Script inicial de auditoría de la Actividad 1
```

---

## 4. Guía Rápida de Ejecución

### Fase 1: Automatización de Infraestructura con Ansible
```bash
# 1. Comprobar conectividad SSH
ansible-playbook playbooks/01_test_connectivity.yml

# 2. Respaldar configuración basal
ansible-playbook playbooks/02_respaldo_configuracion.yml

# 3. Aprovisionar switches y router
ansible-playbook playbooks/site.yml

# 4. Verificar idempotencia (segunda ejecución debe reportar changed=0)
ansible-playbook playbooks/site.yml
```

### Fase 2: Ejecución de Prototipos de Python NetDevOps
```bash
# Prototipo 1: Ejecutar cambio controlado en Ansible y validar inalterabilidad con Python
ansible-playbook playbooks/05_cambio_controlado.yml
python3 python/validar_cambio.py

# Prototipo 2: Calcular diseño VLSM de la Sucursal 02 y exportar variables YAML
python3 python/generar_sucursal_02.py

# Prototipo 3: Auditar las 16 reglas de configuración en la flota de red
python3 python/auditar_flota.py

# Prototipo 4: Reconciliar inventario IPAM vs Diseño YAML vs Red Real
python3 python/validar_inventario.py

# Prototipo 5: Telemetría de red activa hacia direcciones de gestión
python3 python/medir_conectividad.py
```
