#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import Roles

User = get_user_model()

def crear_usuarios_prueba():
    # Contraseña común para todos los usuarios de prueba
    password = 'admin123'
    
    # Usuarios de prueba
    usuarios_prueba = [
        {
            'username': 'admin',
            'email': 'admin@condominio.com',
            'rol': 'administrador',
            'first_name': 'Admin',
            'last_name': 'Sistema'
        },
        {
            'username': 'residente1',
            'email': 'residente1@condominio.com',
            'rol': 'residente',
            'first_name': 'Juan',
            'last_name': 'Pérez'
        },
        {
            'username': 'empleado1',
            'email': 'empleado1@condominio.com',
            'rol': 'empleado',
            'first_name': 'María',
            'last_name': 'González'
        },
        {
            'username': 'seguridad1',
            'email': 'seguridad1@condominio.com',
            'rol': 'seguridad',
            'first_name': 'Carlos',
            'last_name': 'López'
        }
    ]
    
    print("=== CREANDO USUARIOS DE PRUEBA ===")
    print(f"Contraseña para todos: {password}")
    print("=" * 40)
    
    for user_data in usuarios_prueba:
        username = user_data['username']
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            # Actualizar contraseña
            user.set_password(password)
            user.save()
            print(f"✅ Usuario {username} actualizado con nueva contraseña")
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            print(f"✅ Usuario {username} creado exitosamente")
        
        # Obtener o crear rol
        rol, created = Roles.objects.get_or_create(nombre=user_data['rol'])
        if created:
            print(f"   Rol {user_data['rol']} creado")
        
        # Asignar rol al usuario
        user.rol = rol
        user.save()
        print(f"   Rol {user_data['rol']} asignado")
        print()
    
    print("=== CREDENCIALES DE PRUEBA ===")
    print("Usuario: admin, Contraseña: admin123 (Administrador)")
    print("Usuario: residente1, Contraseña: admin123 (Residente)")
    print("Usuario: empleado1, Contraseña: admin123 (Empleado)")
    print("Usuario: seguridad1, Contraseña: admin123 (Seguridad)")
    print("=" * 40)

if __name__ == '__main__':
    crear_usuarios_prueba()

