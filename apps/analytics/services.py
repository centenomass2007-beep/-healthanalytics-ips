"""
Módulo de Analítica de Datos - HealthAnalytics IPS
Estadística descriptiva, KPIs clínicos, segmentación
"""
import pandas as pd
import numpy as np
from django.db.models import Avg, Count, Q
from apps.etl.models import Paciente
from .models import EstadisticaClinica


def obtener_estadisticas_descriptivas() -> dict:
    """Media, mediana, moda, desviación estándar de variables numéricas."""
    qs = Paciente.objects.all()
    if not qs.exists():
        return {}

    df = pd.DataFrame(list(qs.values(
        'edad', 'peso', 'altura', 'imc', 'presion_sistolica',
        'presion_diastolica', 'frecuencia_cardiaca', 'glucosa',
        'colesterol', 'saturacion_oxigeno', 'temperatura'
    )))

    resultado = {}
    for col in df.columns:
        serie = df[col].dropna()
        if len(serie) == 0:
            continue
        resultado[col] = {
            'media': round(float(serie.mean()), 2),
            'mediana': round(float(serie.median()), 2),
            'moda': round(float(serie.mode()[0]), 2) if not serie.mode().empty else None,
            'desviacion_std': round(float(serie.std()), 2),
            'min': round(float(serie.min()), 2),
            'max': round(float(serie.max()), 2),
            'q25': round(float(serie.quantile(0.25)), 2),
            'q75': round(float(serie.quantile(0.75)), 2),
        }
    return resultado


def obtener_kpis() -> dict:
    """KPIs médicos principales."""
    total = Paciente.objects.count()
    if total == 0:
        return {'total': 0}

    criticos = Paciente.objects.filter(es_critico=True).count()
    hipertensos = Paciente.objects.filter(presion_sistolica__gt=140).count()
    diabeticos = Paciente.objects.filter(glucosa__gt=126).count()
    fumadores = Paciente.objects.filter(fumador=True).count()

    riesgos = (Paciente.objects.values('riesgo_enfermedad')
               .annotate(total=Count('id')).order_by('riesgo_enfermedad'))
    riesgo_dict = {r['riesgo_enfermedad']: r['total'] for r in riesgos}

    avg = Paciente.objects.aggregate(
        avg_edad=Avg('edad'),
        avg_imc=Avg('imc'),
        avg_glucosa=Avg('glucosa'),
        avg_colesterol=Avg('colesterol'),
    )

    return {
        'total_pacientes': total,
        'pacientes_criticos': criticos,
        'pct_criticos': round(criticos / total * 100, 1),
        'pacientes_hipertensos': hipertensos,
        'pct_hipertensos': round(hipertensos / total * 100, 1),
        'pacientes_diabeticos': diabeticos,
        'pct_diabeticos': round(diabeticos / total * 100, 1),
        'pacientes_fumadores': fumadores,
        'pct_fumadores': round(fumadores / total * 100, 1),
        'distribucion_riesgo': riesgo_dict,
        'promedios': {k: round(v, 2) if v else None for k, v in avg.items()},
    }


def segmentacion_por_edad() -> list:
    """Agrupa pacientes en rangos etarios."""
    qs = Paciente.objects.exclude(edad__isnull=True)
    df = pd.DataFrame(list(qs.values('edad', 'riesgo_enfermedad', 'sexo')))
    if df.empty:
        return []

    bins = [0, 18, 30, 45, 60, 75, 130]
    labels = ['0-18', '19-30', '31-45', '46-60', '61-75', '76+']
    df['rango_edad'] = pd.cut(df['edad'], bins=bins, labels=labels)

    resultado = (df.groupby('rango_edad', observed=True)
                 .size().reset_index(name='total'))
    return resultado.to_dict(orient='records')


def segmentacion_por_diagnostico() -> list:
    """Top 10 diagnósticos más frecuentes."""
    qs = (Paciente.objects.values('diagnostico_preliminar')
          .annotate(total=Count('id'))
          .order_by('-total')[:10])
    return list(qs)


def distribucion_imc() -> dict:
    """Distribución por clasificación IMC."""
    qs = (Paciente.objects.values('clasificacion_imc')
          .annotate(total=Count('id'))
          .order_by('-total'))
    return {r['clasificacion_imc']: r['total'] for r in qs if r['clasificacion_imc']}


def tendencia_consultas_mensual() -> list:
    """Número de consultas agrupadas por mes."""
    qs = Paciente.objects.exclude(fecha_consulta__isnull=True)
    df = pd.DataFrame(list(qs.values('fecha_consulta')))
    if df.empty:
        return []
    df['mes'] = pd.to_datetime(df['fecha_consulta']).dt.to_period('M').astype(str)
    resultado = df.groupby('mes').size().reset_index(name='total').sort_values('mes')
    return resultado.to_dict(orient='records')


def guardar_estadisticas_snapshot() -> EstadisticaClinica:
    """Persiste un snapshot de KPIs en BD."""
    kpis = obtener_kpis()
    rd = kpis.get('distribucion_riesgo', {})
    avg = kpis.get('promedios', {})
    snap = EstadisticaClinica.objects.create(
        total_pacientes=kpis.get('total_pacientes', 0),
        pacientes_criticos=kpis.get('pacientes_criticos', 0),
        pacientes_hipertensos=kpis.get('pacientes_hipertensos', 0),
        pacientes_diabeticos=kpis.get('pacientes_diabeticos', 0),
        pacientes_fumadores=kpis.get('pacientes_fumadores', 0),
        promedio_edad=avg.get('avg_edad'),
        promedio_imc=avg.get('avg_imc'),
        promedio_glucosa=avg.get('avg_glucosa'),
        promedio_colesterol=avg.get('avg_colesterol'),
        riesgo_bajo=rd.get('bajo', 0),
        riesgo_medio=rd.get('medio', 0),
        riesgo_alto=rd.get('alto', 0),
        riesgo_critico=rd.get('critico', 0),
    )
    return snap
