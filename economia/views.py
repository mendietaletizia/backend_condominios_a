from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from economia.models import Gastos, Multa
from finanzas.models import Pago, Expensa
from economia.serializers.economia_serializer import GastosSerializer, MultaSerializer, PagoSerializer, ExpensaSerializer
from usuarios.models import Empleado
from django.db.models import Sum, Count

class RolPermiso(permissions.BasePermission):
    """
    Solo administradores pueden crear/editar. Otros roles solo GET.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Permitir si es superusuario o tiene rol de administrador
        if getattr(request.user, "is_superuser", False):
            return True
        if hasattr(request.user, "rol") and request.user.rol and request.user.rol.nombre.lower() == "administrador":
            return True
        # Lógica para otros roles
        if hasattr(request.user, "rol") and request.user.rol:
            rol = request.user.rol.nombre.lower()
            if rol == "residente":
                # Solo lectura para residentes
                return request.method in permissions.SAFE_METHODS
            if rol == "empleado":
                # Personaliza aquí los permisos de empleado si lo necesitas
                return request.method in permissions.SAFE_METHODS
        # Lógica anterior para empleados (por compatibilidad)
        empleado = Empleado.objects.filter(usuario=request.user).first()
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
        from django.db.models import Sum, Count
        from usuarios.models import Residentes
        
        hoy = datetime.date.today()
        
        # Obtener residentes con pagos vencidos
        residentes_morosos = Residentes.objects.filter(
            pago__fecha_vencimiento__lt=hoy,
            pago__estado_pago='pendiente'
        ).annotate(
            total_moroso=Sum('pago__monto'),
            cantidad_pagos_vencidos=Count('pago')
        ).values('id', 'persona__nombre', 'total_moroso', 'cantidad_pagos_vencidos')
        
        # Calcular estadísticas generales
        total_morosidad = sum(r['total_moroso'] or 0 for r in residentes_morosos)
        cantidad_morosos = len(residentes_morosos)
        
        return Response({
            'residentes_morosos': list(residentes_morosos),
            'estadisticas': {
                'total_morosidad': total_morosidad,
                'cantidad_morosos': cantidad_morosos,
                'fecha_analisis': hoy
            }
        })
    
    @action(detail=False, methods=['get'])
    def tendencias_pagos(self, request):
        """Análisis de tendencias de pagos por mes"""
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        import datetime
        
        # Pagos por mes del último año
        pagos_por_mes = Pago.objects.filter(
            fecha_pago__gte=datetime.date.today() - datetime.timedelta(days=365)
        ).annotate(
            mes=TruncMonth('fecha_pago')
        ).values('mes').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('mes')
        
        return Response({
            'tendencias_mensuales': list(pagos_por_mes),
            'periodo_analisis': 'Últimos 12 meses'
        })
