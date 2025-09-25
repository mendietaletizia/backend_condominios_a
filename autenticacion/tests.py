from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import CustomToken

User = get_user_model()

class AutenticacionTest(APITestCase):
    """Tests para la autenticación"""

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='testauth',
            email='auth@example.com',
            password='testpass123'
        )

    def test_login_exitoso(self):
        """Test para login exitoso"""
        url = reverse('login')
        data = {
            'username': 'testauth',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'testauth')

    def test_login_fallido(self):
        """Test para login fallido"""
        url = reverse('login')
        data = {
            'username': 'testauth',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_logout(self):
        """Test para logout"""
        # Primero hacer login
        login_url = reverse('login')
        login_data = {
            'username': 'testauth',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['token']

        # Luego hacer logout
        logout_url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post(logout_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Sesión cerrada exitosamente')

class CustomTokenTest(TestCase):
    """Tests para el modelo CustomToken"""

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='tokentest',
            password='testpass123'
        )

    def test_crear_token_personalizado(self):
        """Test para crear un token personalizado"""
        token = CustomToken.objects.create(user=self.usuario)

        self.assertIsNotNone(token.key)
        self.assertEqual(token.user, self.usuario)
        self.assertIsNotNone(token.created)
