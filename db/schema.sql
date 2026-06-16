CREATE TABLE IF NOT EXISTS pacientes (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellido VARCHAR(100) NOT NULL,
  sexo CHAR(1) NOT NULL CHECK (sexo IN ('M', 'F')),
  edad INTEGER NOT NULL CHECK (edad >= 0 AND edad <= 120),
  peso DECIMAL(5,1) NOT NULL,
  altura DECIMAL(4,2) NOT NULL,
  imc DECIMAL(4,1) NOT NULL,
  glucosa DECIMAL(6,1) NOT NULL,
  colesterol DECIMAL(6,1) NOT NULL,
  presion_sistolica INTEGER NOT NULL,
  presion_diastolica INTEGER NOT NULL,
  frecuencia_cardiaca INTEGER NOT NULL,
  saturacion_oxigeno DECIMAL(4,1) NOT NULL,
  temperatura DECIMAL(3,1) NOT NULL,
  fumador BOOLEAN NOT NULL DEFAULT FALSE,
  antecedentes BOOLEAN NOT NULL DEFAULT FALSE,
  diagnostico VARCHAR(100) NOT NULL,
  riesgo VARCHAR(10) NOT NULL CHECK (riesgo IN ('Bajo', 'Medio', 'Alto', 'Crítico')),
  fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'medico', 'analista')),
  password_hash VARCHAR(255) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  ultimo_acceso TIMESTAMP,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historial_etl (
  id SERIAL PRIMARY KEY,
  fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuario VARCHAR(100) NOT NULL,
  registros_originales INTEGER NOT NULL,
  registros_limpios INTEGER NOT NULL,
  duplicados_eliminados INTEGER DEFAULT 0,
  nulos_imputados INTEGER DEFAULT 0,
  tiempo_ejecucion VARCHAR(20),
  estado VARCHAR(10) NOT NULL CHECK (estado IN ('ok', 'err', 'run')),
  detalles TEXT
);

CREATE TABLE IF NOT EXISTS metricas_ml (
  id SERIAL PRIMARY KEY,
  algoritmo VARCHAR(50) NOT NULL,
  accuracy DECIMAL(5,2) NOT NULL,
  precision DECIMAL(5,2) NOT NULL,
  recall DECIMAL(5,2) NOT NULL,
  f1_score DECIMAL(5,2) NOT NULL,
  entrenado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
