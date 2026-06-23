# Manual de Usuario — HealthAnalytics IPS

## 1. Acceso al Sistema

Abre tu navegador y ve a `http://localhost:8000` (o la URL de producción).

Serás redirigido automáticamente a la pantalla de **Login**.

### Credenciales por defecto

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin123 | Administrador |

> **Seguridad**: Cambia la contraseña del administrador después del primer acceso desde el panel `/admin/`.

---

## 2. Dashboard Principal

Al ingresar verás el **Dashboard Clínico** con:

### Tarjetas KPI (fila superior)
- **Total Pacientes**: total de registros cargados en BD.
- **Pacientes Críticos**: pacientes con P.sistólica > 180, glucosa > 300 o SatO₂ < 85.
- **Hipertensos**: P.sistólica > 140 mmHg.
- **Diabéticos**: glucosa > 126 mg/dL.

### Tarjetas secundarias
- Fumadores y su porcentaje del total.
- Promedio de IMC y Glucosa de la población.

### Gráficas
- **Distribución por Riesgo** (dona): porcentaje de pacientes en cada nivel.
- **Pacientes por Rango de Edad** (barras): segmentación etaria.
- **Clasificación IMC** (torta): bajo peso / normal / sobrepeso / obesidad.
- **Top 10 Diagnósticos** (barras horizontales): diagnósticos más frecuentes.

### Panel de Estado
- Fecha y resultado del último proceso ETL.
- Nombre y accuracy del modelo ML activo.

---

## 3. Gestión de Pacientes

Navega a **Pacientes** en el menú lateral.

### Filtros disponibles
| Filtro | Opciones |
|--------|---------|
| Riesgo | Todos / Bajo / Medio / Alto / Crítico |
| Sexo | Todos / Masculino / Femenino |
| Solo críticos | Activar para ver únicamente pacientes críticos |
| Búsqueda libre | Filtra por nombre, apellido o diagnóstico |

### Tabla de pacientes
Las filas en **rojo** indican pacientes críticos. Los valores de glucosa y presión sistólica se resaltan en rojo cuando superan los umbrales clínicos.

### Exportar datos
- **CSV**: compatible con Excel y cualquier herramienta de análisis.
- **Excel**: archivo `.xlsx` con celdas coloreadas por nivel de riesgo (verde=bajo, amarillo=medio, naranja=alto, rojo=crítico).

---

## 4. Proceso ETL

Navega a **Proceso ETL** en el menú lateral.

### Ejecutar ETL con dataset cargado
1. Haz clic en **Ejecutar ETL Ahora**.
2. Espera a que la barra de progreso termine (1–5 segundos para 1.800 registros).
3. Se mostrará el resultado con:
   - Registros de entrada / registros limpios.
   - Duplicados eliminados / nulos tratados.
   - Tiempo de ejecución.
   - Log detallado con cada paso del proceso.

### Subir un nuevo dataset
1. Haz clic en **Elegir archivo** y selecciona tu archivo `.csv`, `.xlsx` o `.xls`.
2. El archivo debe contener las columnas del dataset clínico estándar.
3. Haz clic en **Subir y Procesar** — el ETL se ejecuta automáticamente.

### Historial de ejecuciones
La tabla inferior muestra todas las ejecuciones con fecha, usuario, conteos y estado. Los estados posibles son:
- 🟢 **completado** — proceso exitoso.
- 🔴 **error** — falló (ver log para detalle).
- 🟡 **en_proceso** — corriendo actualmente.

---

## 5. Machine Learning

Navega a **Machine Learning** en el menú lateral.

### Entrenar un modelo
1. Selecciona el algoritmo en el desplegable:
   - **Random Forest** — recomendado, mejor rendimiento general.
   - **Regresión Logística** — más interpretable.
   - **Árbol de Decisión** — útil para reglas simples.
2. Haz clic en **Entrenar Modelo**.
3. Espera 5–30 segundos según el tamaño del dataset.
4. Se mostrarán las métricas: Accuracy, Precision, Recall y F1-Score con barras de progreso.
5. Aparecerá la **Matriz de Confusión** mostrando predicciones correctas (diagonal verde) vs. errores.

### Interpretar métricas

| Métrica | Qué mide | Valor ideal |
|---------|---------|-------------|
| **Accuracy** | % de predicciones correctas en total | > 80% |
| **Precision** | De los que predije como riesgo X, ¿cuántos lo eran? | > 75% |
| **Recall** | De los que realmente son riesgo X, ¿cuántos detecté? | > 75% |
| **F1-Score** | Balance entre Precision y Recall | > 77% |

### Predecir riesgo de un paciente
1. Ingresa el **ID del paciente** (el número `id_paciente` del dataset).
2. Haz clic en **Predecir Riesgo**.
3. Verás el nivel de riesgo predicho, la probabilidad y la distribución entre todas las clases.

### Modelos entrenados
La tabla inferior muestra el historial de modelos. El **activo** es el más reciente por algoritmo.

---

## 6. Exportación de Reportes

Desde el menú lateral o la página de Pacientes:

- **Exportar CSV** → descarga `pacientes.csv` con todos los pacientes procesados.
- **Exportar Excel** → descarga `reporte_pacientes.xlsx` con formato y colores.

Ambos formatos incluyen todos los campos clínicos: identificación, signos vitales, diagnóstico, IMC y nivel de riesgo.

---

## 7. Roles y Permisos

| Función | Admin | Médico | Analista |
|---------|-------|--------|---------|
| Ver dashboard | ✅ | ✅ | ✅ |
| Ver pacientes | ✅ | ✅ | ✅ |
| Ejecutar ETL | ✅ | ❌ | ✅ |
| Subir dataset | ✅ | ❌ | ✅ |
| Entrenar modelos | ✅ | ❌ | ✅ |
| Predecir paciente | ✅ | ✅ | ✅ |
| Exportar reportes | ✅ | ✅ | ✅ |
| Gestionar usuarios | ✅ | ❌ | ❌ |
| Panel de administración | ✅ | ❌ | ❌ |

---

## 8. Panel de Administración Django

Accede a `http://localhost:8000/admin/` con el usuario administrador.

Desde aquí puedes:
- Crear, editar y eliminar **usuarios** y asignar roles.
- Ver y buscar **pacientes** cargados con todos sus campos.
- Revisar el **historial ETL** con logs completos.
- Consultar **modelos ML** entrenados y sus métricas.

---

## 9. Solución de Problemas Frecuentes

**"Dataset no encontrado" al ejecutar ETL**
→ Copia tu archivo Excel como `datasets/dataset_clinico.xlsx` o usa la opción "Subir Dataset".

**"Dataset insuficiente para entrenar" al entrenar ML**
→ Asegúrate de haber ejecutado el ETL primero. Se necesitan mínimo 50 registros con `riesgo_enfermedad` definido.

**La página redirige al login constantemente**
→ El token JWT expiró. Recarga la página para refrescarlo automáticamente, o haz login nuevamente.

**Valores en la tabla de pacientes muestran "—"**
→ El ETL no ha sido ejecutado aún, o el campo era nulo/inválido en el dataset original.
