from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Persona, Residentes, Roles, Permiso, RolPermiso, Empleado
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario"""

    def setUp(self):
        self.rol = Roles.objects.create(nombre='Administrador')

    def test_crear_usuario(self):
        """Test para crear un usuario"""
        usuario = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        usuario.rol = self.rol
        usuario.save()

        self.assertEqual(usuario.username, 'testuser')
        self.assertEqual(usuario.email, 'test@example.com')
        self.assertEqual(usuario.rol.nombre, 'Administrador')
        self.assertTrue(usuario.check_password('testpass123'))

    def test_crear_persona(self):
        """Test para crear una persona"""
        persona = Persona.objects.create(
            ci='12345678',
            nombre='Juan Pérez',
            email='juan@example.com',
            telefono='555-1234'
        )

        self.assertEqual(persona.nombre, 'Juan Pérez')
        self.assertEqual(persona.ci, '12345678')
        self.assertEqual(persona.email, 'juan@example.com')

    def test_crear_residente(self):
        """Test para crear un residente"""
        persona = Persona.objects.create(
            ci='87654321',
            nombre='María García',
            email='maria@example.com'
        )

        usuario = User.objects.create_user(
            username='mariagarcia',
            password='testpass123'
        )

        residente = Residentes.objects.create(
            persona=persona,
            usuario=usuario
        )

        self.assertEqual(residente.persona.nombre, 'María García')
        self.assertEqual(residente.usuario.username, 'mariagarcia')

class UsuarioAPITest(APITestCase):
    """Tests para las APIs de usuarios"""

    def setUp(self):
        self.rol = Roles.objects.create(nombre='Usuario')
        self.usuario = User.objects.create_user(
            username='testapi',
            email='api@example.com',
            password='testpass123'
        )
        self.usuario.rol = self.rol
        self.usuario.save()

    def test_obtener_usuarios(self):
        """Test para obtener lista de usuarios"""
        url = reverse('usuario-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_crear_usuario_api(self):
        """Test para crear usuario vía API"""
        url = reverse('usuario-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'rol_id': self.rol.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'new@example.com')

class PersonaModelTest(TestCase):
    """Tests para el modelo Persona"""

    def test_persona_str(self):
        """Test para el método __str__ de Persona"""
        persona = Persona.objects.create(
            nombre='Test Persona',
            ci='123456789'
        )
        self.assertEqual(str(persona), 'Test Persona')

    def test_persona_campos_opcionales(self):
        """Test para campos opcionales en Persona"""
        persona = Persona.objects.create(
            nombre='Test Sin Email',
            ci='987654321'
        )
        self.assertIsNone(persona.email)
        self.assertIsNone(persona.telefono)

class RolesModelTest(TestCase):
    """Tests para el modelo Roles"""

    def test_crear_rol(self):
        """Test para crear un rol"""
        rol = Roles.objects.create(nombre='Moderador')
        self.assertEqual(rol.nombre, 'Moderador')

    def test_rol_str(self):
        """Test para el método __str__ de Roles"""
        rol = Roles.objects.create(nombre='Supervisor')
        self.assertEqual(str(rol), 'Supervisor')
