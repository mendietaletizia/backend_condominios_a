from rest_framework import serializers
from mantenimiento.models import AreaComun, Reserva, Mantenimiento, BitacoraMantenimiento, Reglamento

class AreaComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaComun
        fields = '__all__'

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'

class MantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mantenimiento
        fields = '__all__'

class BitacoraMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BitacoraMantenimiento
        fields = '__all__'

class ReglamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reglamento
        fields = '__all__'

# CU16: Mantenimiento de Áreas Comunes - Nuevos Serializers
from mantenimiento.models import TipoMantenimiento, PlanMantenimiento, TareaMantenimiento, InventarioArea
from usuarios.models import Empleado


class TipoMantenimientoSerializer(serializers.ModelSerializer):
    """Serializer para TipoMantenimiento - CU16"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_default_display = serializers.CharField(source='get_prioridad_default_display', read_only=True)
    
    class Meta:
        model = TipoMantenimiento
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display', 'descripcion',
            'prioridad_default', 'prioridad_default_display', 'frecuencia_dias',
            'duracion_estimada_horas', 'costo_estimado', 'requiere_especialista', 'activo'
        ]
    
    def validate_costo_estimado(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo estimado no puede ser negativo")
        return value


class PlanMantenimientoSerializer(serializers.ModelSerializer):
    """Serializer para PlanMantenimiento - CU16"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    area_comun_nombre = serializers.CharField(source='area_comun.nombre', read_only=True)
    tipo_mantenimiento_nombre = serializers.CharField(source='tipo_mantenimiento.nombre', read_only=True)
    empleado_nombre = serializers.SerializerMethodField()
    supervisor_nombre = serializers.CharField(source='supervisor.username', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    progreso = serializers.SerializerMethodField()
    esta_vencido = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanMantenimiento
        fields = [
            'id', 'nombre', 'descripcion', 'area_comun', 'area_comun_nombre',
            'tipo_mantenimiento', 'tipo_mantenimiento_nombre', 'fecha_inicio',
            'fecha_fin_estimada', 'fecha_fin_real', 'estado', 'estado_display',
            'prioridad', 'prioridad_display', 'empleado_asignado', 'empleado_nombre',
            'supervisor', 'supervisor_nombre', 'costo_presupuestado', 'costo_real',
            'materiales_necesarios', 'fecha_creacion', 'fecha_modificacion',
            'creado_por', 'creado_por_nombre', 'progreso', 'esta_vencido'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'creado_por']
    
    def get_empleado_nombre(self, obj):
        if obj.empleado_asignado:
            return f"{obj.empleado_asignado.persona_relacionada.nombre} {obj.empleado_asignado.persona_relacionada.apellido}"
        return None
    
    def get_progreso(self, obj):
        return obj.calcular_progreso()
    
    def get_esta_vencido(self, obj):
        return obj.esta_vencido()


class TareaMantenimientoSerializer(serializers.ModelSerializer):
    """Serializer para TareaMantenimiento - CU16"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    plan_mantenimiento_nombre = serializers.CharField(source='plan_mantenimiento.nombre', read_only=True)
    empleado_nombre = serializers.SerializerMethodField()
    progreso = serializers.SerializerMethodField()
    
    class Meta:
        model = TareaMantenimiento
        fields = [
            'id', 'plan_mantenimiento', 'plan_mantenimiento_nombre', 'nombre',
            'descripcion', 'fecha_inicio', 'fecha_fin_estimada', 'fecha_fin_real',
            'estado', 'estado_display', 'prioridad', 'prioridad_display',
            'empleado_asignado', 'empleado_nombre', 'materiales_utilizados',
            'costo_real', 'horas_trabajadas', 'fecha_creacion', 'fecha_modificacion',
            'progreso'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_empleado_nombre(self, obj):
        if obj.empleado_asignado:
            return f"{obj.empleado_asignado.persona_relacionada.nombre} {obj.empleado_asignado.persona_relacionada.apellido}"
        return None
    
    def get_progreso(self, obj):
        return obj.calcular_progreso()


class InventarioAreaSerializer(serializers.ModelSerializer):
    """Serializer para InventarioArea - CU16"""
    estado_actual_display = serializers.CharField(source='get_estado_actual_display', read_only=True)
    area_comun_nombre = serializers.CharField(source='area_comun.nombre', read_only=True)
    registrado_por_nombre = serializers.CharField(source='registrado_por.username', read_only=True)
    necesita_mantenimiento = serializers.SerializerMethodField()
    
    class Meta:
        model = InventarioArea
        fields = [
            'id', 'area_comun', 'area_comun_nombre', 'nombre_equipo', 'descripcion',
            'marca', 'modelo', 'numero_serie', 'fecha_adquisicion', 'costo_adquisicion',
            'estado_actual', 'estado_actual_display', 'fecha_ultimo_mantenimiento',
            'fecha_proximo_mantenimiento', 'frecuencia_mantenimiento_dias',
            'fecha_registro', 'fecha_modificacion', 'registrado_por', 'registrado_por_nombre',
            'necesita_mantenimiento'
        ]
        read_only_fields = ['fecha_registro', 'fecha_modificacion', 'registrado_por']
    
    def get_necesita_mantenimiento(self, obj):
        return obj.necesita_mantenimiento()


# Serializers para estadísticas y resúmenes
class ResumenMantenimientoSerializer(serializers.Serializer):
    """Serializer para resumen de mantenimiento - CU16"""
    total_planes = serializers.IntegerField()
    planes_activos = serializers.IntegerField()
    planes_completados = serializers.IntegerField()
    planes_vencidos = serializers.IntegerField()
    total_tareas = serializers.IntegerField()
    tareas_pendientes = serializers.IntegerField()
    tareas_en_progreso = serializers.IntegerField()
    tareas_completadas = serializers.IntegerField()
    costo_total_presupuestado = serializers.DecimalField(max_digits=15, decimal_places=2)
    costo_total_real = serializers.DecimalField(max_digits=15, decimal_places=2)
    horas_trabajadas_totales = serializers.DecimalField(max_digits=8, decimal_places=2)


class EstadisticasMantenimientoSerializer(serializers.Serializer):
    """Serializer para estadísticas de mantenimiento - CU16"""
    total_planes = serializers.IntegerField()
    planes_activos = serializers.IntegerField()
    planes_completados = serializers.IntegerField()
    total_tareas = serializers.IntegerField()
    tareas_pendientes = serializers.IntegerField()
    tareas_completadas = serializers.IntegerField()
    total_equipos = serializers.IntegerField()
    equipos_necesitan_mantenimiento = serializers.IntegerField()


class ResumenEquiposSerializer(serializers.Serializer):
    """Serializer para resumen de equipos por área - CU16"""
    area_comun_nombre = serializers.CharField()
    total_equipos = serializers.IntegerField()
    equipos_buen_estado = serializers.IntegerField()
    equipos_regular_estado = serializers.IntegerField()
    equipos_mal_estado = serializers.IntegerField()
    equipos_fuera_servicio = serializers.IntegerField()
    equipos_en_reparacion = serializers.IntegerField()
    equipos_necesitan_mantenimiento = serializers.IntegerField()
    costo_total_equipos = serializers.DecimalField(max_digits=15, decimal_places=2)