from rest_framework import serializers
from economia.models import Gastos, Multa, ReporteFinanciero, AnalisisFinanciero, IndicadorFinanciero, DashboardFinanciero
# from finanzas.models import Pago, Expensa  # Comentado temporalmente

class GastosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gastos
        fields = '__all__'

class MultaSerializer(serializers.ModelSerializer):
    reglamento_info = serializers.SerializerMethodField()
    residente_info = serializers.SerializerMethodField()
    dias_vencido = serializers.SerializerMethodField()
    
    class Meta:
        model = Multa
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_reglamento_info(self, obj):
        """Obtener información del reglamento asociado"""
        if obj.reglamento:
            return {
                'id': obj.reglamento.id,
                'articulo': obj.reglamento.articulo,
                'titulo': obj.reglamento.titulo,
                'tipo': obj.reglamento.tipo,
                'monto_multa': obj.reglamento.monto_multa,
                'dias_suspension': obj.reglamento.dias_suspension
            }
        return None
    
    def get_residente_info(self, obj):
        """Obtener información del residente multado"""
        if obj.residente and obj.residente.persona:
            return {
                'id': obj.residente.id,
                'nombre': obj.residente.persona.nombre,
                'apellido': obj.residente.persona.apellido,
                'ci': obj.residente.persona.ci,
                'email': obj.residente.persona.email,
                'telefono': obj.residente.persona.telefono
            }
        return None
    
    def get_dias_vencido(self, obj):
        """Calcular días vencido si la multa está vencida"""
        try:
            if obj.estado == 'pendiente' and obj.fecha_vencimiento:
                from django.utils import timezone
                hoy = timezone.now().date()
                if obj.fecha_vencimiento < hoy:
                    return (hoy - obj.fecha_vencimiento).days
            return 0
        except:
            return 0

# Comentado temporalmente hasta que finanzas esté configurado
# Serializers comentados temporalmente para CU7
# class PagoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Pago
#         fields = '__all__'

# class ExpensaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Expensa
#         fields = '__all__'

# CU19: Reportes y Analítica
class ReporteFinancieroSerializer(serializers.ModelSerializer):
    tipo_reporte_display = serializers.CharField(source='get_tipo_reporte_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    generado_por_nombre = serializers.CharField(source='generado_por.username', read_only=True)
    periodo_dias = serializers.SerializerMethodField()
    
    class Meta:
        model = ReporteFinanciero
        fields = [
            'id', 'nombre', 'tipo_reporte', 'tipo_reporte_display',
            'fecha_inicio', 'fecha_fin', 'estado', 'estado_display',
            'total_ingresos', 'total_gastos', 'total_multas', 'saldo_neto',
            'archivo_pdf', 'archivo_excel', 'fecha_generacion', 'fecha_modificacion',
            'generado_por', 'generado_por_nombre', 'observaciones', 'periodo_dias'
        ]
        read_only_fields = ['fecha_generacion', 'fecha_modificacion', 'generado_por']
    
    def get_periodo_dias(self, obj):
        """Calcular días del período"""
        return (obj.fecha_fin - obj.fecha_inicio).days + 1
    
    def validate_fecha_fin(self, value):
        """Validar que fecha_fin sea posterior a fecha_inicio"""
        fecha_inicio = self.initial_data.get('fecha_inicio')
        if fecha_inicio and value < fecha_inicio:
            raise serializers.ValidationError("La fecha fin debe ser posterior a la fecha inicio")
        return value

class AnalisisFinancieroSerializer(serializers.ModelSerializer):
    tipo_analisis_display = serializers.CharField(source='get_tipo_analisis_display', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    periodo_dias = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalisisFinanciero
        fields = [
            'id', 'nombre', 'tipo_analisis', 'tipo_analisis_display',
            'periodo_inicio', 'periodo_fin', 'datos_analisis',
            'conclusiones', 'recomendaciones', 'fecha_creacion',
            'fecha_modificacion', 'creado_por', 'creado_por_nombre', 'periodo_dias'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'creado_por']
    
    def get_periodo_dias(self, obj):
        """Calcular días del período"""
        return (obj.periodo_fin - obj.periodo_inicio).days + 1

class IndicadorFinancieroSerializer(serializers.ModelSerializer):
    tipo_indicador_display = serializers.CharField(source='get_tipo_indicador_display', read_only=True)
    
    class Meta:
        model = IndicadorFinanciero
        fields = [
            'id', 'nombre', 'tipo_indicador', 'tipo_indicador_display',
            'valor', 'unidad', 'fecha_calculo', 'descripcion', 'formula', 'fecha_creacion'
        ]
        read_only_fields = ['fecha_creacion']

class DashboardFinancieroSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    
    class Meta:
        model = DashboardFinanciero
        fields = [
            'id', 'nombre', 'descripcion', 'widgets_config',
            'filtros_default', 'es_publico', 'fecha_creacion',
            'fecha_modificacion', 'creado_por', 'creado_por_nombre'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'creado_por']

class ResumenFinancieroSerializer(serializers.Serializer):
    """Serializer para resúmenes financieros"""
    periodo = serializers.CharField()
    total_ingresos = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gastos = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_multas = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo_neto = serializers.DecimalField(max_digits=15, decimal_places=2)
    margen_utilidad = serializers.DecimalField(max_digits=5, decimal_places=2)
    ingresos_por_tipo = serializers.DictField()
    gastos_por_categoria = serializers.DictField()
    tendencia_ingresos = serializers.ListField()
    tendencia_gastos = serializers.ListField()

class AnalisisMorosidadSerializer(serializers.Serializer):
    """Serializer para análisis de morosidad"""
    total_morosidad = serializers.DecimalField(max_digits=15, decimal_places=2)
    residentes_morosos = serializers.IntegerField()
    porcentaje_morosidad = serializers.DecimalField(max_digits=5, decimal_places=2)
    promedio_dias_vencido = serializers.DecimalField(max_digits=8, decimal_places=2)
    top_morosos = serializers.ListField()
    tendencia_morosidad = serializers.ListField()
    prediccion_morosidad = serializers.DictField()

class ProyeccionFinancieraSerializer(serializers.Serializer):
    """Serializer para proyecciones financieras"""
    periodo_proyeccion = serializers.CharField()
    ingresos_proyectados = serializers.DecimalField(max_digits=15, decimal_places=2)
    gastos_proyectados = serializers.DecimalField(max_digits=15, decimal_places=2)
    saldo_proyectado = serializers.DecimalField(max_digits=15, decimal_places=2)
    escenario_optimista = serializers.DictField()
    escenario_pesimista = serializers.DictField()
    escenario_realista = serializers.DictField()
    factores_riesgo = serializers.ListField()
    recomendaciones = serializers.ListField()
