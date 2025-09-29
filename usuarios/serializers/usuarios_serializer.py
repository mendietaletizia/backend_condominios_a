from rest_framework import serializers
from usuarios.models import (
    Residentes, Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo,
    PlacaVehiculo, PlacaInvitado, RegistroAcceso, ConfiguracionAcceso
)
from django.contrib.auth.hashers import make_password

# Residentes serializer
class ResidentesSerializer(serializers.ModelSerializer):
    usuario_asociado = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), required=False, allow_null=True
    )
    persona_info = serializers.SerializerMethodField()
    usuario_info = serializers.SerializerMethodField()
    usuario_asociado_info = serializers.SerializerMethodField()
    unidades_info = serializers.SerializerMethodField()
    mascotas_info = serializers.SerializerMethodField()

    class Meta:
        model = Residentes
        fields = '__all__'
    
    def get_persona_info(self, obj):
        if obj.persona:
            return {
                'id': obj.persona.id,
                'ci': obj.persona.ci,
                'nombre': obj.persona.nombre,
                'email': obj.persona.email,
                'telefono': obj.persona.telefono
            }
        return None
    
    def get_usuario_info(self, obj):
        if obj.usuario:
            return {
                'id': obj.usuario.id,
                'username': obj.usuario.username,
                'email': obj.usuario.email,
                'rol': obj.usuario.rol.nombre if obj.usuario.rol else None
            }
        return None
    
    def get_usuario_asociado_info(self, obj):
        if obj.usuario_asociado:
            return {
                'id': obj.usuario_asociado.id,
                'username': obj.usuario_asociado.username,
                'email': obj.usuario_asociado.email
            }
        return None
    
    def get_unidades_info(self, obj):
        from comunidad.models import ResidentesUnidad
        relaciones = ResidentesUnidad.objects.filter(id_residente=obj.id, estado=True)
        return [
            {
                'id': rel.id,
                'unidad_id': rel.id_unidad.id,
                'numero_casa': rel.id_unidad.numero_casa,
                'rol_en_unidad': rel.rol_en_unidad,
                'fecha_inicio': rel.fecha_inicio,
                'fecha_fin': rel.fecha_fin
            }
            for rel in relaciones
        ]
    
    def get_mascotas_info(self, obj):
        try:
            from comunidad.models import Mascota
            mascotas = Mascota.objects.filter(residente=obj.id, activo=True)
            return [
                {
                    'id': mascota.id,
                    'nombre': mascota.nombre,
                    'tipo': mascota.tipo,
                    'raza': mascota.raza,
                    'color': mascota.color,
                    'fecha_nacimiento': mascota.fecha_nacimiento,
                    'observaciones': mascota.observaciones,
                    'unidad_id': mascota.unidad.id if mascota.unidad else None,
                    'numero_casa': mascota.unidad.numero_casa if mascota.unidad else None
                }
                for mascota in mascotas
            ]
        except Exception as e:
            # Si hay error, retornar lista vacía
            return []

# Roles serializer
class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'nombre']

# Usuario serializer
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rol_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    rol = RolesSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'rol', 'rol_id']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

