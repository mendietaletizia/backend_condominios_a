from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from economia.models import Gastos, Multa, ReporteFinanciero, AnalisisFinanciero, IndicadorFinanciero, DashboardFinanciero
# from finanzas.models import Pago, Expensa  # Comentado temporalmente
from economia.serializers.economia_serializer import (
    GastosSerializer, MultaSerializer, ReporteFinancieroSerializer, 
    AnalisisFinancieroSerializer, IndicadorFinancieroSerializer, 
    DashboardFinancieroSerializer, ResumenFinancieroSerializer,
    AnalisisMorosidadSerializer, ProyeccionFinancieraSerializer
)
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

# CU19: Reportes y Analítica
class ReporteFinancieroViewSet(viewsets.ModelViewSet):
    """Gestión de Reportes Financieros - CU19"""
    queryset = ReporteFinanciero.objects.all()
    serializer_class = ReporteFinancieroSerializer
    permission_classes = [RolPermiso]
    
    def perform_create(self, serializer):
        serializer.save(generado_por=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generar_reporte(self, request):
        """Generar un nuevo reporte financiero"""
        try:
            data = request.data
            reporte = ReporteFinanciero.objects.create(
                nombre=data.get('nombre', f"Reporte {data.get('tipo_reporte', 'personalizado')}"),
                tipo_reporte=data.get('tipo_reporte', 'personalizado'),
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data['fecha_fin'],
                generado_por=request.user,
                observaciones=data.get('observaciones', '')
            )
            
            # Calcular totales
            reporte.calcular_totales()
            
            serializer = self.get_serializer(reporte)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error generando reporte: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def regenerar_totales(self, request, pk=None):
        """Regenerar totales de un reporte existente"""
        try:
            reporte = self.get_object()
            reporte.calcular_totales()
            serializer = self.get_serializer(reporte)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Error regenerando totales: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class AnalisisFinancieroViewSet(viewsets.ModelViewSet):
    """Gestión de Análisis Financieros - CU19"""
    queryset = AnalisisFinanciero.objects.all()
    serializer_class = AnalisisFinancieroSerializer
    permission_classes = [RolPermiso]
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)
    
    @action(detail=False, methods=['post'])
    def analizar_tendencia(self, request):
        """Realizar análisis de tendencia financiera"""
        try:
            data = request.data
            periodo_inicio = data['periodo_inicio']
            periodo_fin = data['periodo_fin']
            
            # Obtener datos de ingresos y gastos
            from finanzas.models import Ingreso
            
            ingresos = Ingreso.objects.filter(
                fecha_ingreso__range=[periodo_inicio, periodo_fin],
                estado='confirmado'
            )
            gastos = Gastos.objects.filter(
                fecha_hora__date__range=[periodo_inicio, periodo_fin]
            )
            
            # Calcular tendencias
            total_ingresos = sum(ing.monto for ing in ingresos)
            total_gastos = sum(g.monto for g in gastos)
            
            # Análisis por mes
            tendencia_mensual = []
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            ingresos_por_mes = defaultdict(float)
            gastos_por_mes = defaultdict(float)
            
            for ingreso in ingresos:
                mes_key = ingreso.fecha_ingreso.strftime('%Y-%m')
                ingresos_por_mes[mes_key] += float(ingreso.monto)
            
            for gasto in gastos:
                mes_key = gasto.fecha_hora.strftime('%Y-%m')
                gastos_por_mes[mes_key] += float(gasto.monto)
            
            # Crear análisis
            analisis = AnalisisFinanciero.objects.create(
                nombre=f"Análisis de Tendencia {periodo_inicio} a {periodo_fin}",
                tipo_analisis='tendencia',
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                creado_por=request.user,
                datos_analisis={
                    'total_ingresos': float(total_ingresos),
                    'total_gastos': float(total_gastos),
                    'saldo_neto': float(total_ingresos - total_gastos),
                    'tendencia_mensual': [
                        {
                            'mes': mes,
                            'ingresos': ingresos_por_mes[mes],
                            'gastos': gastos_por_mes[mes],
                            'saldo': ingresos_por_mes[mes] - gastos_por_mes[mes]
                        }
                        for mes in sorted(set(list(ingresos_por_mes.keys()) + list(gastos_por_mes.keys())))
                    ]
                },
                conclusiones=f"Análisis de tendencia financiera del {periodo_inicio} al {periodo_fin}",
                recomendaciones="Revisar las tendencias mensuales para identificar patrones y oportunidades de mejora."
            )
            
            serializer = self.get_serializer(analisis)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error realizando análisis: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class IndicadorFinancieroViewSet(viewsets.ReadOnlyModelViewSet):
    """Indicadores Financieros - CU19"""
    queryset = IndicadorFinanciero.objects.all()
    serializer_class = IndicadorFinancieroSerializer
    permission_classes = [RolPermiso]
    
    @action(detail=False, methods=['get'])
    def calcular_indicadores(self, request):
        """Calcular indicadores financieros actuales"""
        try:
            from datetime import datetime, timedelta
            from finanzas.models import Ingreso
            
            # Período de análisis (últimos 12 meses)
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=365)
            
            # Obtener datos
            ingresos = Ingreso.objects.filter(
                fecha_ingreso__range=[fecha_inicio, fecha_fin],
                estado='confirmado'
            )
            gastos = Gastos.objects.filter(
                fecha_hora__date__range=[fecha_inicio, fecha_fin]
            )
            multas = Multa.objects.filter(
                fecha_emision__range=[fecha_inicio, fecha_fin]
            )
            
            total_ingresos = sum(ing.monto for ing in ingresos)
            total_gastos = sum(g.monto for g in gastos)
            total_multas = sum(m.monto for m in multas)
            
            # Calcular indicadores
            indicadores = []
            
            # Margen de utilidad
            if total_ingresos > 0:
                margen_utilidad = ((total_ingresos - total_gastos) / total_ingresos) * 100
                indicadores.append({
                    'nombre': 'Margen de Utilidad',
                    'tipo_indicador': 'rentabilidad',
                    'valor': float(margen_utilidad),
                    'unidad': '%',
                    'descripcion': 'Porcentaje de ingresos que se convierte en utilidad',
                    'formula': '(Ingresos - Gastos) / Ingresos * 100'
                })
            
            # Eficiencia de cobranza
            multas_pagadas = multas.filter(estado='pagada').count()
            total_multas_count = multas.count()
            if total_multas_count > 0:
                eficiencia_cobranza = (multas_pagadas / total_multas_count) * 100
                indicadores.append({
                    'nombre': 'Eficiencia de Cobranza',
                    'tipo_indicador': 'eficiencia',
                    'valor': float(eficiencia_cobranza),
                    'unidad': '%',
                    'descripcion': 'Porcentaje de multas pagadas',
                    'formula': 'Multas Pagadas / Total Multas * 100'
                })
            
            # Liquidez (simplificado)
            if total_gastos > 0:
                liquidez = (total_ingresos / total_gastos) * 100
                indicadores.append({
                    'nombre': 'Ratio de Liquidez',
                    'tipo_indicador': 'liquidez',
                    'valor': float(liquidez),
                    'unidad': '%',
                    'descripcion': 'Capacidad de cubrir gastos con ingresos',
                    'formula': 'Ingresos / Gastos * 100'
                })
            
            return Response({
                'indicadores': indicadores,
                'periodo_analisis': f'{fecha_inicio} a {fecha_fin}',
                'datos_base': {
                    'total_ingresos': float(total_ingresos),
                    'total_gastos': float(total_gastos),
                    'total_multas': float(total_multas)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error calculando indicadores: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class DashboardFinancieroViewSet(viewsets.ModelViewSet):
    """Dashboards Financieros Personalizables - CU19"""
    queryset = DashboardFinanciero.objects.all()
    serializer_class = DashboardFinancieroSerializer
    permission_classes = [RolPermiso]
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)
    
    @action(detail=False, methods=['get'])
    def resumen_financiero(self, request):
        """Obtener resumen financiero completo"""
        try:
            from datetime import datetime, timedelta
            from finanzas.models import Ingreso
            
            # Parámetros de fecha
            periodo = request.query_params.get('periodo', 'mes')
            fecha_fin = datetime.now().date()
            
            if periodo == 'mes':
                fecha_inicio = fecha_fin.replace(day=1)
            elif periodo == 'trimestre':
                fecha_inicio = fecha_fin - timedelta(days=90)
            elif periodo == 'año':
                fecha_inicio = fecha_fin - timedelta(days=365)
            else:
                fecha_inicio = fecha_fin - timedelta(days=30)
            
            # Obtener datos
            ingresos = Ingreso.objects.filter(
                fecha_ingreso__range=[fecha_inicio, fecha_fin],
                estado='confirmado'
            )
            gastos = Gastos.objects.filter(
                fecha_hora__date__range=[fecha_inicio, fecha_fin]
            )
            multas = Multa.objects.filter(
                fecha_emision__range=[fecha_inicio, fecha_fin]
            )
            
            # Calcular totales
            total_ingresos = sum(ing.monto for ing in ingresos)
            total_gastos = sum(g.monto for g in gastos)
            total_multas = sum(m.monto for m in multas)
            saldo_neto = total_ingresos - total_gastos
            
            # Margen de utilidad
            margen_utilidad = (saldo_neto / total_ingresos * 100) if total_ingresos > 0 else 0
            
            # Ingresos por tipo
            ingresos_por_tipo = {}
            for tipo, _ in Ingreso.TIPO_INGRESO_CHOICES:
                ingresos_por_tipo[tipo] = sum(
                    ing.monto for ing in ingresos if ing.tipo_ingreso == tipo
                )
            
            # Tendencia (últimos 6 meses)
            tendencia_ingresos = []
            tendencia_gastos = []
            
            for i in range(6):
                fecha_mes = fecha_fin - timedelta(days=30*i)
                mes_inicio = fecha_mes.replace(day=1)
                mes_fin = fecha_mes.replace(day=28) + timedelta(days=4)
                mes_fin = mes_fin - timedelta(days=mes_fin.day)
                
                ing_mes = sum(
                    ing.monto for ing in ingresos 
                    if mes_inicio <= ing.fecha_ingreso <= mes_fin
                )
                gas_mes = sum(
                    g.monto for g in gastos 
                    if mes_inicio <= g.fecha_hora.date() <= mes_fin
                )
                
                tendencia_ingresos.append({
                    'mes': fecha_mes.strftime('%Y-%m'),
                    'total': float(ing_mes)
                })
                tendencia_gastos.append({
                    'mes': fecha_mes.strftime('%Y-%m'),
                    'total': float(gas_mes)
                })
            
            tendencia_ingresos.reverse()
            tendencia_gastos.reverse()
            
            resumen = {
                'periodo': periodo,
                'total_ingresos': float(total_ingresos),
                'total_gastos': float(total_gastos),
                'total_multas': float(total_multas),
                'saldo_neto': float(saldo_neto),
                'margen_utilidad': float(margen_utilidad),
                'ingresos_por_tipo': {k: float(v) for k, v in ingresos_por_tipo.items()},
                'gastos_por_categoria': {},  # Se puede implementar categorización de gastos
                'tendencia_ingresos': tendencia_ingresos,
                'tendencia_gastos': tendencia_gastos
            }
            
            serializer = ResumenFinancieroSerializer(resumen)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error generando resumen: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def analisis_morosidad(self, request):
        """Análisis de morosidad"""
        try:
            # Obtener multas pendientes y vencidas
            multas_pendientes = Multa.objects.filter(estado='pendiente')
            multas_vencidas = multa.objects.filter(estado='vencida')
            
            total_morosidad = sum(m.monto for m in multas_pendientes) + sum(m.monto for m in multas_vencidas)
            residentes_morosos = len(set(m.residente.id for m in multas_pendientes))
            
            # Calcular porcentaje de morosidad
            total_multas = Multa.objects.count()
            porcentaje_morosidad = (residentes_morosos / total_multas * 100) if total_multas > 0 else 0
            
            # Top morosos
            from django.db.models import Sum
            top_morosos = Multa.objects.filter(
                estado__in=['pendiente', 'vencida']
            ).values('residente__persona__nombre').annotate(
                total_deuda=Sum('monto')
            ).order_by('-total_deuda')[:5]
            
            analisis = {
                'total_morosidad': float(total_morosidad),
                'residentes_morosos': residentes_morosos,
                'porcentaje_morosidad': float(porcentaje_morosidad),
                'promedio_dias_vencido': 0,  # Se puede calcular
                'top_morosos': [
                    {
                        'residente': item['residente__persona__nombre'],
                        'total_deuda': float(item['total_deuda'])
                    }
                    for item in top_morosos
                ],
                'tendencia_morosidad': [],  # Se puede implementar
                'prediccion_morosidad': {}  # Se puede implementar
            }
            
            serializer = AnalisisMorosidadSerializer(analisis)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error analizando morosidad: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
