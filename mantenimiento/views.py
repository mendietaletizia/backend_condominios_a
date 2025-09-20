from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from mantenimiento.models import AreaComun, Reserva
from mantenimiento.serializers.mantenimiento_serializer import AreaComunSerializer, ReservaSerializer
from usuarios.models import Empleado

class RolPermiso(permissions.BasePermission):
    """
    Solo Administrador puede crear/editar áreas.
    Residente puede crear reservas pero no modificar áreas.
    """
    def has_permission(self, request, view):
        user = getattr(request.user, 'usuario', None)
        if not user:
            return False
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        # Para reservas, permitimos POST y GET a residentes
        if view.basename == 'reserva':
            return request.method in ['GET', 'POST']
        # Solo lectura para otros
        return request.method in permissions.SAFE_METHODS

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
        user = getattr(self.request.user, 'usuario', None)
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Reserva.objects.all()
        return Reserva.objects.filter(residente__usuario=user)
