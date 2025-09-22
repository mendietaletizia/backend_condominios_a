from rest_framework import serializers
from usuarios.models import Residentes, Usuario, Persona, Roles, Permiso, RolPermiso, Empleado, Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo
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
