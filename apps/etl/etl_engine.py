"""
Motor ETL Principal - HealthAnalytics IPS
Proceso completo: Extract → Transform → Load
"""
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime
from django.conf import settings
from .models import Paciente, HistorialETL

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# EXTRACT
# ──────────────────────────────────────────────────────────────────────────────
def extract(filepath: str) -> tuple[pd.DataFrame, dict]:
    """Lee el archivo Excel/CSV y retorna el DataFrame crudo + metadata."""
    inicio = time.time()
    logs = []

    if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        df = pd.read_excel(filepath, engine='openpyxl')
    else:
        df = pd.read_csv(filepath, encoding='utf-8')

    logs.append(f"[EXTRACT] Archivo leído: {filepath}")
    logs.append(f"[EXTRACT] Registros cargados: {len(df)}")
    logs.append(f"[EXTRACT] Columnas: {list(df.columns)}")
    logs.append(f"[EXTRACT] Tiempo: {time.time() - inicio:.2f}s")

    return df, {'logs': logs, 'registros_entrada': len(df)}


# ──────────────────────────────────────────────────────────────────────────────
# TRANSFORM
# ──────────────────────────────────────────────────────────────────────────────
DIAGNOSTICOS_MAP = {
    'hipertencion': 'hipertensión',
    'hipertensíon': 'hipertensión',
    'hipertension': 'hipertensión',
    'diabetis': 'diabetes',
    'diabetes melitus': 'diabetes mellitus',
    'cardiopatia': 'cardiopatía',
    'paciente sano': 'paciente sano',
}

SEXO_MAP = {
    'm': 'M', 'masculino': 'M', 'male': 'M', 'hombre': 'M',
    'f': 'F', 'femenino': 'F', 'female': 'F', 'mujer': 'F',
}

ACTIVIDAD_MAP = {
    'sedentario': 'sedentario', 'sedentaria': 'sedentario',
    'baja': 'baja', 'bajo': 'baja', 'low': 'baja',
    'media': 'media', 'moderada': 'media', 'moderate': 'media',
    'alta': 'alta', 'alto': 'alta', 'high': 'alta',
}

RANGOS_CLINICOS = {
    'edad':              (0, 130),
    'peso':              (2, 300),
    'altura':            (0.3, 2.5),
    'presion_sistolica': (50, 250),
    'presion_diastolica':(30, 150),
    'frecuencia_cardiaca':(30, 250),
    'glucosa':           (20, 600),
    'colesterol':        (50, 600),
    'saturacion_oxigeno':(50, 100),
    'temperatura':       (30, 45),
}


def _limpiar_tipos(df: pd.DataFrame, logs: list) -> tuple[pd.DataFrame, int]:
    """Convierte tipos incorrectos; registra cuántos se corrigieron."""
    corregidos = 0
    col_map = {
        'edad': 'int', 'peso': 'float', 'altura': 'float', 'IMC': 'float',
        'presión_sistólica': 'int', 'presión_diastólica': 'int',
        'frecuencia_cardiaca': 'int', 'glucosa': 'float',
        'colesterol': 'float', 'saturación_oxígeno': 'float', 'temperatura': 'float',
    }
    for col, tipo in col_map.items():
        if col not in df.columns:
            continue
        antes = df[col].dtype
        df[col] = pd.to_numeric(df[col], errors='coerce')
        if tipo == 'int':
            df[col] = df[col].astype('Int64')
        invalidos = df[col].isna().sum() - (antes == object and df[col].isna().sum())
        corregidos += int(pd.to_numeric(df[col], errors='coerce').isna().sum())

    logs.append(f"[TRANSFORM] Tipos corregidos en {len(col_map)} columnas numéricas")
    return df, corregidos


def _eliminar_duplicados(df: pd.DataFrame, logs: list) -> tuple[pd.DataFrame, int]:
    antes = len(df)
    df = df.drop_duplicates(subset=['id_paciente'])
    eliminados = antes - len(df)
    logs.append(f"[TRANSFORM] Duplicados eliminados: {eliminados}")
    return df, eliminados


