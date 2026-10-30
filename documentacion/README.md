# Documentación Técnica de Prototipos de Python Aplicados a Redes (NetDevOps)

**Asignatura:** Gestión de Infraestructura de Red  
**Programa:** Ingeniería Informática — Corporación Universitaria Reformada  
**Estudiante:** Daniel Barraza  
**Docente:** Miler Baldovino  

---

## 1. Visión General de la Actividad 2

Esta fase extiende la infraestructura de la **Sucursal 01** previamente automatizada con Ansible, incorporando cinco prototipos en **Python 3** que representan casos de uso fundamentales en la ingeniería y operación de redes (NetDevOps):

1. **Validación antes y después de un cambio controlado (Guardrails).**
2. **Generación automatizada de datos de diseño VLSM para nueva sede (Sucursal 02).**
3. **Auditoría continua de flota pequeña mediante análisis de configuración offline.**
4. **Relación y conciliación multifuente (IPAM JSON vs. Diseño YAML vs. Estado Real Ansible).**
5. **Medición de conectividad activa y telemetría de calidad en la red de gestión (ICMP).**

---

## 2. Detalle de los Cinco Prototipos Implementados

### Prototipo 1: Validación Antes y Después de un Cambio Controlado (`python/validar_cambio.py`)
* **Propósito:** Validar mediante análisis de diferencias que un cambio aprobado en la red se aplicó con éxito y garantizar que los elementos críticos de la infraestructura no sufrieron alteraciones no planificadas.
* **Entradas:** 
  * Evidencia basal en `evidencias/pre_cambio/` (`sw_suc_01_core-running.cfg`, `sw_suc_01_core-vlan.txt`, `sw_suc_01_core-ip_int.txt`, `r_suc_01-running.cfg`, etc.).
  * Evidencia posterior en `evidencias/post_cambio/`.
* **Playbook de Soporte:** `playbooks/05_cambio_controlado.yml` (Fase 1: Pre-evidencia, Fase 2: Actualización de descripciones en Gi0/1 y Gi0/0 de `SW-SUC-01-CORE`, Fase 3: Post-evidencia).
* **Condiciones Evaluadas:**
  * Actualización de descripción en `Gi0/1` (PC2 - VLAN 10): `[CAMBIO APLICADO CORRECTAMENTE]`
  * Actualización de descripción en `Gi0/0` (Troncal Router): `[CAMBIO APLICADO CORRECTAMENTE]`
  * Inalterabilidad de VLAN 99 en Core y Acceso: `[ELEMENTO CRITICO SIN CAMBIOS]`
  * Inalterabilidad de enlaces troncales Gi0/0 y Gi1/2 (Modo, Nativa 99, permitidas 10,20,99): `[ELEMENTO CRITICO SIN CAMBIOS]`
  * Inalterabilidad de SVI Vlan99 (192.168.99.2) y subinterfaces del Router: `[ELEMENTO CRITICO SIN CAMBIOS]`
* **Salida y Dictamen:** Veredicto final `[APROBADO]`.

### Prototipo 2: Generador de Datos de Diseño VLSM - Sucursal 02 (`python/generar_sucursal_02.py`)
* **Propósito:** Calcular dinámicamente el plan de direccionamiento IP sin solapamiento (VLSM) para la expansión de una nueva sede a partir de requerimientos en YAML, exportando variables listas para aprovisionamiento con Ansible.
* **Entradas:** `datos/sucursal_02_entrada.yml` (Bloque disponible `10.20.0.0/23`, 50 dispositivos Admin, 25 Operación, 10 Gestión).
* **Salida Generada:** `variables/sucursal_02_generada.yml` y resumen visual en terminal.
* **Plan de Direccionamiento Calculado:**
  * **VLAN 10 ADMINISTRACION:** Subred `10.20.0.0/26` (Máscara `255.255.255.192`), Gateway `10.20.0.1`, Rango `10.20.0.2 - 10.20.0.62` (50 pedidos -> 62 usables).
  * **VLAN 20 OPERACION:** Subred `10.20.0.64/27` (Máscara `255.255.255.224`), Gateway `10.20.0.65`, Rango `10.20.0.66 - 10.20.0.94` (25 pedidos -> 30 usables).
  * **VLAN 99 GESTION:** Subred `10.20.0.96/28` (Máscara `255.255.255.240`), Gateway `10.20.0.97`, Rango `10.20.0.98 - 10.20.0.110` (10 pedidos -> 14 usables).
  * **Remanente Libre:** Bloque continuo `10.20.0.112 - 10.20.1.255` (400 direcciones IP libres para crecimiento).

### Prototipo 3: Auditoría Automatizada de Flota Pequeña (`python/auditar_flota.py`)
* **Propósito:** Inspeccionar de forma masiva y offline la configuración de los equipos de red (`R-SUC-01`, `SW-SUC-01-CORE` y `SW-SUC-01-ACC1`) contra el estándar de diseño (Golden Configuration) sin conectarse por SSH a los equipos en producción.
* **Entradas:** Archivos de respaldo recolectados por Ansible en `respaldos/` (`running-config` y `vlan.txt`).
* **Alcance:** 16 pruebas técnicas (enrutamiento ROAS, subinterfaces de gateway, existencia y estado activo de VLANs 10, 20 y 99, configuración de troncales 802.1Q con nativa 99, y direcciones IP de las SVIs).
* **Salida Generada:** Reporte en pantalla y exportación normalizada a `evidencias/auditoria_flota.csv` (100.00% de cumplimiento, 16/16 pruebas conformes).

