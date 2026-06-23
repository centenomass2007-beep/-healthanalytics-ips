"""Tests para autenticación JWT y roles."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Usuario


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            username='testadmin', password='Test1234!', email='a@test.com', rol='administrador'
        )
        self.medico = Usuario.objects.create_user(
            username='testmedico', password='Test1234!', email='m@test.com', rol='medico'
        )

    def _login(self, username='testadmin', password='Test1234!'):
        res = self.client.post('/api/auth/login/', {'username': username, 'password': password})
        return res.data.get('access')

    def test_login_exitoso(self):
        res = self.client.post('/api/auth/login/',
                               {'username': 'testadmin', 'password': 'Test1234!'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        # El rol está en el JWT payload, no en el response body
        self.assertIn('access', res.data)

    def test_login_credenciales_invalidas(self):
        res = self.client.post('/api/auth/login/',
                               {'username': 'testadmin', 'password': 'wrong'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_perfil_autenticado(self):
        token = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/auth/perfil/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'testadmin')

    def test_perfil_sin_token(self):
        res = self.client.get('/api/auth/perfil/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_roles_modelo(self):
        self.assertEqual(self.admin.rol, 'administrador')
        self.assertEqual(self.medico.rol, 'medico')

    def test_refresh_token(self):
        res = self.client.post('/api/auth/login/',
                               {'username': 'testadmin', 'password': 'Test1234!'})
        refresh = res.data['refresh']
        res2 = self.client.post('/api/auth/refresh/', {'refresh': refresh})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertIn('access', res2.data)
