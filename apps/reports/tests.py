"""Tests para exportación de reportes."""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import Usuario
from apps.etl.models import Paciente


def _paciente(i):
    return Paciente(id_paciente=i, nombres=f'N{i}', apellidos=f'A{i}',
                    edad=30+i, sexo='M', glucosa=100.0, colesterol=200.0,
                    riesgo_enfermedad='bajo', es_critico=False)


class ReportesAPITestCase(TestCase):
    def setUp(self):
        Paciente.objects.bulk_create([_paciente(i) for i in range(1, 11)])
        self.client = APIClient()
        u = Usuario.objects.create_superuser(
            username='rep', password='Test1234!', email='r@t.com', rol='analista')
        res = self.client.post('/api/auth/login/', {'username': 'rep', 'password': 'Test1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_exportar_csv(self):
        res = self.client.get('/api/reportes/csv/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', res['Content-Type'])
        content = res.content.decode('utf-8-sig')
        self.assertIn('id_paciente', content)
        self.assertIn('nombres', content)

    def test_exportar_excel(self):
        res = self.client.get('/api/reportes/excel/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', res['Content-Type'])
        self.assertGreater(len(res.content), 1000)

    def test_exportar_pdf(self):
        res = self.client.get('/api/reportes/pdf/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', res['Content-Type'])
        self.assertGreater(len(res.content), 1000)

    def test_exportar_sin_auth(self):
        self.client.credentials()
        self.assertEqual(self.client.get('/api/reportes/csv/').status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/excel/').status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/pdf/').status_code,
                         status.HTTP_401_UNAUTHORIZED)
