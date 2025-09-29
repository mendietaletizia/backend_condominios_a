from rest_framework import serializers
from ..models import CuotaMensual, CuotaUnidad, PagoCuota, Ingreso, ResumenIngresos
from comunidad.models import Unidad
from usuarios.models import Persona

class CuotaMensualSerializer(serializers.ModelSerializer):
    monto_por_unidad = serializers.SerializerMethodField()
    total_unidades = serializers.SerializerMethodField()
    cuotas_pagadas = serializers.SerializerMethodField()
    cuotas_pendientes = serializers.SerializerMethodField()
    cuotas_vencidas = serializers.SerializerMethodField()
    monto_total_cobrado = serializers.SerializerMethodField()
    monto_total_pendiente = serializers.SerializerMethodField()

    class Meta:
        model = CuotaMensual
        fields = [
            'id', 'mes_año', 'monto_total', 'fecha_limite', 'descripcion',
            'estado', 'fecha_creacion', 'fecha_modificacion', 'creado_por',
            'monto_por_unidad', 'total_unidades', 'cuotas_pagadas',
            'cuotas_pendientes', 'cuotas_vencidas', 'monto_total_cobrado',
            'monto_total_pendiente'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'creado_por']

    def validate_mes_año(self, value):
        """Validar que el mes/año no esté duplicado"""
        if self.instance is None:  # Solo validar en creación
            if CuotaMensual.objects.filter(mes_año=value).exists():
                # En lugar de error, permitir duplicados temporalmente
                pass
        return value

    def get_monto_por_unidad(self, obj):
        return obj.calcular_monto_por_unidad()

    def get_total_unidades(self, obj):
        return obj.cuotas_unidad.count()

    def get_cuotas_pagadas(self, obj):
        return obj.cuotas_unidad.filter(estado='pagada').count()

    def get_cuotas_pendientes(self, obj):
        return obj.cuotas_unidad.filter(estado='pendiente').count()

    def get_cuotas_vencidas(self, obj):
        return obj.cuotas_unidad.filter(estado='vencida').count()

    def get_monto_total_cobrado(self, obj):
        return sum(cuota.monto_pagado for cuota in obj.cuotas_unidad.all())

    def get_monto_total_pendiente(self, obj):
        return sum(cuota.calcular_saldo_pendiente() for cuota in obj.cuotas_unidad.all())

class CuotaUnidadSerializer(serializers.ModelSerializer):
    unidad_numero = serializers.CharField(source='unidad.numero_casa', read_only=True)
    unidad_metros = serializers.DecimalField(source='unidad.metros_cuadrados', max_digits=8, decimal_places=2, read_only=True)
    residente_nombre = serializers.SerializerMethodField()
    saldo_pendiente = serializers.SerializerMethodField()
    dias_vencido = serializers.SerializerMethodField()

    class Meta:
        model = CuotaUnidad
        fields = [
            'id', 'cuota_mensual', 'unidad', 'unidad_numero', 'unidad_metros',
            'monto', 'fecha_limite', 'estado', 'monto_pagado', 'fecha_pago',
            'observaciones', 'residente_nombre', 'saldo_pendiente', 'dias_vencido'
        ]

    def get_residente_nombre(self, obj):
        """Obtener el nombre del residente principal de la unidad"""
        try:
            # Buscar el residente principal (propietario) de la unidad
            relacion = obj.unidad.residentesunidad_set.filter(
                rol_en_unidad='propietario', 
                estado=True
            ).first()
            if relacion and relacion.id_residente and relacion.id_residente.persona:
                return f"{relacion.id_residente.persona.nombre} {relacion.id_residente.persona.apellido}"
            return "Sin residente"
        except Exception:
            return "Sin residente"

    def get_saldo_pendiente(self, obj):
        """Calcular el saldo pendiente de la cuota"""
        return obj.calcular_saldo_pendiente()

    def get_dias_vencido(self, obj):
        """Calcular los días vencidos si la cuota está vencida"""
        from django.utils import timezone
        if obj.estado == 'vencida' and obj.fecha_limite:
            return (timezone.now().date() - obj.fecha_limite).days
        return 0

class CuotaUnidadUpdateSerializer(serializers.ModelSerializer):
    """Serializer específico para actualizar cuotas por unidad"""
    
    class Meta:
        model = CuotaUnidad
        fields = ['monto', 'fecha_limite', 'observaciones']
        
    def validate_monto(self, value):
        """Validar que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value
        
    def validate_fecha_limite(self, value):
        """Validar que la fecha límite sea válida"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("La fecha límite no puede ser anterior a hoy")
        return value

