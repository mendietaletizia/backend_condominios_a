from rest_framework import serializers
from usuarios.models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo
)
from django.contrib.auth.hashers import make_password

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rol = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'rol']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def get_rol(self, obj):
        """Determinar el rol del usuario basado en si es empleado o residente"""
        from usuarios.models import Empleado, Residentes
        
        # Verificar si es empleado
        empleado = Empleado.objects.filter(usuario=obj).first()
        if empleado:
            return empleado.cargo
        
        # Verificar si es residente
        residente = Residentes.objects.filter(persona__email=obj.email).first()
        if residente:
            return "Residente"
        
        return "Usuario"

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data and validated_data['password']:
            password = validated_data.pop('password')
            instance.set_password(password)
        elif 'password' in validated_data:
            # Si se envía una contraseña vacía, la removemos
            validated_data.pop('password')
        return super().update(instance, validated_data)


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = '__all__'


class RolPermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolPermiso
        fields = '__all__'


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'

# Serializers para los nuevos modelos
class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'

class AccesoVehicularSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccesoVehicular
        fields = '__all__'

class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita
        fields = '__all__'

class InvitadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitado
        fields = '__all__'

class ReclamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamo
        fields = '__all__'
