from django.test import TestCase
from .models import Unidad, Evento, Reserva, Notificacion
from usuarios.models import Persona, Residentes, User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ComunidadModelTest(TestCase):
    """Tests para los modelos de comunidad"""

    def setUp(self):
        self.persona = Persona.objects.create(
            nombre='Test Persona',
            ci='123456789'
        )

        self.usuario = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.residente = Residentes.objects.create(
            persona=self.persona,
            usuario=self.usuario
        )

    def test_crear_unidad(self):
        """Test para crear una unidad"""
        unidad = Unidad.objects.create(
            numero='101',
            piso='1',
            torre='A',
            area=85.5,
            residente=self.residente
        )

        self.assertEqual(unidad.numero, '101')
        self.assertEqual(unidad.piso, '1')
        self.assertEqual(unidad.torre, 'A')
        self.assertEqual(unidad.area, 85.5)
        self.assertEqual(unidad.residente, self.residente)

    def test_crear_evento(self):
        """Test para crear un evento"""
        evento = Evento.objects.create(
            titulo='Reunión de Condóminos',
            descripcion='Reunión mensual para discutir temas del edificio',
            fecha='2024-12-25',
            hora='19:00',
            lugar='Salón Comunal',
            organizador=self.usuario
        )

        self.assertEqual(evento.titulo, 'Reunión de Condóminos')
        self.assertEqual(evento.lugar, 'Salón Comunal')
        self.assertEqual(evento.organizador, self.usuario)

    def test_crear_reserva(self):
        """Test para crear una reserva"""
        reserva = Reserva.objects.create(
            titulo='Reserva Salón',
            descripcion='Reserva del salón para cumpleaños',
            fecha='2024-12-20',
            hora_inicio='14:00',
            hora_fin='18:00',
            residente=self.residente,
            estado='pendiente'
        )

        self.assertEqual(reserva.titulo, 'Reserva Salón')
        self.assertEqual(reserva.estado, 'pendiente')
        self.assertEqual(reserva.residente, self.residente)

    def test_crear_notificacion(self):
        """Test para crear una notificación"""
        notificacion = Notificacion.objects.create(
            titulo='Mantenimiento Programado',
            mensaje='Se realizará mantenimiento del ascensor el día 25/12',
            tipo='mantenimiento',
            usuario=self.usuario
        )

        self.assertEqual(notificacion.titulo, 'Mantenimiento Programado')
        self.assertEqual(notificacion.tipo, 'mantenimiento')
        self.assertEqual(notificacion.usuario, self.usuario)

class ComunidadAPITest(APITestCase):
    """Tests para las APIs de comunidad"""

    def setUp(self):
        self.persona = Persona.objects.create(
            nombre='API Test Persona',
            ci='987654321'
        )

        self.usuario = User.objects.create_user(
            username='apitest',
            password='testpass123'
        )

        self.residente = Residentes.objects.create(
            persona=self.persona,
            usuario=self.usuario
        )

    def test_obtener_unidades(self):
        """Test para obtener lista de unidades"""
        url = reverse('unidad-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_unidad_api(self):
        """Test para crear unidad vía API"""
        url = reverse('unidad-list')
        data = {
            'numero': '201',
            'piso': '2',
            'torre': 'B',
            'area': 90.0,
            'residente_id': self.residente.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['numero'], '201')
        self.assertEqual(response.data['torre'], 'B')

    def test_obtener_eventos(self):
        """Test para obtener lista de eventos"""
        url = reverse('evento-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
