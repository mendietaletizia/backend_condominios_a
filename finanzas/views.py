from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from finanzas.models import Expensa, Pago
from finanzas.serializers.finanzas_serializer import ExpensaSerializer, PagoSerializer
from usuarios.models import Empleado

class RolPermiso(permissions.BasePermission):
    """
    Solo administradores pueden crear/modificar ingresos.
    Otros roles solo pueden ver (GET).
    """
    def has_permission(self, request, view):
        user = getattr(request.user, 'usuario', None)
        if not user:
            return False
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        # Solo permitir GET para otros roles
        return request.method in permissions.SAFE_METHODS

class ExpensaViewSet(viewsets.ModelViewSet):
    queryset = Expensa.objects.all()
    serializer_class = ExpensaSerializer
    permission_classes = [RolPermiso]

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [RolPermiso]