# Serializer específico para usuarios residentes (para selección de propietarios)
class UsuarioResidenteSerializer(serializers.ModelSerializer):
    """
    Serializer específico para usuarios con rol de residente
    Incluye información adicional para facilitar la selección como propietario
    """
    rol = RolesSerializer(read_only=True)
    residente_info = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'rol', 'residente_info', 'nombre_completo']
    
    def get_residente_info(self, obj):
        """Obtener información del residente asociado si existe"""
        try:
            from usuarios.models import Residentes
            residente = Residentes.objects.filter(usuario_asociado=obj).first()
            if residente:
                return {
                    'id': residente.id,
                    'nombre': residente.persona.nombre if residente.persona else None,
                    'ci': residente.persona.ci if residente.persona else None,
                    'telefono': residente.persona.telefono if residente.persona else None,
                    'email': residente.persona.email if residente.persona else None
                }
        except Exception:
            pass
        return None
    
    def get_nombre_completo(self, obj):
        """Obtener nombre completo del usuario"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        else:
            return obj.username

# Persona serializer
class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'ci', 'nombre', 'email', 'telefono']

# Permiso serializer
class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'descripcion']

# RolPermiso serializer
class RolPermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolPermiso
        fields = ['id', 'rol', 'permiso']

# Empleado serializer
class EmpleadoSerializer(serializers.ModelSerializer):
    persona_info = serializers.SerializerMethodField()
    usuario_info = serializers.SerializerMethodField()
    cargo_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Empleado
        fields = ['id', 'persona', 'usuario', 'cargo', 'persona_info', 'usuario_info', 'cargo_display']
    
    def get_persona_info(self, obj):
        if obj.persona:
            return {
                'id': obj.persona.id,
                'nombre': obj.persona.nombre,
                'ci': obj.persona.ci,
                'telefono': obj.persona.telefono,
                'email': obj.persona.email
            }
        return None
    
    def get_usuario_info(self, obj):
        if obj.usuario:
            return {
                'id': obj.usuario.id,
                'username': obj.usuario.username,
                'email': obj.usuario.email,
                'is_active': obj.usuario.is_active,
                'rol': obj.usuario.rol.nombre if obj.usuario.rol else None
            }
        return None
    
    def get_cargo_display(self, obj):
        cargo_colors = {
            'administrador': 'red',
            'seguridad': 'blue',
            'mantenimiento': 'green',
            'limpieza': 'orange',
            'jardinero': 'green',
            'portero': 'purple'
        }
        return {
            'nombre': obj.cargo.title(),
            'color': cargo_colors.get(obj.cargo.lower(), 'default')
        }

# Vehiculo serializer
class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'

# AccesoVehicular serializer
class AccesoVehicularSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccesoVehicular
        fields = '__all__'

# Visita serializer
class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita
        fields = '__all__'

# Invitado serializer
class InvitadoSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    check_in_by_username = serializers.CharField(source='check_in_by.username', read_only=True)
    check_out_by_username = serializers.CharField(source='check_out_by.username', read_only=True)

    class Meta:
        model = Invitado
        fields = '__all__'
        extra_kwargs = {
            # Residente se asigna automáticamente desde el usuario autenticado si no se envía
            'residente': {'required': False, 'allow_null': True},
        }

    def get_residente_info(self, obj):
        try:
            if obj.residente:
                return {
                    'id': obj.residente.id,
                    'nombre': obj.residente.persona.nombre if getattr(obj.residente, 'persona', None) else None,
                }
        except Exception:
            return None
        return None

    def validate(self, attrs):
        tipo = attrs.get('tipo') or (self.instance.tipo if self.instance else 'casual')
        evento = attrs.get('evento') if 'evento' in attrs else (self.instance.evento if self.instance else None)
        fecha_inicio = attrs.get('fecha_inicio') if 'fecha_inicio' in attrs else (self.instance.fecha_inicio if self.instance else None)
        fecha_fin = attrs.get('fecha_fin') if 'fecha_fin' in attrs else (self.instance.fecha_fin if self.instance else None)

        if tipo == 'evento' and not evento:
            raise serializers.ValidationError('Invitado de tipo evento requiere campo evento')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError('fecha_fin no puede ser anterior a fecha_inicio')

        return attrs

    def create(self, validated_data):
        # Si no viene residente explícito, asignar por usuario autenticado si es residente
        request = self.context.get('request')
        if request and not validated_data.get('residente'):
            try:
                from usuarios.models import Residentes
                residente = Residentes.objects.filter(usuario=request.user).first()
                if residente:
                    validated_data['residente'] = residente
            except Exception:
                pass
        return super().create(validated_data)

# Reclamo serializer
class ReclamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamo
        fields = '__all__'

# Serializers para CU14: Gestión de Acceso con IA
class PlacaVehiculoSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()
    unidad_info = serializers.SerializerMethodField()

    class Meta:
        model = PlacaVehiculo
        fields = '__all__'

    def get_residente_info(self, obj):
        return {
            'id': obj.residente.id,
            'nombre': obj.residente.persona.nombre,
            'email': obj.residente.persona.email
        }

    def get_unidad_info(self, obj):
        try:
            from comunidad.models import ResidentesUnidad
            rel = ResidentesUnidad.objects.filter(id_residente=obj.residente, estado=True).select_related('id_unidad').first()
            if rel and rel.id_unidad:
                return {
                    'id': rel.id_unidad.id,
                    'numero_casa': rel.id_unidad.numero_casa
                }
        except Exception:
            pass
        return None

class PlacaInvitadoSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()

    class Meta:
        model = PlacaInvitado
        fields = '__all__'

    def get_residente_info(self, obj):
        return {
            'id': obj.residente.id,
            'nombre': obj.residente.persona.nombre,
            'email': obj.residente.persona.email
        }

class RegistroAccesoSerializer(serializers.ModelSerializer):
    placa_vehiculo_info = serializers.SerializerMethodField()
    placa_invitado_info = serializers.SerializerMethodField()
    autorizado_por_info = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAcceso
        fields = '__all__'

    def get_placa_vehiculo_info(self, obj):
        if obj.placa_vehiculo:
            return {
                'id': obj.placa_vehiculo.id,
                'placa': obj.placa_vehiculo.placa,
                'marca': obj.placa_vehiculo.marca,
                'modelo': obj.placa_vehiculo.modelo
            }
        return None

    def get_placa_invitado_info(self, obj):
        if obj.placa_invitado:
            return {
                'id': obj.placa_invitado.id,
                'placa': obj.placa_invitado.placa,
                'nombre_visitante': obj.placa_invitado.nombre_visitante,
                'fecha_vencimiento': obj.placa_invitado.fecha_vencimiento
            }
        return None

    def get_autorizado_por_info(self, obj):
        if obj.autorizado_por:
            return {
                'id': obj.autorizado_por.id,
                'username': obj.autorizado_por.username,
            }
        return None

# CU23: Asignación de Tareas para Empleados - Serializers adicionales
from usuarios.models import TipoTarea, TareaEmpleado, ComentarioTarea, EvaluacionTarea


class TipoTareaSerializer(serializers.ModelSerializer):
    """Serializer para TipoTarea - CU23"""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    prioridad_default_display = serializers.CharField(source='get_prioridad_default_display', read_only=True)
    
    class Meta:
        model = TipoTarea
        fields = [
            'id', 'nombre', 'categoria', 'categoria_display', 'descripcion',
            'prioridad_default', 'prioridad_default_display', 'duracion_estimada_horas',
            'requiere_especialista', 'requiere_herramientas', 'materiales_necesarios',
            'instrucciones', 'activo'
        ]
    
    def validate_duracion_estimada_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError("La duración estimada debe ser mayor a 0")
        return value


class TareaEmpleadoSerializer(serializers.ModelSerializer):
    """Serializer para TareaEmpleado - CU23"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    tipo_tarea_nombre = serializers.CharField(source='tipo_tarea.nombre', read_only=True)
    tipo_tarea_categoria = serializers.CharField(source='tipo_tarea.categoria', read_only=True)
    empleado_nombre = serializers.SerializerMethodField()
    supervisor_nombre = serializers.CharField(source='supervisor.username', read_only=True)
    progreso_calculado = serializers.SerializerMethodField()
    esta_vencida = serializers.SerializerMethodField()
    tiempo_restante = serializers.SerializerMethodField()
    fecha_asignacion_formatted = serializers.SerializerMethodField()
    fecha_limite_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TareaEmpleado
        fields = [
            'id', 'titulo', 'descripcion', 'tipo_tarea', 'tipo_tarea_nombre', 'tipo_tarea_categoria',
            'empleado_asignado', 'empleado_nombre', 'supervisor', 'supervisor_nombre',
            'fecha_asignacion', 'fecha_asignacion_formatted', 'fecha_limite', 'fecha_limite_formatted',
            'fecha_inicio', 'fecha_completado', 'estado', 'estado_display', 'prioridad', 'prioridad_display',
            'materiales_proporcionados', 'herramientas_necesarias', 'costo_estimado', 'costo_real',
            'horas_trabajadas', 'progreso_porcentaje', 'progreso_calculado', 'esta_vencida', 'tiempo_restante',
            'observaciones_empleado', 'observaciones_supervisor', 'foto_antes', 'foto_despues',
            'documento_adjunto', 'fecha_modificacion'
        ]
        read_only_fields = ['fecha_asignacion', 'fecha_modificacion']
    
    def get_empleado_nombre(self, obj):
        return f"{obj.empleado_asignado.persona_relacionada.nombre} {obj.empleado_asignado.persona_relacionada.apellido}"
    
    def get_progreso_calculado(self, obj):
        return obj.calcular_progreso()
    
    def get_esta_vencida(self, obj):
        return obj.esta_vencida()
    
    def get_tiempo_restante(self, obj):
        return obj.tiempo_restante()
    
    def get_fecha_asignacion_formatted(self, obj):
        return obj.fecha_asignacion.strftime('%d/%m/%Y %H:%M')
    
    def get_fecha_limite_formatted(self, obj):
        return obj.fecha_limite.strftime('%d/%m/%Y %H:%M')
    
    def validate_fecha_limite(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("La fecha límite debe ser futura")
        return value
    
    def validate_progreso_porcentaje(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El progreso debe estar entre 0 y 100")
        return value
    
    def validate_costo_estimado(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo estimado no puede ser negativo")
        return value
    
    def validate_costo_real(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo real no puede ser negativo")
        return value


class ComentarioTareaSerializer(serializers.ModelSerializer):
    """Serializer para ComentarioTarea - CU23"""
    autor_nombre = serializers.CharField(source='autor.username', read_only=True)
    fecha_comentario_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ComentarioTarea
        fields = [
            'id', 'tarea', 'autor', 'autor_nombre', 'comentario',
            'fecha_comentario', 'fecha_comentario_formatted', 'es_interno'
        ]
        read_only_fields = ['fecha_comentario']


class EvaluacionTareaSerializer(serializers.ModelSerializer):
    """Serializer para EvaluacionTarea - CU23"""
    calificacion_promedio = serializers.SerializerMethodField()
    evaluador_nombre = serializers.CharField(source='evaluador.username', read_only=True)
    fecha_evaluacion_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = EvaluacionTarea
        fields = [
            'id', 'tarea', 'evaluador', 'evaluador_nombre',
            'calidad_trabajo', 'cumplimiento_tiempo', 'uso_recursos', 'comunicacion',
            'comentarios_positivos', 'areas_mejora', 'recomendaciones',
            'fecha_evaluacion', 'fecha_evaluacion_formatted', 'calificacion_promedio'
        ]
        read_only_fields = ['fecha_evaluacion']
    
    def get_calificacion_promedio(self, obj):
        return obj.calificacion_promedio()
    
    def get_fecha_evaluacion_formatted(self, obj):
        return obj.fecha_evaluacion.strftime('%d/%m/%Y %H:%M')
    
    def validate_calidad_trabajo(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value
    
    def validate_cumplimiento_tiempo(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value
    
    def validate_uso_recursos(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value
    
    def validate_comunicacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value


# Serializers para estadísticas y resúmenes
class ResumenTareasSerializer(serializers.Serializer):
    """Serializer para resumen de tareas - CU23"""
    total_tareas = serializers.IntegerField()
    tareas_asignadas = serializers.IntegerField()
    tareas_en_progreso = serializers.IntegerField()
    tareas_completadas = serializers.IntegerField()
    tareas_vencidas = serializers.IntegerField()
    tareas_canceladas = serializers.IntegerField()
    horas_trabajadas_totales = serializers.DecimalField(max_digits=8, decimal_places=2)
    costo_total_estimado = serializers.DecimalField(max_digits=15, decimal_places=2)
    costo_total_real = serializers.DecimalField(max_digits=15, decimal_places=2)


class EstadisticasTareasSerializer(serializers.Serializer):
    """Serializer para estadísticas de tareas - CU23"""
    tareas_por_estado = serializers.DictField()
    tareas_por_prioridad = serializers.DictField()
    tareas_por_categoria = serializers.DictField()
    tareas_por_empleado = serializers.DictField()
    tareas_por_mes = serializers.ListField()
    horas_por_mes = serializers.ListField()
    calificaciones_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    empleados_mas_productivos = serializers.ListField()


class ResumenEmpleadoSerializer(serializers.Serializer):
    """Serializer para resumen de empleado - CU23"""
    empleado_nombre = serializers.CharField()
    total_tareas_asignadas = serializers.IntegerField()
    tareas_completadas = serializers.IntegerField()
    tareas_en_progreso = serializers.IntegerField()
    tareas_vencidas = serializers.IntegerField()
    horas_trabajadas_totales = serializers.DecimalField(max_digits=8, decimal_places=2)
    calificacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2)
    eficiencia_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2)

class ConfiguracionAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionAcceso
        fields = '__all__'
