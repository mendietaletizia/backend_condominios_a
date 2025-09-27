from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from economia.models import Gastos, Multa
# from finanzas.models import Pago, Expensa  # Comentado temporalmente
from economia.serializers.economia_serializer import GastosSerializer, MultaSerializer
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
    
    def get_queryset(self):
        """Filtrar multas por estado y residente"""
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado', None)
        residente_id = self.request.query_params.get('residente_id', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if residente_id:
            queryset = queryset.filter(residente_id=residente_id)
        
        return queryset.order_by('-fecha_emision')
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener multas pendientes de pago"""
        multas_pendientes = self.get_queryset().filter(estado='pendiente')
        serializer = self.get_serializer(multas_pendientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Obtener multas vencidas"""
        from django.utils import timezone
        hoy = timezone.now().date()
        multas_vencidas = self.get_queryset().filter(
            estado='pendiente',
            fecha_vencimiento__lt=hoy
        )
        serializer = self.get_serializer(multas_vencidas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marcar_pagada(self, request, pk=None):
        """Marcar una multa como pagada"""
        multa = self.get_object()
        if multa.estado == 'pagada':
            return Response(
                {'error': 'La multa ya está marcada como pagada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        multa.estado = 'pagada'
        multa.save()
        
        # Crear notificación de pago
        from comunidad.services import NotificacionService
        NotificacionService.crear_notificacion_multa(multa)
        
        serializer = self.get_serializer(multa)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_reglamento(self, request):
        """Obtener multas por artículo de reglamento"""
        reglamento_id = request.query_params.get('reglamento_id')
        if not reglamento_id:
            return Response(
                {'error': 'Parámetro reglamento_id es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        multas = self.get_queryset().filter(reglamento_id=reglamento_id)
        serializer = self.get_serializer(multas, many=True)
        return Response(serializer.data)

# CU19: Reportes y analítica
class ReporteViewSet(viewsets.ViewSet):
    permission_classes = [RolPermiso]

    @action(detail=False, methods=['get'])
    def resumen_financiero(self, request):
        # Comentado temporalmente - CU7 eliminado
        # total_pagos = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0
        # total_expensas = Expensa.objects.aggregate(total=Sum('monto'))['total'] or 0
        total_gastos = Gastos.objects.aggregate(total=Sum('monto'))['total'] or 0
        total_multas = Multa.objects.aggregate(total=Sum('monto'))['total'] or 0
        return Response({
            "total_pagos": 0,  # CU7 eliminado
            "total_expensas": 0,  # Temporal
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
        Comentado temporalmente hasta que finanzas esté configurado.
        """
        import datetime
        
        hoy = datetime.date.today()
        
        # Comentado temporalmente hasta que finanzas esté configurado
        return Response({
            'residentes_morosos': [],
            'estadisticas': {
                'total_morosidad': 0,
                'cantidad_morosos': 0,
                'fecha_analisis': hoy,
                'mensaje': 'Funcionalidad temporalmente deshabilitada hasta configuración completa de finanzas'
            }
        })
    
    @action(detail=False, methods=['get'])
    def tendencias_pagos(self, request):
        """Análisis de tendencias de pagos por mes - CU7 eliminado"""
        import datetime
        
        # CU7 eliminado - solo CU22 (pagos de cuotas) disponible
        return Response({
            'tendencias_mensuales': [],
            'periodo_analisis': 'Últimos 12 meses',
            'mensaje': 'CU7 eliminado. Solo disponible CU22 - Gestión de Cuotas y Expensas'
        })
