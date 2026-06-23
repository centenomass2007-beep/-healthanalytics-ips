"""Tests para el módulo de Machine Learning."""
import random
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import Usuario
from apps.etl.models import Paciente
from .services import entrenar_modelo, predecir_paciente
from .models import ModeloML, PrediccionPaciente


def _poblar_pacientes_ml(n=120):
    """Pacientes con suficiente variedad para entrenar un modelo."""
    random.seed(99)
    riesgos = ['bajo', 'medio', 'alto', 'critico']
    pacs = []
    for i in range(1, n + 1):
        pacs.append(Paciente(
            id_paciente=i,
            nombres=f'P{i}', apellidos=f'A{i}',
            edad=random.randint(20, 80),
            sexo=random.choice(['M', 'F']),
            peso=random.uniform(50, 110),
            altura=random.uniform(1.55, 1.85),
            imc=random.uniform(17, 38),
            presion_sistolica=random.randint(90, 190),
            presion_diastolica=random.randint(55, 110),
            frecuencia_cardiaca=random.randint(55, 100),
            glucosa=random.uniform(60, 320),
            colesterol=random.uniform(140, 300),
            saturacion_oxigeno=random.uniform(85, 99),
            temperatura=random.uniform(36.0, 38.5),
            antecedentes_familiares=random.choice([True, False]),
            fumador=random.choice([True, False]),
            consumo_alcohol=random.choice([True, False]),
            riesgo_enfermedad=riesgos[i % 4],
            es_critico=(i % 15 == 0),
        ))
    Paciente.objects.bulk_create(pacs)


class ModeloMLTestCase(TestCase):
    def setUp(self):
        _poblar_pacientes_ml(120)

    def test_entrenamiento_random_forest(self):
        modelo, metricas = entrenar_modelo('random_forest')
        self.assertIsNotNone(modelo.id)
        self.assertEqual(modelo.algoritmo, 'random_forest')
        self.assertTrue(modelo.activo)
        self.assertGreater(modelo.accuracy, 0)
        self.assertLessEqual(modelo.accuracy, 1)

    def test_entrenamiento_regresion_logistica(self):
        modelo, metricas = entrenar_modelo('logistic_regression')
        self.assertEqual(modelo.algoritmo, 'logistic_regression')
        self.assertIsNotNone(modelo.accuracy)

    def test_entrenamiento_arbol_decision(self):
        modelo, metricas = entrenar_modelo('decision_tree')
        self.assertEqual(modelo.algoritmo, 'decision_tree')

    def test_metricas_completas(self):
        _, metricas = entrenar_modelo('random_forest')
        for m in ['accuracy', 'precision', 'recall', 'f1_score', 'confusion_matrix']:
            self.assertIn(m, metricas, f"Métrica '{m}' faltante")

    def test_accuracy_razonable(self):
        _, metricas = entrenar_modelo('random_forest')
        self.assertGreater(metricas['accuracy'], 0.3,
                           "Accuracy demasiado bajo, revisar datos de entrenamiento")

    def test_solo_un_modelo_activo_por_algoritmo(self):
        entrenar_modelo('random_forest')
        entrenar_modelo('random_forest')
        activos = ModeloML.objects.filter(algoritmo='random_forest', activo=True).count()
        self.assertEqual(activos, 1)

    def test_algoritmo_invalido(self):
        with self.assertRaises(ValueError):
            entrenar_modelo('algoritmo_que_no_existe')

    def test_prediccion_paciente(self):
        resultado = predecir_paciente(1)
        self.assertIn('riesgo_predicho', resultado)
        self.assertIn('probabilidad', resultado)
        self.assertIn(resultado['riesgo_predicho'],
                      ['bajo', 'medio', 'alto', 'critico'])
        self.assertGreaterEqual(resultado['probabilidad'], 0)
        self.assertLessEqual(resultado['probabilidad'], 1)

    def test_prediccion_guarda_en_bd(self):
        antes = PrediccionPaciente.objects.count()
        predecir_paciente(1)
        self.assertGreater(PrediccionPaciente.objects.count(), antes)

    def test_dataset_insuficiente(self):
        Paciente.objects.all().delete()
        with self.assertRaises(ValueError):
            entrenar_modelo('random_forest')


class MLAPITestCase(TestCase):
    def setUp(self):
        _poblar_pacientes_ml(120)
        self.client = APIClient()
        self.user = Usuario.objects.create_superuser(
            username='mluser', password='Test1234!', email='ml@t.com', rol='analista'
        )
        res = self.client.post('/api/auth/login/',
                               {'username': 'mluser', 'password': 'Test1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_api_entrenar(self):
        res = self.client.post('/api/ml/entrenar/',
                               {'algoritmo': 'random_forest'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('metricas', res.data)
        self.assertIn('accuracy', res.data['metricas'])

    def test_api_predecir(self):
        self.client.post('/api/ml/entrenar/',
                         {'algoritmo': 'random_forest'}, format='json')
        res = self.client.post('/api/ml/predecir/',
                               {'paciente_id': 1}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('riesgo_predicho', res.data)

    def test_api_predecir_sin_id(self):
        res = self.client.post('/api/ml/predecir/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_modelos_lista(self):
        res = self.client.get('/api/ml/modelos/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)