def _tratar_nulos(df: pd.DataFrame, logs: list) -> tuple[pd.DataFrame, int]:
    nulos_antes = df.isnull().sum().sum()
    # Numéricas → mediana
    for col in ['peso', 'glucosa', 'colesterol', 'temperatura', 'IMC']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    # Categóricas → moda
    for col in ['sexo', 'actividad_física', 'diagnóstico_preliminar', 'riesgo_enfermedad']:
        if col in df.columns and df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'No especificado')
    nulos_despues = df.isnull().sum().sum()
    tratados = int(nulos_antes - nulos_despues)
    logs.append(f"[TRANSFORM] Nulos tratados: {tratados}")
    return df, tratados


def _validar_rangos(df: pd.DataFrame, logs: list) -> pd.DataFrame:
    col_rename = {
        'presión_sistólica': 'presion_sistolica',
        'presión_diastólica': 'presion_diastolica',
        'saturación_oxígeno': 'saturacion_oxigeno',
        'actividad_física': 'actividad_fisica',
        'diagnóstico_preliminar': 'diagnostico_preliminar',
        'riesgo_enfermedad': 'riesgo_enfermedad',
        'fecha_consulta': 'fecha_consulta',
        'IMC': 'imc',
    }
    df = df.rename(columns=col_rename)

    for col, (min_val, max_val) in RANGOS_CLINICOS.items():
        if col in df.columns:
            fuera = ((df[col] < min_val) | (df[col] > max_val)).sum()
            if fuera > 0:
                df.loc[(df[col] < min_val) | (df[col] > max_val), col] = np.nan
                logs.append(f"[TRANSFORM] {fuera} valores atípicos eliminados en '{col}'")
    return df


def _normalizar_categoricas(df: pd.DataFrame, logs: list) -> pd.DataFrame:
    if 'sexo' in df.columns:
        df['sexo'] = df['sexo'].astype(str).str.strip().str.lower().map(SEXO_MAP).fillna('O')

    if 'actividad_fisica' in df.columns:
        df['actividad_fisica'] = (df['actividad_fisica'].astype(str).str.strip()
                                  .str.lower().map(ACTIVIDAD_MAP).fillna('sedentario'))

    if 'diagnostico_preliminar' in df.columns:
        df['diagnostico_preliminar'] = (df['diagnostico_preliminar'].astype(str)
                                        .str.strip().str.lower()
                                        .map(lambda x: DIAGNOSTICOS_MAP.get(x, x))
                                        .str.title())

    if 'riesgo_enfermedad' in df.columns:
        df['riesgo_enfermedad'] = (df['riesgo_enfermedad'].astype(str)
                                   .str.strip().str.lower()
                                   .map({'bajo': 'bajo', 'medio': 'medio',
                                         'alto': 'alto', 'crítico': 'critico',
                                         'critico': 'critico'})
                                   .fillna('bajo'))

    logs.append("[TRANSFORM] Categorías normalizadas: sexo, actividad, diagnóstico, riesgo")
    return df


def _calcular_imc(df: pd.DataFrame, logs: list) -> pd.DataFrame:
    """Recalcula IMC y añade clasificación clínica."""
    mask = df['peso'].notna() & df['altura'].notna() & (df['altura'] > 0)
    df.loc[mask, 'imc'] = (df.loc[mask, 'peso'] / (df.loc[mask, 'altura'] ** 2)).round(2)

    def clasificar_imc(imc):
        if pd.isna(imc): return None
        if imc < 18.5:  return 'bajo_peso'
        if imc < 25:    return 'normal'
        if imc < 30:    return 'sobrepeso'
        return 'obesidad'

    df['clasificacion_imc'] = df['imc'].apply(clasificar_imc)
    logs.append("[TRANSFORM] IMC recalculado y clasificado")
    return df


def _detectar_criticos(df: pd.DataFrame, logs: list) -> pd.DataFrame:
    df['es_critico'] = (
        (df.get('presion_sistolica', pd.Series(dtype=float)) > 180) |
        (df.get('glucosa', pd.Series(dtype=float)) > 300) |
        (df.get('saturacion_oxigeno', pd.Series(dtype=float)) < 85)
    ).fillna(False)
    criticos = int(df['es_critico'].sum())
    logs.append(f"[TRANSFORM] Pacientes críticos detectados: {criticos}")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    logs = []
    df = df.copy()

    df, corregidos = _limpiar_tipos(df, logs)
    df, duplicados = _eliminar_duplicados(df, logs)
    df, nulos = _tratar_nulos(df, logs)
    df = _validar_rangos(df, logs)
    df = _normalizar_categoricas(df, logs)
    df = _calcular_imc(df, logs)
    df = _detectar_criticos(df, logs)

    logs.append(f"[TRANSFORM] Registros finales limpios: {len(df)}")
    return df, {
        'logs': logs,
        'registros_limpios': len(df),
        'duplicados_eliminados': duplicados,
        'nulos_tratados': nulos,
    }


