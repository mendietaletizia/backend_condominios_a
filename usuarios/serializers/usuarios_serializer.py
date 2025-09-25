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

    class Meta:
        model = Residentes
        fields = '__all__'

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
    class Meta:
        model = Empleado
        fields = ['id', 'persona', 'usuario', 'cargo']

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
