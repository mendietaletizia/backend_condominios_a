from rest_framework import serializers
from usuarios.models import Usuario, PlacaInvitado
from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Debe proporcionar username y password")

        try:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Credenciales inválidas")
            if not user.is_active:
                raise serializers.ValidationError("Usuario inactivo")
            data['user'] = user
            return data
        except Exception as e:
            raise serializers.ValidationError(f"Error de autenticación: {str(e)}")

class PlacaInvitadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacaInvitado
        fields = '__all__'
        read_only_fields = ['id', 'fecha_registro']
