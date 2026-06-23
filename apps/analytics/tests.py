"""Tests para el módulo de analítica de datos."""
import pandas as pd
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import Usuario
from apps.etl.models import Paciente
from .services import (
    obtener_kpis, obtener_estadisticas_descriptivas,
    segmentacion_por_edad, distribucion_imc,
)


def _poblar_pacientes(n=60):
    """Inserta pacientes de prueba directamente en BD."""
    import random
    random.seed(42)
    riesgos   = ['bajo', 'medio', 'alto', 'critico']
    sexos     = ['M', 'F']
    imcs      = ['bajo_peso', 'normal', 'sobrepeso', 'obesidad']
    pacientes = []
    for i in range(1, n + 1):
        pacientes.append(Paciente(
            id_paciente=i,
            nombres=f'Paciente{i}', apellidos=f'Apellido{i}',
            edad=random.randint(20, 75),
            sexo=random.choice(sexos),
            peso=random.uniform(55, 100),
            altura=random.uniform(1.55, 1.85),
            imc=random.uniform(18, 35),
            clasificacion_imc=random.choice(imcs),
            presion_sistolica=random.randint(100, 180),
            presion_diastolica=random.randint(60, 100),
            frecuencia_cardiaca=random.randint(60, 95),
            glucosa=random.uniform(70, 280),
            colesterol=random.uniform(150, 280),
            saturacion_oxigeno=random.uniform(88, 99),
            temperatura=random.uniform(36.0, 37.9),
            antecedentes_familiares=random.choice([True, False]),
            fumador=random.choice([True, False]),
            consumo_alcohol=random.choice([True, False]),
            riesgo_enfermedad=random.choice(riesgos),
            diagnostico_preliminar=random.choice(['Hipertensión', 'Diabetes', 'Paciente Sano']),
            es_critico=(i % 10 == 0),
        ))
    Paciente.objects.bulk_create(pacientes)


class KPIsTestCase(TestCase):
    def setUp(self):
        _poblar_pacientes(60)

    def test_kpis_total_correcto(self):
        kpis = obtener_kpis()
        self.assertEqual(kpis['total_pacientes'], 60)

    def test_kpis_tiene_campos_requeridos(self):
        kpis = obtener_kpis()
        campos = ['total_pacientes', 'pacientes_criticos', 'pacientes_hipertensos',
                  'pacientes_diabeticos', 'pacientes_fumadores', 'distribucion_riesgo']
        for campo in campos:
            self.assertIn(campo, kpis, f"KPI '{campo}' faltante")

    def test_kpis_porcentajes_rango(self):
        kpis = obtener_kpis()
        for pct in ['pct_criticos', 'pct_hipertensos', 'pct_diabeticos', 'pct_fumadores']:
            self.assertGreaterEqual(kpis[pct], 0)
            self.assertLessEqual(kpis[pct], 100)

    def test_kpis_sin_pacientes(self):
        Paciente.objects.all().delete()
        kpis = obtener_kpis()
        self.assertEqual(kpis.get('total', kpis.get('total_pacientes', 0)), 0)

    def test_estadisticas_descriptivas(self):
        stats = obtener_estadisticas_descriptivas()
        self.assertIn('edad', stats)
        for metrica in ['media', 'mediana', 'desviacion_std', 'min', 'max']:
            self.assertIn(metrica, stats['edad'])

    def test_segmentacion_edad(self):
        seg = segmentacion_por_edad()
        self.assertIsInstance(seg, list)
        if seg:
            self.assertIn('rango_edad', seg[0])
            self.assertIn('total', seg[0])

    def test_distribucion_imc(self):
        dist = distribucion_imc()
        self.assertIsInstance(dist, dict)
        claves_validas = {'bajo_peso', 'normal', 'sobrepeso', 'obesidad'}
        for k in dist:
            self.assertIn(k, claves_validas)


class AnalyticsAPITestCase(TestCase):
    def setUp(self):
        _poblar_pacientes(30)
        self.client = APIClient()
        self.user = Usuario.objects.create_superuser(
            username='analista', password='Test1234!', email='a@t.com', rol='analista'
        )
        res = self.client.post('/api/auth/login/',
                               {'username': 'analista', 'password': 'Test1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_api_kpis(self):
        res = self.client.get('/api/analytics/kpis/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_pacientes', res.data)

    def test_api_estadisticas(self):
        res = self.client.get('/api/analytics/estadisticas/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_api_segmentacion(self):
        res = self.client.get('/api/analytics/segmentacion/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('por_edad', res.data)
        self.assertIn('por_imc', res.data)

    def test_api_tendencias(self):
        res = self.client.get('/api/analytics/tendencias/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
