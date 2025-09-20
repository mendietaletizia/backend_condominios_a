from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from economia.models import Gastos, Multa
from finanzas.models import Pago, Expensa
from economia.serializers.economia_serializer import GastosSerializer, MultaSerializer, PagoSerializer, ExpensaSerializer
from usuarios.models import Empleado
from django.db.models import Sum

class RolPermiso(permissions.BasePermission):
    """
    Solo administradores pueden crear/editar. Otros roles solo GET.
    """
    def has_permission(self, request, view):
        user = getattr(request.user, 'usuario', None)
        if not user:
            return False
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        return request.method in permissions.SAFE_METHODS

# CU8: Gastos
class GastosViewSet(viewsets.ModelViewSet):
    queryset = Gastos.objects.all()
    serializer_class = GastosSerializer
    permission_classes = [RolPermiso]

# CU9: Multas
class MultaViewSet(viewsets.ModelViewSet):
    queryset = Multa.objects.all()
    serializer_class = MultaSerializer
    permission_classes = [RolPermiso]

# CU19: Reportes y analítica
class ReporteViewSet(viewsets.ViewSet):
    permission_classes = [RolPermiso]

    @action(detail=False, methods=['get'])
    def resumen_financiero(self, request):
        total_pagos = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0
        total_expensas = Expensa.objects.aggregate(total=Sum('monto'))['total'] or 0
        total_gastos = Gastos.objects.aggregate(total=Sum('monto'))['total'] or 0
        total_multas = Multa.objects.aggregate(total=Sum('monto'))['total'] or 0
        return Response({
            "total_pagos": total_pagos,
            "total_expensas": total_expensas,
            "total_gastos": total_gastos,
            "total_multas": total_multas
        })

# CU20: Analítica predictiva de morosidad
class MorosidadViewSet(viewsets.ViewSet):
    permission_classes = [RolPermiso]

    @action(detail=False, methods=['get'])
    def predecir_morosidad(self, request):
        """
        Retorna morosidad estimada por residente basado en pagos atrasados.
        Simple aproximación: si fecha_vencimiento < hoy y estado pago pendiente
        """
        import datetime
        hoy = datetime.date.today()
        morosidad = {}
        pagos = Pago.objects.all()
        for pago in pagos:
            if pago.fecha_vencimiento < hoy and pago.monto > 0:
                r_id = pago.residente.id
                morosidad[r_id] = morosidad.get(r_id, 0) + pago.monto
        return Response(morosidad)
