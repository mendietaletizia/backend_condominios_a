from rest_framework import serializers
from usuarios.models import Usuario
from django.contrib.auth.hashers import check_password

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = Usuario.objects.get(username=data['username'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no existe")

        if not check_password(data['password'], user.password):
            raise serializers.ValidationError("Contraseña incorrecta")
        
        data['user'] = user
        return data
