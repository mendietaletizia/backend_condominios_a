from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, Acta
from comunidad.serializers.comunidad_serializer import (
    UnidadSerializer, ResidentesUnidadSerializer,
    EventoSerializer, NotificacionSerializer,
    NotificacionResidenteSerializer, ActaSerializer
)
from usuarios.models import Empleado

class RolPermiso(permissions.BasePermission):
    """Solo Admin puede modificar; otros roles pueden ver"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        # Para vistas que solo consultan, permitimos GET
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

# CU6: Unidades
class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    permission_classes = [RolPermiso]

class ResidentesUnidadViewSet(viewsets.ModelViewSet):
    queryset = ResidentesUnidad.objects.all()
    serializer_class = ResidentesUnidadSerializer
    permission_classes = [RolPermiso]

# CU11: Eventos
class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [RolPermiso]

# CU12: Comunicados / Noticias
class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [RolPermiso]

class NotificacionResidenteViewSet(viewsets.ModelViewSet):
    queryset = NotificacionResidente.objects.all()
    serializer_class = NotificacionResidenteSerializer
    permission_classes = [permissions.IsAuthenticated]  # Todos los usuarios pueden ver sus notificaciones
    
    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return NotificacionResidente.objects.none()
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return NotificacionResidente.objects.all()
        # Residentes solo ven sus propias notificaciones
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return NotificacionResidente.objects.filter(residente=residente)
        return NotificacionResidente.objects.none()

# CU17: Actas
class ActaViewSet(viewsets.ModelViewSet):
    queryset = Acta.objects.all()
    serializer_class = ActaSerializer
    permission_classes = [RolPermiso]