### Prototipo 4: Relación y Conciliación Multifuente (`python/validar_inventario.py`)
* **Propósito:** Correlacionar la fuente de verdad declarativa (IPAM/CMDB), el modelo de infraestructura como código (YAML) y la evidencia operativa real (Ansible) para detectar desviaciones (*Configuration Drift*).
* **Entradas:**
  * `datos/ipam_sucursal_01.json` (simulación de respuesta API de IPAM con discrepancias planificadas: switch de acceso proyectado `SW-SUC-01-ACC2` y `VLAN 30 INVITADOS`).
  * `variables/sucursal_01.yml` y `variables/router_vars.yml` (diseño de red).
  * `respaldos/` (evidencias reales obtenidas por Ansible).
* **Clasificación Obtenida:**
  * **Coincidencias (6 Matches):** Dispositivos y VLANs activas consistentes en las tres fuentes.
  * **Faltantes (2 Missing):** `SW-SUC-01-ACC2` (IP `192.168.99.4`) y `VLAN 30 INVITADOS` (`192.168.30.0/24`) presentes en IPAM pero ausentes en la red física.
  * **Diferencias (0 Discrepancies):** Cero contradicciones en direccionamiento o nombres de elementos desplegados.

### Prototipo 5: Medición de Conectividad y Telemetría de Red (`python/medir_conectividad.py`)
* **Propósito:** Medición activa y telemetría continua de calidad de enlace sobre el plano de gestión (VLAN 99) originada desde el servidor de automatización (Ubuntu).
* **Entradas:** Lista de IPs de gestión: `192.168.99.1` (Router), `192.168.99.2` (Switch Core) y `192.168.99.3` (Switch Acceso 1).
* **Criterio de SLA:** CUMPLE cuando Pérdida = 0% y Latencia Promedio <= 50 ms; de lo contrario, NO CUMPLE.
* **Salida Generada:** Exportación hacia `evidencias/mediciones_conectividad.csv`.
* **Resultados Obtenidos:**
  * `R-SUC-01`: 0% pérdida, Latencia Avg = 7.40 ms `[CUMPLE]`
  * `SW-SUC-01-CORE`: 0% pérdida, Latencia Avg = 106.95 ms `[NO CUMPLE]` (Latencia elevada por procesamiento de CPU en interfaz virtual SVI de conmutador virtualizado).
  * `SW-SUC-01-ACC1`: 0% pérdida, Latencia Avg = 320.98 ms `[NO CUMPLE]`

---

## 3. Matriz de Complementariedad Ansible vs. Python

| Prototipo | Rol de Ansible | Rol de Python | Valor Técnico Aportado |
| :--- | :--- | :--- | :--- |
| **Prototipo 1** | Orquesta las 3 fases del cambio y extrae pre/post evidencias sin tocar la lógica. | Realiza el análisis diferencial sintáctico (regex) y emite veredicto `[APROBADO]`. | Garantiza guardarraíles de seguridad operativa ante modificaciones en producción. |
| **Prototipo 2** | Consume las variables generadas para desplegar la configuración en switches y routers. | Ejecuta el algoritmo VLSM, calcula máscaras, valida solapamiento y genera el YAML. | Automatiza el dimensionamiento IP libre de errores humanos para Zero-Touch Provisioning. |
| **Prototipo 3** | Recolecta masivamente respaldos de configuración y comandos show sin intervención interactiva. | Audita 16 condiciones de red de forma offline y exporta el archivo CSV normalizado. | Auditoría continua con cero sobrecarga de CPU sobre el plano de control en producción. |
| **Prototipo 4** | Proporciona la evidencia operativa real desde los conmutadores y enrutadores físicos. | Cruza 3 fuentes heterogéneas (JSON, YAML, .cfg) y clasifica Matches, Faltantes y Drift. | Sincronización entre la CMDB/IPAM y el estado real de la infraestructura. |
| **Prototipo 5** | Utiliza el plano de gestión validado para la ejecución confiable de playbooks. | Ejecuta ráfagas ICMP activas, calcula métricas estadísticas y evalúa SLAs de red. | Telemetría proactiva y detección temprana de cuellos de botella en la gestión. |

---

## 4. Instrucciones de Ejecución en Ubuntu Server

```bash
# Prototipo 1: Validación de Cambio
ansible-playbook playbooks/05_cambio_controlado.yml
python3 python/validar_cambio.py

# Prototipo 2: Generador VLSM Sucursal 02
python3 python/generar_sucursal_02.py

# Prototipo 3: Auditoría de Flota
python3 python/auditar_flota.py

# Prototipo 4: Conciliación Multifuente
python3 python/validar_inventario.py

# Prototipo 5: Telemetría ICMP
python3 python/medir_conectividad.py
```
