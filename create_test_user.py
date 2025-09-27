#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from usuarios.models import Roles

User = get_user_model()

def create_test_user():
    # Crear usuario de prueba
    username = 'admin'
    email = 'admin@condominio.com'
    password = 'admin123'
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"Usuario {username} ya existe")
    else:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Administrador',
            last_name='Sistema'
        )
        print(f"Usuario {username} creado exitosamente")
    
    # Crear o obtener token
    token, created = Token.objects.get_or_create(user=user)
    if created:
        print(f"Token creado para {username}: {token.key}")
    else:
        print(f"Token existente para {username}: {token.key}")
    
    # Crear rol de administrador si no existe
    rol_admin, created = Roles.objects.get_or_create(
        nombre='administrador'
    )
    
    if created:
        print("Rol administrador creado")
    else:
        print("Rol administrador ya existe")
    
    # Asignar rol al usuario
    user.rol = rol_admin
    user.save()
    print(f"Rol administrador asignado a {username}")
    
    return user, token

if __name__ == '__main__':
    user, token = create_test_user()
    print(f"\n=== CREDENCIALES DE PRUEBA ===")
    print(f"Usuario: {user.username}")
    print(f"Contraseña: admin123")
    print(f"Token: {token.key}")
    print(f"===============================")
