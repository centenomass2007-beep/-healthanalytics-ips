"""Tests para el motor ETL: extracción, transformación y carga."""
import os, tempfile, pandas as pd
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import Usuario
from .etl_engine import extract, transform, load, ejecutar_etl
from .models import Paciente, HistorialETL


def _crear_dataset_prueba(n=50):
    """Genera un DataFrame de prueba con errores intencionales."""
    import numpy as np
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        'id_paciente':        range(1, n + 1),
        'nombres':            [f'Nombre{i}' for i in range(n)],
        'apellidos':          [f'Apellido{i}' for i in range(n)],
        'edad':               [int(x) for x in rng.integers(18, 80, n)],
        'sexo':               rng.choice(['masculino', 'femenino', 'M', 'F', None], n).tolist(),
        'peso':               rng.uniform(50, 120, n).tolist(),
        'altura':             rng.uniform(1.5, 1.9, n).tolist(),
        'IMC':                [None] * n,
        'presión_sistólica':  rng.integers(100, 160, n).tolist(),
        'presión_diastólica': rng.integers(60, 100, n).tolist(),
        'frecuencia_cardiaca': rng.integers(60, 100, n).tolist(),
        'glucosa':            rng.uniform(70, 200, n).tolist(),
        'colesterol':         rng.uniform(150, 280, n).tolist(),
        'saturación_oxígeno': rng.uniform(92, 99, n).tolist(),
        'temperatura':        rng.uniform(36.0, 37.8, n).tolist(),
        'antecedentes_familiares': rng.choice([True, False], n).tolist(),
        'fumador':            rng.choice([True, False], n).tolist(),
        'consumo_alcohol':    rng.choice([True, False], n).tolist(),
        'actividad_física':   rng.choice(['sedentario', 'baja', 'media', 'alta'], n).tolist(),
        'diagnóstico_preliminar': rng.choice(['hipertensión', 'diabetes', 'paciente sano'], n).tolist(),
        'riesgo_enfermedad':  rng.choice(['bajo', 'medio', 'alto', 'critico'], n).tolist(),
        'fecha_consulta':     pd.date_range('2024-01-01', periods=n, freq='D').tolist(),
    })
    # Convertir edad a object para permitir valor string
    df['edad'] = df['edad'].astype(object)
    # Introducir errores intencionales
    df.loc[0, 'glucosa']   = None
    df.loc[1, 'peso']      = None
    df.loc[2, 'edad']      = 'Treinta'     # tipo incorrecto
    df.loc[3, 'peso']      = 420           # atípico
    df.loc[4, 'temperatura'] = 28          # atípico
    # Duplicado intencional
    df = pd.concat([df, df.iloc[[5]]], ignore_index=True)
    return df


class ETLExtractTestCase(TestCase):
    def test_extract_excel(self):
        df = _crear_dataset_prueba(20)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False)
            df_out, meta = extract(f.name)
        os.unlink(f.name)
        self.assertEqual(meta['registros_entrada'], 21)  # 20 + 1 dup
        self.assertGreater(len(df_out), 0)

    def test_extract_csv(self):
        df = _crear_dataset_prueba(15)
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as f:
            df.to_csv(f.name, index=False)
            df_out, meta = extract(f.name)
        os.unlink(f.name)
        self.assertEqual(meta['registros_entrada'], 16)


class ETLTransformTestCase(TestCase):
    def setUp(self):
        self.df_raw = _crear_dataset_prueba(50)

    def test_elimina_duplicados(self):
        df_clean, meta = transform(self.df_raw)
        self.assertGreaterEqual(meta['duplicados_eliminados'], 1)

    def test_calcula_imc(self):
        df_clean, _ = transform(self.df_raw)
        self.assertIn('imc', df_clean.columns)
        self.assertIn('clasificacion_imc', df_clean.columns)
        # IMC debe ser valor positivo razonable
        validos = df_clean['imc'].dropna()
        self.assertTrue((validos > 10).all())
        self.assertTrue((validos < 80).all())

    def test_detecta_criticos(self):
        df = self.df_raw.copy()
        # Añadir un paciente crítico explícito
        df.loc[0, 'presión_sistólica'] = 200
        df_clean, _ = transform(df)
        self.assertTrue(df_clean['es_critico'].any())

    def test_trata_nulos(self):
        df_clean, meta = transform(self.df_raw)
        # Columnas críticas no deben tener NaN
        for col in ['imc', 'glucosa']:
            if col in df_clean.columns:
                self.assertFalse(df_clean[col].isna().all(),
                                 f"Columna {col} no debería ser todo NaN")

    def test_normaliza_sexo(self):
        df_clean, _ = transform(self.df_raw)
        if 'sexo' in df_clean.columns:
            validos = {'M', 'F', 'O'}
            valores = set(df_clean['sexo'].dropna().unique())
            self.assertTrue(valores.issubset(validos),
                            f"Valores inesperados en sexo: {valores - validos}")

    def test_valores_atipicos_eliminados(self):
        df_clean, _ = transform(self.df_raw)
        if 'peso' in df_clean.columns:
            self.assertTrue((df_clean['peso'].dropna() <= 300).all())


class ETLLoadTestCase(TestCase):
    def test_carga_en_bd(self):
        df_raw  = _crear_dataset_prueba(30)
        df_clean, _ = transform(df_raw)
        logs = []
        n = load(df_clean, logs)
        self.assertEqual(Paciente.objects.count(), n)
        self.assertGreater(n, 0)


class ETLOrquestadorTestCase(TestCase):
    def test_ejecutar_etl_completo(self):
        df = _crear_dataset_prueba(40)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False)
            h = ejecutar_etl(f.name)
        os.unlink(f.name)
        self.assertEqual(h.estado, 'completado')
        self.assertGreater(h.registros_limpios, 0)
        self.assertGreater(h.tiempo_ejecucion_seg, 0)
        self.assertIn('[ETL] Proceso completado', h.log_detalle)

    def test_etl_archivo_invalido(self):
        h = ejecutar_etl('/ruta/que/no/existe.xlsx')
        self.assertEqual(h.estado, 'error')
        self.assertNotEqual(h.errores, '')


class ETLAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_superuser(
            username='etluser', password='Test1234!', email='e@test.com', rol='analista'
        )
        res = self.client.post('/api/auth/login/',
                               {'username': 'etluser', 'password': 'Test1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_historial_etl_vacio(self):
        res = self.client.get('/api/etl/historial/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_pacientes_requiere_auth(self):
        self.client.credentials()
        res = self.client.get('/api/pacientes/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
