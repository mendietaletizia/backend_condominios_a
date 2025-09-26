from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from mantenimiento.models import AreaComun, Reserva, Mantenimiento, BitacoraMantenimiento, Reglamento
from mantenimiento.serializers.mantenimiento_serializer import (
    AreaComunSerializer, ReservaSerializer, MantenimientoSerializer,
    BitacoraMantenimientoSerializer, ReglamentoSerializer
)
from usuarios.models import Empleado
from comunidad.models import Evento
from datetime import datetime
from django.utils import timezone

class RolPermiso(permissions.BasePermission):
    """
    Solo Administrador puede crear/editar áreas.
    Residente puede crear reservas pero no modificar áreas.
    """
    def has_permission(self, request, view):
        # Permitir lectura pública (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # Administrador por empleado
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        # Administrador por rol de usuario
        if hasattr(request.user, 'rol') and request.user.rol and request.user.rol.nombre.lower() == 'administrador':
            return True
        # Para reservas, permitimos POST y GET a residentes
        if view.basename == 'reserva':
            return request.method in ['GET', 'POST']
        # Solo lectura para otros (ya cubierto arriba); bloquear escritura
        return False

# Áreas comunes
class AreaComunViewSet(viewsets.ModelViewSet):
    queryset = AreaComun.objects.all()
    serializer_class = AreaComunSerializer
    permission_classes = [RolPermiso]

# Reservas
class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [RolPermiso]

    def get_queryset(self):
        # Residente solo ve sus reservas, admin ve todas
        if not self.request.user or not self.request.user.is_authenticated:
            return Reserva.objects.none()
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Reserva.objects.all()
        # Para residentes, necesitamos encontrar su relación con las reservas
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Reserva.objects.filter(residente=residente)
        return Reserva.objects.none()
    
    def perform_create(self, serializer):
        # Asignar automáticamente el residente al crear la reserva
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            serializer.save(residente=residente)
    
    @action(detail=False, methods=['get'])
    def disponibilidad(self, request):
        """Verificar disponibilidad de un área en una fecha y hora específica"""
        area_id = request.query_params.get('area_id')
        fecha = request.query_params.get('fecha')
        hora_inicio = request.query_params.get('hora_inicio')
        hora_fin = request.query_params.get('hora_fin')
        
        if not all([area_id, fecha, hora_inicio, hora_fin]):
            return Response({'error': 'Faltan parámetros requeridos'}, status=400)
        
        # Verificar si hay conflictos de horario
        reservas_conflicto = Reserva.objects.filter(
            area_id=area_id,
            fecha=fecha,
            estado__in=['pendiente', 'confirmada']
        ).filter(
            models.Q(hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio)
        )
        
        disponible = not reservas_conflicto.exists()
        
        return Response({
            'disponible': disponible,
            'conflictos': reservas_conflicto.count()
        })

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirmar una reserva y generar un evento en la agenda (CU11)."""
        reserva = self.get_object()
        reserva.estado = 'confirmada'
        reserva.save()

        # Crear evento asociado (sin FK directa, guardamos datos descriptivos)
        try:
            fecha_evento = datetime.combine(reserva.fecha, reserva.hora_inicio)
            if timezone.is_naive(fecha_evento):
                fecha_evento = timezone.make_aware(fecha_evento)
        except Exception:
            fecha_evento = timezone.now()

        titulo = f"Reserva confirmada - {reserva.area.nombre}"
        descripcion = f"Evento por reserva del área {reserva.area.nombre} de {reserva.hora_inicio} a {reserva.hora_fin}. Residente ID: {reserva.residente_id}."
        Evento.objects.create(titulo=titulo, descripcion=descripcion, fecha=fecha_evento, estado=True)

        return Response({'detail': 'Reserva confirmada y evento creado'}, status=200)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancelar una reserva (y no crear evento)."""
        reserva = self.get_object()
        reserva.estado = 'cancelada'
        reserva.save()
        return Response({'detail': 'Reserva cancelada'}, status=200)

# Vistas para los nuevos modelos
class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.all()
    serializer_class = MantenimientoSerializer
    permission_classes = [RolPermiso]

class BitacoraMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = BitacoraMantenimiento.objects.all()
    serializer_class = BitacoraMantenimientoSerializer
    permission_classes = [RolPermiso]

class ReglamentoViewSet(viewsets.ModelViewSet):
    queryset = Reglamento.objects.all()
    serializer_class = ReglamentoSerializer
    permission_classes = [RolPermiso]
