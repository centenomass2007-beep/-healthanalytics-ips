# HealthAnalytics IPS — Plataforma Inteligente de Analítica Clínica

Solución FullStack para detección de riesgo médico mediante ETL, analítica de datos y Machine Learning.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 · Django 4.2 · Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Data | Pandas · NumPy · Scikit-Learn |
| BD | SQLite (dev) / PostgreSQL o MySQL (prod) |
| Frontend | HTML5 · Bootstrap 5 · Chart.js |
| Exportación | openpyxl · csv |

## Estructura del Proyecto

```
healthcare-etl-platform/
├── apps/
│   ├── authentication/   # Usuarios, roles, JWT
│   ├── etl/              # Motor ETL + modelos Paciente / HistorialETL
│   ├── analytics/        # KPIs, estadísticas, segmentación
│   ├── ml/               # Entrenamiento y predicción ML
│   ├── dashboard/        # API agregada para dashboard
│   └── reports/          # Exportación CSV / Excel
├── frontend/
│   ├── templates/        # Plantillas Django (base, dashboard, etl, ml, auth)
│   └── static/
│       ├── css/main.css
│       └── js/           # auth.js · dashboard.js · etl.js · ml.js · pacientes.js
├── datasets/             # Dataset clínico (Excel/CSV)
├── config/               # settings.py · urls.py · wsgi.py
├── requirements.txt
├── setup.sh              # Script de instalación
└── manage.py
```

## Instalación Rápida

```bash
# 1. Clona el repositorio
git clone <repo-url>
cd healthcare-etl-platform

# 2. Copia el dataset
cp /ruta/al/dataset_clinico_etl_1800_registros.xlsx datasets/dataset_clinico_etl_1800_registros.xlsx

# 3. Ejecuta el setup
chmod +x setup.sh && ./setup.sh

# 4. Levanta el servidor
source venv/bin/activate
python manage.py runserver
```

Abre http://127.0.0.1:8000 · Usuario: `admin` / Contraseña: `admin123`

## APIs REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Obtener tokens JWT |
| `/api/auth/refresh/` | POST | Refrescar access token |
| `/api/pacientes/` | GET | Lista pacientes (filtros: riesgo, sexo, critico) |
| `/api/etl/run/` | POST | Ejecutar ETL con dataset cargado |
| `/api/etl/upload/` | POST | Subir archivo y ejecutar ETL |
| `/api/etl/historial/` | GET | Historial de ejecuciones ETL |
| `/api/analytics/kpis/` | GET | KPIs médicos principales |
| `/api/analytics/estadisticas/` | GET | Estadística descriptiva |
| `/api/analytics/segmentacion/` | GET | Segmentación por edad, IMC, diagnóstico |
| `/api/analytics/tendencias/` | GET | Tendencias de consultas mensuales |
| `/api/ml/entrenar/` | POST | Entrenar modelo ML |
| `/api/ml/predecir/` | POST | Predecir riesgo de un paciente |
| `/api/ml/modelos/` | GET | Listar modelos entrenados |
| `/api/dashboard/kpis/` | GET | Datos agregados para dashboard |
| `/api/reportes/csv/` | GET | Exportar pacientes en CSV |
| `/api/reportes/excel/` | GET | Exportar pacientes en Excel |

## Proceso ETL

```
EXTRACT  →  Lee Excel/CSV con 1800 registros simulados (con errores intencionales)
TRANSFORM → Elimina duplicados · Trata nulos · Corrige tipos · Valida rangos clínicos
             Normaliza categorías · Recalcula IMC · Detecta pacientes críticos
LOAD     →  Inserta registros limpios en BD · Registra historial con logs y métricas
```

## Machine Learning

Algoritmos disponibles: **Random Forest**, **Regresión Logística**, **Árbol de Decisión**

Variables predictoras: IMC, Edad, Glucosa, Colesterol, Presión sistólica/diastólica,
Frecuencia cardíaca, Saturación O₂, Temperatura, Fumador, Consumo alcohol, Antecedentes familiares

Métricas reportadas: Accuracy · Precision · Recall · F1-Score · Matriz de Confusión

## Roles del Sistema

| Rol | Acceso |
|-----|--------|
| Administrador | Gestión completa (usuarios, ETL, ML, reportes) |
| Médico | Visualización clínica y predicciones |
| Analista | ETL, analítica y exportación |

## Criterios de Detección de Pacientes Críticos

- Presión sistólica > 180 mmHg
- Glucosa > 300 mg/dL
- Saturación de oxígeno < 85%