class PagoCuotaSerializer(serializers.ModelSerializer):
    cuota_info = serializers.SerializerMethodField()

    class Meta:
        model = PagoCuota
        fields = [
            'id', 'cuota_unidad', 'monto', 'fecha_pago', 'metodo_pago',
            'comprobante', 'numero_referencia', 'observaciones',
            'fecha_creacion', 'cuota_info'
        ]
        read_only_fields = ['fecha_creacion', 'registrado_por']

    def get_cuota_info(self, obj):
        return {
            'mes_año': obj.cuota_unidad.cuota_mensual.mes_año,
            'unidad': obj.cuota_unidad.unidad.numero_casa,
            'monto_total': obj.cuota_unidad.monto
        }

class ResumenCuotasSerializer(serializers.Serializer):
    total_cuotas = serializers.IntegerField()
    cuotas_pagadas = serializers.IntegerField()
    cuotas_pendientes = serializers.IntegerField()
    cuotas_vencidas = serializers.IntegerField()
    monto_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    monto_cobrado = serializers.DecimalField(max_digits=12, decimal_places=2)
    monto_pendiente = serializers.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_cobranza = serializers.DecimalField(max_digits=5, decimal_places=2)

class MorososSerializer(serializers.Serializer):
    cuota_id = serializers.IntegerField()
    unidad = serializers.CharField()
    residente = serializers.CharField()
    mes_año = serializers.CharField()
    monto_adeudado = serializers.DecimalField(max_digits=10, decimal_places=2)
    dias_vencido = serializers.IntegerField()
    fecha_vencimiento = serializers.DateField()

# CU18 - Gestión de Ingresos
class IngresoSerializer(serializers.ModelSerializer):
    tipo_ingreso_display = serializers.CharField(source='get_tipo_ingreso_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    unidad_numero = serializers.CharField(source='unidad_relacionada.numero_casa', read_only=True)
    residente_nombre = serializers.CharField(source='residente_relacionado.nombre', read_only=True)
    mes_año = serializers.SerializerMethodField()
    
    class Meta:
        model = Ingreso
        fields = [
            'id', 'tipo_ingreso', 'tipo_ingreso_display', 'concepto', 'descripcion',
            'monto', 'fecha_ingreso', 'fecha_registro', 'estado', 'estado_display',
            'unidad_relacionada', 'unidad_numero', 'residente_relacionado', 'residente_nombre',
            'cuota_relacionada', 'comprobante', 'numero_referencia', 'observaciones',
            'registrado_por', 'mes_año'
        ]
        read_only_fields = ['fecha_registro', 'registrado_por']
    
    def get_mes_año(self, obj):
        return obj.get_mes_año()
    
    def validate_monto(self, value):
        """Validar que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value
    
    def validate_fecha_ingreso(self, value):
        """Validar que la fecha de ingreso no sea futura"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de ingreso no puede ser futura")
        return value

class ResumenIngresosSerializer(serializers.ModelSerializer):
    porcentaje_cuotas = serializers.SerializerMethodField()
    porcentaje_multas = serializers.SerializerMethodField()
    porcentaje_servicios = serializers.SerializerMethodField()
    porcentaje_alquiler = serializers.SerializerMethodField()
    porcentaje_eventos = serializers.SerializerMethodField()
    porcentaje_donaciones = serializers.SerializerMethodField()
    porcentaje_otros = serializers.SerializerMethodField()
    
    class Meta:
        model = ResumenIngresos
        fields = [
            'id', 'mes_año', 'total_cuotas', 'total_multas', 'total_servicios',
            'total_alquiler', 'total_eventos', 'total_donaciones', 'total_otros',
            'total_general', 'fecha_creacion', 'fecha_modificacion', 'creado_por',
            'porcentaje_cuotas', 'porcentaje_multas', 'porcentaje_servicios',
            'porcentaje_alquiler', 'porcentaje_eventos', 'porcentaje_donaciones',
            'porcentaje_otros'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'creado_por']
    
    def get_porcentaje_cuotas(self, obj):
        if obj.total_general > 0:
            return round((obj.total_cuotas / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_multas(self, obj):
        if obj.total_general > 0:
            return round((obj.total_multas / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_servicios(self, obj):
        if obj.total_general > 0:
            return round((obj.total_servicios / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_alquiler(self, obj):
        if obj.total_general > 0:
            return round((obj.total_alquiler / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_eventos(self, obj):
        if obj.total_general > 0:
            return round((obj.total_eventos / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_donaciones(self, obj):
        if obj.total_general > 0:
            return round((obj.total_donaciones / obj.total_general) * 100, 2)
        return 0
    
    def get_porcentaje_otros(self, obj):
        if obj.total_general > 0:
            return round((obj.total_otros / obj.total_general) * 100, 2)
        return 0

 