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
        if not request.user or not request.user.is_authenticated:
            return False
        empleado = Empleado.objects.filter(usuario=request.user).first()
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
    
    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return Pago.objects.none()
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Pago.objects.all()
        # Residentes solo ven sus propios pagos
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Pago.objects.filter(residente=residente)
        return Pago.objects.none()