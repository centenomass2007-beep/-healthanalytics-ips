-- ============================================================
-- HealthAnalytics IPS — Schema SQL
-- Compatible con PostgreSQL 14+ y MySQL 8+
-- Generado para referencia y despliegue manual
-- ============================================================

-- ─── Extensiones (PostgreSQL) ────────────────────────────────
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── 1. Usuarios ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS authentication_usuario (
    id                  SERIAL PRIMARY KEY,
    password            VARCHAR(128)   NOT NULL,
    last_login          TIMESTAMP WITH TIME ZONE,
    is_superuser        BOOLEAN        NOT NULL DEFAULT FALSE,
    username            VARCHAR(150)   NOT NULL UNIQUE,
    first_name          VARCHAR(150)   NOT NULL DEFAULT '',
    last_name           VARCHAR(150)   NOT NULL DEFAULT '',
    email               VARCHAR(254)   NOT NULL DEFAULT '',
    is_staff            BOOLEAN        NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN        NOT NULL DEFAULT TRUE,
    date_joined         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    rol                 VARCHAR(20)    NOT NULL DEFAULT 'analista'
                        CHECK (rol IN ('administrador','medico','analista')),
    fecha_creacion      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usuario_username ON authentication_usuario(username);
CREATE INDEX idx_usuario_rol      ON authentication_usuario(rol);

-- ─── 2. Pacientes ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS etl_paciente (
    id                      SERIAL PRIMARY KEY,
    id_paciente             INTEGER        NOT NULL UNIQUE,
    nombres                 VARCHAR(100)   NOT NULL,
    apellidos               VARCHAR(100)   NOT NULL,
    edad                    INTEGER,
    sexo                    CHAR(1)        CHECK (sexo IN ('M','F','O')),
    peso                    DOUBLE PRECISION,
    altura                  DOUBLE PRECISION,
    imc                     DOUBLE PRECISION,
    clasificacion_imc       VARCHAR(20)
                            CHECK (clasificacion_imc IN ('bajo_peso','normal','sobrepeso','obesidad')),
    presion_sistolica       INTEGER,
    presion_diastolica      INTEGER,
    frecuencia_cardiaca     INTEGER,
    glucosa                 DOUBLE PRECISION,
    colesterol              DOUBLE PRECISION,
    saturacion_oxigeno      DOUBLE PRECISION,
    temperatura             DOUBLE PRECISION,
    antecedentes_familiares BOOLEAN        NOT NULL DEFAULT FALSE,
    fumador                 BOOLEAN        NOT NULL DEFAULT FALSE,
    consumo_alcohol         BOOLEAN        NOT NULL DEFAULT FALSE,
    actividad_fisica        VARCHAR(20)
                            CHECK (actividad_fisica IN ('sedentario','baja','media','alta')),
    diagnostico_preliminar  VARCHAR(200),
    riesgo_enfermedad       VARCHAR(10)
                            CHECK (riesgo_enfermedad IN ('bajo','medio','alto','critico')),
    fecha_consulta          DATE,
    es_critico              BOOLEAN        NOT NULL DEFAULT FALSE,
    fecha_carga             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_paciente_riesgo    ON etl_paciente(riesgo_enfermedad);
CREATE INDEX idx_paciente_critico   ON etl_paciente(es_critico);
CREATE INDEX idx_paciente_sexo      ON etl_paciente(sexo);
CREATE INDEX idx_paciente_edad      ON etl_paciente(edad);
CREATE INDEX idx_paciente_diagnostico ON etl_paciente(diagnostico_preliminar);
CREATE INDEX idx_paciente_fecha     ON etl_paciente(fecha_consulta);

-- ─── 3. Historial ETL ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS etl_historialetl (
    id                      SERIAL PRIMARY KEY,
    usuario_id              INTEGER        REFERENCES authentication_usuario(id) ON DELETE SET NULL,
    fecha_ejecucion         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    archivo_origen          VARCHAR(255)   NOT NULL DEFAULT '',
    registros_entrada       INTEGER        NOT NULL DEFAULT 0,
    registros_limpios       INTEGER        NOT NULL DEFAULT 0,
    duplicados_eliminados   INTEGER        NOT NULL DEFAULT 0,
    nulos_tratados          INTEGER        NOT NULL DEFAULT 0,
    tiempo_ejecucion_seg    DOUBLE PRECISION NOT NULL DEFAULT 0,
    estado                  VARCHAR(20)    NOT NULL DEFAULT 'pendiente'
                            CHECK (estado IN ('pendiente','en_proceso','completado','error')),
    log_detalle             TEXT           NOT NULL DEFAULT '',
    errores                 TEXT           NOT NULL DEFAULT ''
);

CREATE INDEX idx_historialetl_estado ON etl_historialetl(estado);
CREATE INDEX idx_historialetl_fecha  ON etl_historialetl(fecha_ejecucion DESC);

-- ─── 4. Estadísticas Clínicas (snapshots analítica) ───────────
CREATE TABLE IF NOT EXISTS analytics_estadisticaclinica (
    id                      SERIAL PRIMARY KEY,
    fecha_calculo           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_pacientes         INTEGER        NOT NULL DEFAULT 0,
    pacientes_criticos      INTEGER        NOT NULL DEFAULT 0,
    pacientes_hipertensos   INTEGER        NOT NULL DEFAULT 0,
    pacientes_diabeticos    INTEGER        NOT NULL DEFAULT 0,
    pacientes_fumadores     INTEGER        NOT NULL DEFAULT 0,
    promedio_edad           DOUBLE PRECISION,
    promedio_imc            DOUBLE PRECISION,
    promedio_glucosa        DOUBLE PRECISION,
    promedio_colesterol     DOUBLE PRECISION,
    riesgo_bajo             INTEGER        NOT NULL DEFAULT 0,
    riesgo_medio            INTEGER        NOT NULL DEFAULT 0,
    riesgo_alto             INTEGER        NOT NULL DEFAULT 0,
    riesgo_critico          INTEGER        NOT NULL DEFAULT 0
);

-- ─── 5. Modelos ML ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ml_modeloml (
    id                      SERIAL PRIMARY KEY,
    nombre                  VARCHAR(100)   NOT NULL,
    algoritmo               VARCHAR(30)    NOT NULL
                            CHECK (algoritmo IN ('logistic_regression','decision_tree','random_forest')),
    fecha_entrenamiento     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    accuracy                DOUBLE PRECISION,
    precision               DOUBLE PRECISION,
    recall                  DOUBLE PRECISION,
    f1_score                DOUBLE PRECISION,
    matriz_confusion        JSONB,
    variables_predictoras   JSONB          NOT NULL DEFAULT '[]',
    activo                  BOOLEAN        NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_modeloml_algoritmo ON ml_modeloml(algoritmo);
CREATE INDEX idx_modeloml_activo    ON ml_modeloml(activo);

-- ─── 6. Predicciones ML ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS ml_prediccionpaciente (
    id                      SERIAL PRIMARY KEY,
    paciente_id             INTEGER        NOT NULL REFERENCES etl_paciente(id) ON DELETE CASCADE,
    modelo_id               INTEGER        NOT NULL REFERENCES ml_modeloml(id) ON DELETE CASCADE,
    probabilidad_riesgo     DOUBLE PRECISION NOT NULL,
    riesgo_predicho         VARCHAR(10)    NOT NULL,
    fecha_prediccion        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prediccion_paciente ON ml_prediccionpaciente(paciente_id);
CREATE INDEX idx_prediccion_modelo   ON ml_prediccionpaciente(modelo_id);
CREATE INDEX idx_prediccion_fecha    ON ml_prediccionpaciente(fecha_prediccion DESC);

-- ─── Vistas útiles ────────────────────────────────────────────

-- Vista: Resumen clínico por paciente
CREATE OR REPLACE VIEW v_resumen_clinico AS
SELECT
    p.id_paciente,
    p.nombres || ' ' || p.apellidos AS nombre_completo,
    p.edad,
    p.sexo,
    p.imc,
    p.clasificacion_imc,
    p.presion_sistolica,
    p.glucosa,
    p.colesterol,
    p.riesgo_enfermedad,
    p.es_critico,
    CASE
        WHEN p.presion_sistolica > 180 THEN 'Hipertensión severa'
        WHEN p.presion_sistolica > 140 THEN 'Hipertensión'
        ELSE 'Presión normal'
    END AS estado_presion,
    CASE
        WHEN p.glucosa > 300 THEN 'Diabetes severa'
        WHEN p.glucosa > 126 THEN 'Diabetes'
        WHEN p.glucosa > 100 THEN 'Pre-diabetes'
        ELSE 'Glucosa normal'
    END AS estado_glucosa,
    (SELECT pr.riesgo_predicho
     FROM ml_prediccionpaciente pr
     WHERE pr.paciente_id = p.id
     ORDER BY pr.fecha_prediccion DESC
     LIMIT 1) AS ultimo_riesgo_predicho
FROM etl_paciente p;

-- Vista: KPIs generales
CREATE OR REPLACE VIEW v_kpis_clinicos AS
SELECT
    COUNT(*)                                                      AS total_pacientes,
    COUNT(*) FILTER (WHERE es_critico = TRUE)                     AS pacientes_criticos,
    COUNT(*) FILTER (WHERE presion_sistolica > 140)               AS hipertensos,
    COUNT(*) FILTER (WHERE glucosa > 126)                         AS diabeticos,
    COUNT(*) FILTER (WHERE fumador = TRUE)                        AS fumadores,
    ROUND(AVG(edad)::NUMERIC, 1)                                  AS promedio_edad,
    ROUND(AVG(imc)::NUMERIC, 2)                                   AS promedio_imc,
    ROUND(AVG(glucosa)::NUMERIC, 2)                               AS promedio_glucosa,
    COUNT(*) FILTER (WHERE riesgo_enfermedad = 'bajo')            AS riesgo_bajo,
    COUNT(*) FILTER (WHERE riesgo_enfermedad = 'medio')           AS riesgo_medio,
    COUNT(*) FILTER (WHERE riesgo_enfermedad = 'alto')            AS riesgo_alto,
    COUNT(*) FILTER (WHERE riesgo_enfermedad = 'critico')         AS riesgo_critico
FROM etl_paciente;

-- Vista: Historial ETL resumido
CREATE OR REPLACE VIEW v_historial_etl AS
SELECT
    h.id,
    u.username                                          AS usuario,
    h.fecha_ejecucion,
    h.registros_entrada,
    h.registros_limpios,
    h.duplicados_eliminados,
    h.nulos_tratados,
    h.tiempo_ejecucion_seg,
    h.estado,
    ROUND(
        (h.registros_limpios::NUMERIC / NULLIF(h.registros_entrada, 0)) * 100, 1
    )                                                   AS pct_calidad
FROM etl_historialetl h
LEFT JOIN authentication_usuario u ON u.id = h.usuario_id
ORDER BY h.fecha_ejecucion DESC;

-- ─── Datos iniciales ──────────────────────────────────────────
-- Superusuario administrador (contraseña: admin123)
-- NOTA: La contraseña real debe generarse con Django:
--   python manage.py createsuperuser
-- Este es solo un placeholder de referencia.
INSERT INTO authentication_usuario
    (password, is_superuser, username, email, is_staff, is_active, rol)
VALUES
    ('pbkdf2_sha256$600000$placeholder$hash=', TRUE,
     'admin', 'admin@healthanalytics.co', TRUE, TRUE, 'administrador')
ON CONFLICT (username) DO NOTHING;
