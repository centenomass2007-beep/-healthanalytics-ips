# Documentación Técnica — HealthAnalytics IPS

## Tabla de Contenidos
1. [Arquitectura del Sistema](#arquitectura)
2. [Modelo de Datos (ERD)](#erd)
3. [Flujo ETL Detallado](#etl)
4. [Módulo de Machine Learning](#ml)
5. [API REST — Referencia Completa](#api)
6. [Seguridad](#seguridad)
7. [Instalación y Despliegue](#instalacion)
8. [Variables de Entorno](#env)
9. [Pruebas](#tests)

---

## 1. Arquitectura del Sistema {#arquitectura}

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE                              │
│          Browser (Bootstrap 5 + Chart.js)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / REST + JWT
┌────────────────────────▼────────────────────────────────────┐
│                   NGINX (puerto 80)                         │
│            Proxy inverso + archivos estáticos               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              DJANGO (Gunicorn, puerto 8000)                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ auth         │  │ etl          │  │ analytics        │  │
│  │ JWT + Roles  │  │ ETL Engine   │  │ KPIs + Stats     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ ml           │  │ dashboard    │  │ reports          │  │
│  │ Sklearn      │  │ API agregada │  │ CSV / Excel      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ ORM (psycopg2 / sqlite3)
┌────────────────────────▼────────────────────────────────────┐
│            PostgreSQL / SQLite                              │
│   authentication_usuario  etl_paciente  etl_historialetl    │
│   analytics_estadistica   ml_modeloml   ml_prediccion       │
└─────────────────────────────────────────────────────────────┘
```

### Principios de diseño
- **Separación de responsabilidades**: cada app Django tiene una única responsabilidad.
- **API-first**: el frontend consume la misma API REST que estaría disponible para terceros.
- **Stateless**: la autenticación es completamente basada en JWT, sin sesiones del lado servidor.
- **Trazabilidad**: cada ejecución ETL genera un registro de historial con logs detallados.

---

## 2. Modelo de Datos (ERD) {#erd}

```
authentication_usuario
├── id (PK)
├── username (UNIQUE)
├── email
├── password (hash)
├── rol: administrador | medico | analista
└── fecha_creacion

etl_paciente
├── id (PK)
├── id_paciente (UNIQUE, del dataset original)
├── nombres, apellidos
├── edad, sexo, peso, altura
├── imc, clasificacion_imc              ← Calculado en Transform
├── presion_sistolica, presion_diastolica
├── frecuencia_cardiaca
├── glucosa, colesterol
├── saturacion_oxigeno, temperatura
├── antecedentes_familiares, fumador, consumo_alcohol
├── actividad_fisica
├── diagnostico_preliminar
├── riesgo_enfermedad: bajo|medio|alto|critico
├── es_critico (Boolean)                ← Calculado en Transform
└── fecha_carga

etl_historialetl
├── id (PK)
├── usuario_id (FK → authentication_usuario)
├── fecha_ejecucion
├── archivo_origen
├── registros_entrada / registros_limpios
├── duplicados_eliminados / nulos_tratados
├── tiempo_ejecucion_seg
├── estado: pendiente|en_proceso|completado|error
├── log_detalle (TEXT)
└── errores (TEXT)

analytics_estadisticaclinica
├── id (PK)
├── fecha_calculo
├── total_pacientes, pacientes_criticos
├── pacientes_hipertensos, pacientes_diabeticos, pacientes_fumadores
├── promedio_edad, promedio_imc, promedio_glucosa, promedio_colesterol
└── riesgo_bajo / medio / alto / critico

ml_modeloml
├── id (PK)
├── nombre, algoritmo
├── fecha_entrenamiento
├── accuracy, precision, recall, f1_score
├── matriz_confusion (JSON)
├── variables_predictoras (JSON)
└── activo (Boolean)

ml_prediccionpaciente
├── id (PK)
├── paciente_id (FK → etl_paciente)
├── modelo_id   (FK → ml_modeloml)
├── probabilidad_riesgo
├── riesgo_predicho
└── fecha_prediccion
```

---

## 3. Flujo ETL Detallado {#etl}

### EXTRACT
```
Fuente: Excel (.xlsx) o CSV
  ↓
pd.read_excel() / pd.read_csv()
  ↓
Validación de estructura (columnas requeridas)
  ↓
Registro: registros_entrada, tiempo, fuente
```

### TRANSFORM — Reglas aplicadas en orden

| Paso | Operación | Detalle |
|------|-----------|---------|
| 1 | Corrección de tipos | `pd.to_numeric(errors='coerce')` en todas las columnas numéricas |
| 2 | Eliminación de duplicados | `drop_duplicates(subset=['id_paciente'])` |
| 3 | Tratamiento de nulos | Numéricas → mediana; Categóricas → moda |
| 4 | Validación de rangos | Valores fuera de rango → `NaN` (ej. peso > 300 kg) |
| 5 | Normalización de sexo | `'masculino'`, `'male'`, `'hombre'` → `'M'` |
| 6 | Normalización diagnósticos | `'hipertencion'` → `'hipertensión'` (mapa de correcciones) |
| 7 | Normalización actividad física | `'sedentaria'` → `'sedentario'`, etc. |
| 8 | Cálculo IMC | `peso / altura²`, clasificación clínica |
| 9 | Detección de críticos | P.sistólica > 180 OR glucosa > 300 OR SatO2 < 85 |

### LOAD
```
Paciente.objects.all().delete()   ← Reemplaza dataset completo
Paciente.objects.bulk_create(pacientes, batch_size=500)
HistorialETL.save() con logs completos
```

---

## 4. Módulo de Machine Learning {#ml}

### Variables predictoras
`edad`, `imc`, `glucosa`, `colesterol`, `presion_sistolica`, `presion_diastolica`,
`frecuencia_cardiaca`, `saturacion_oxigeno`, `temperatura`, `fumador`,
`consumo_alcohol`, `antecedentes_familiares`

### Variable objetivo
`riesgo_enfermedad` → codificada con `LabelEncoder` → clases: bajo, medio, alto, critico

### Flujo de entrenamiento
```
Paciente.objects.exclude(riesgo_enfermedad__isnull=True)
  ↓ 80% train / 20% test  (stratify=riesgo)
  ↓ StandardScaler().fit_transform(X_train)
  ↓ Algoritmo.fit(X_train_scaled, y_train)
  ↓ Métricas: accuracy, precision, recall, f1 (weighted)
  ↓ Matriz de confusión
  ↓ ModeloML.objects.create(...) — desactiva versiones anteriores del mismo algoritmo
```

### Algoritmos y parámetros

| Algoritmo | Parámetros clave |
|-----------|-----------------|
| Random Forest | n_estimators=100, random_state=42 |
| Logistic Regression | max_iter=500, random_state=42 |
| Decision Tree | max_depth=8, random_state=42 |

---

## 5. API REST — Referencia Completa {#api}

La documentación interactiva completa está disponible en:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/docs/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Autenticación

Todas las rutas (excepto login) requieren el header:
```
Authorization: Bearer <access_token>
```

#### POST /api/auth/login/
```json
// Request
{ "username": "admin", "password": "admin123" }

// Response 200
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

#### POST /api/auth/refresh/
```json
// Request
{ "refresh": "eyJ..." }
// Response: { "access": "eyJ..." }
```

#### GET /api/auth/perfil/
```json
// Response 200
{
  "id": 1, "username": "admin",
  "email": "admin@healthanalytics.co",
  "rol": "administrador"
}
```

### Pacientes

#### GET /api/pacientes/
Query params: `riesgo`, `sexo`, `critico=true`, `page`
```json
// Response 200
{
  "count": 1800,
  "next": "http://localhost:8000/api/pacientes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1, "id_paciente": 1001,
      "nombres": "Juan", "apellidos": "Pérez",
      "edad": 45, "sexo": "M",
      "imc": 27.3, "clasificacion_imc": "sobrepeso",
      "glucosa": 142.5, "presion_sistolica": 155,
      "riesgo_enfermedad": "alto", "es_critico": false
    }
  ]
}
```

### ETL

#### POST /api/etl/run/
```json
// Response 200
{
  "id": 5,
  "estado": "completado",
  "registros_entrada": 1850,
  "registros_limpios": 1800,
  "duplicados_eliminados": 50,
  "nulos_tratados": 234,
  "tiempo_ejecucion_seg": 1.08,
  "log_detalle": "[EXTRACT] Registros cargados: 1850\n[TRANSFORM]..."
}
```

#### POST /api/etl/upload/
```
Content-Type: multipart/form-data
Body: archivo=<file.xlsx>
```

#### GET /api/etl/historial/
```json
// Response 200 — Array de HistorialETL
[{ "id": 5, "estado": "completado", "registros_limpios": 1800, ... }]
```

### Analytics

#### GET /api/analytics/kpis/
```json
{
  "total_pacientes": 1800,
  "pacientes_criticos": 87,    "pct_criticos": 4.8,
  "pacientes_hipertensos": 423, "pct_hipertensos": 23.5,
  "pacientes_diabeticos": 312,  "pct_diabeticos": 17.3,
  "pacientes_fumadores": 540,   "pct_fumadores": 30.0,
  "distribucion_riesgo": { "bajo": 620, "medio": 580, "alto": 430, "critico": 170 },
  "promedios": { "avg_edad": 46.2, "avg_imc": 26.8, "avg_glucosa": 118.4 }
}
```

#### GET /api/analytics/estadisticas/
```json
{
  "edad":    { "media": 46.2, "mediana": 46, "moda": 45, "desviacion_std": 15.3, ... },
  "glucosa": { "media": 118.4, "mediana": 105.0, ... },
  ...
}
```

### Machine Learning

#### POST /api/ml/entrenar/
```json
// Request
{ "algoritmo": "random_forest" }

// Response 200
{
  "modelo": { "id": 3, "nombre": "Random Forest v3", "activo": true },
  "metricas": {
    "accuracy": 0.8722,
    "precision": 0.8651,
    "recall": 0.8722,
    "f1_score": 0.8680,
    "confusion_matrix": [[120, 8, 3, 1], [7, 95, 5, 2], ...],
    "clases": ["alto", "bajo", "critico", "medio"]
  }
}
```

#### POST /api/ml/predecir/
```json
// Request
{ "paciente_id": 1045 }

// Response 200
{
  "paciente_id": 1045,
  "riesgo_predicho": "alto",
  "probabilidad": 0.7823,
  "distribucion_clases": { "bajo": 0.05, "medio": 0.12, "alto": 0.78, "critico": 0.05 }
}
```

### Dashboard

#### GET /api/dashboard/kpis/
Retorna KPIs + datos de todas las gráficas en una sola llamada para optimizar el dashboard.

### Reportes

#### GET /api/reportes/csv/
Descarga CSV con BOM UTF-8 (compatible con Excel).

#### GET /api/reportes/excel/
Descarga Excel `.xlsx` con celdas coloreadas según nivel de riesgo.

---

## 6. Seguridad {#seguridad}

| Medida | Implementación |
|--------|---------------|
| Autenticación | JWT con expiración configurable (60 min access, 7 días refresh) |
| Rotación de tokens | `ROTATE_REFRESH_TOKENS=True` |
| CORS | `django-cors-headers` con dominios permitidos |
| CSRF | Protección Django activa en vistas HTML |
| Sanitización | DRF serializers validan todos los inputs |
| Roles | Verificación de `usuario.rol` en vistas sensibles |
| Variables sensibles | `.env` — nunca en código fuente |

---

## 7. Instalación y Despliegue {#instalacion}

### Desarrollo local (SQLite)
```bash
git clone <repo> && cd healthcare-etl-platform
chmod +x setup.sh && ./setup.sh
# Copiar dataset a datasets/dataset_clinico.xlsx
python manage.py cargar_dataset
python manage.py runserver
```

### Docker (PostgreSQL + Nginx)
```bash
# Copiar dataset
cp /ruta/dataset.xlsx datasets/dataset_clinico.xlsx

# Levantar servicios
docker-compose up --build -d

# Ver logs
docker-compose logs -f web
```

Servicios disponibles:
- App: `http://localhost`
- API Docs: `http://localhost/api/docs/`
- Admin Django: `http://localhost/admin/`

---

## 8. Variables de Entorno {#env}

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta Django | insecure-key-dev |
| `DEBUG` | Modo debug | True |
| `ALLOWED_HOSTS` | Hosts permitidos | localhost,127.0.0.1 |
| `DB_ENGINE` | Motor de BD | sqlite3 |
| `DB_NAME` | Nombre de la BD | db.sqlite3 |
| `DB_USER` | Usuario BD | — |
| `DB_PASSWORD` | Contraseña BD | — |
| `DB_HOST` | Host BD | localhost |
| `DB_PORT` | Puerto BD | 5432 |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Expiración access | 60 |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Expiración refresh | 7 |

---

## 9. Pruebas {#tests}

```bash
# Ejecutar todos los tests
python manage.py test apps --verbosity=2

# App específica
python manage.py test apps.etl
python manage.py test apps.ml

# Con coverage
pip install coverage
coverage run manage.py test apps
coverage report -m
coverage html  # Genera htmlcov/index.html
```

### Suite de pruebas: 33 tests

| App | Tests | Cubre |
|-----|-------|-------|
| authentication | 6 | Login, refresh, perfil, roles, credenciales inválidas |
| etl | 14 | Extract Excel/CSV, Transform (duplicados, nulos, atípicos, normalización, IMC), Load, Orquestador, API |
| analytics | 8 | KPIs, estadística descriptiva, segmentación edad/IMC, API endpoints |
| reports | 5 | Exportación CSV, Excel, autenticación requerida |
