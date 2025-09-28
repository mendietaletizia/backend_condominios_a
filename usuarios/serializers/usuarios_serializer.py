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
    class Meta:
        model = Invitado
        fields = '__all__'

# Reclamo serializer
class ReclamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamo
        fields = '__all__'

# Serializers para CU14: Gestión de Acceso con IA
class PlacaVehiculoSerializer(serializers.ModelSerializer):
    residente_info = serializers.SerializerMethodField()

    class Meta:
        model = PlacaVehiculo
        fields = '__all__'

    def get_residente_info(self, obj):
        return {
            'id': obj.residente.id,
            'nombre': obj.residente.persona.nombre,
            'email': obj.residente.persona.email
        }

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
                'email': obj.autorizado_por.email
            }
        return None

class ConfiguracionAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionAcceso
        fields = '__all__'