# ──────────────────────────────────────────────────────────────────────────────
# LOAD
# ──────────────────────────────────────────────────────────────────────────────
def load(df: pd.DataFrame, logs: list) -> int:
    """Inserta los registros limpios en la base de datos."""
    Paciente.objects.all().delete()  # Reemplaza dataset completo
    pacientes = []
    for _, row in df.iterrows():
        p = Paciente(
            id_paciente=int(row.get('id_paciente', 0)),
            nombres=str(row.get('nombres', '')).strip().title(),
            apellidos=str(row.get('apellidos', '')).strip().title(),
            edad=None if pd.isna(row.get('edad')) else int(row['edad']),
            sexo=row.get('sexo'),
            peso=None if pd.isna(row.get('peso')) else float(row['peso']),
            altura=None if pd.isna(row.get('altura')) else float(row['altura']),
            imc=None if pd.isna(row.get('imc')) else float(row['imc']),
            clasificacion_imc=row.get('clasificacion_imc'),
            presion_sistolica=None if pd.isna(row.get('presion_sistolica')) else int(row['presion_sistolica']),
            presion_diastolica=None if pd.isna(row.get('presion_diastolica')) else int(row['presion_diastolica']),
            frecuencia_cardiaca=None if pd.isna(row.get('frecuencia_cardiaca')) else int(row['frecuencia_cardiaca']),
            glucosa=None if pd.isna(row.get('glucosa')) else float(row['glucosa']),
            colesterol=None if pd.isna(row.get('colesterol')) else float(row['colesterol']),
            saturacion_oxigeno=None if pd.isna(row.get('saturacion_oxigeno')) else float(row['saturacion_oxigeno']),
            temperatura=None if pd.isna(row.get('temperatura')) else float(row['temperatura']),
            antecedentes_familiares=bool(row.get('antecedentes_familiares', False)),
            fumador=bool(row.get('fumador', False)),
            consumo_alcohol=bool(row.get('consumo_alcohol', False)),
            actividad_fisica=row.get('actividad_fisica'),
            diagnostico_preliminar=row.get('diagnostico_preliminar'),
            riesgo_enfermedad=row.get('riesgo_enfermedad'),
            fecha_consulta=row.get('fecha_consulta') if pd.notna(row.get('fecha_consulta')) else None,
            es_critico=bool(row.get('es_critico', False)),
        )
        pacientes.append(p)

    Paciente.objects.bulk_create(pacientes, batch_size=500)
    logs.append(f"[LOAD] {len(pacientes)} pacientes cargados en BD")
    return len(pacientes)


# ──────────────────────────────────────────────────────────────────────────────
# ORQUESTADOR PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
def ejecutar_etl(filepath: str, usuario=None) -> HistorialETL:
    """Punto de entrada: ejecuta ETL completo y guarda historial."""
    inicio = time.time()
    historial = HistorialETL.objects.create(
        usuario=usuario,
        archivo_origen=filepath,
        estado='en_proceso',
    )
    todos_logs = []
    try:
        df_raw, meta_e = extract(filepath)
        todos_logs += meta_e['logs']
        historial.registros_entrada = meta_e['registros_entrada']

        df_clean, meta_t = transform(df_raw)
        todos_logs += meta_t['logs']

        load(df_clean, todos_logs)

        historial.registros_limpios = meta_t['registros_limpios']
        historial.duplicados_eliminados = meta_t['duplicados_eliminados']
        historial.nulos_tratados = meta_t['nulos_tratados']
        historial.tiempo_ejecucion_seg = round(time.time() - inicio, 2)
        historial.estado = 'completado'
        todos_logs.append(f"[ETL] Proceso completado en {historial.tiempo_ejecucion_seg}s")

    except Exception as e:
        historial.estado = 'error'
        historial.errores = str(e)
        todos_logs.append(f"[ETL ERROR] {str(e)}")
        logger.exception("Error en proceso ETL")

    historial.log_detalle = '\n'.join(todos_logs)
    historial.save()
    return historial
