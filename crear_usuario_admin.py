#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from usuarios.models import Usuario

def crear_usuario_admin():
    try:
        # Verificar si ya existe
        if Usuario.objects.filter(username='admin').exists():
            print("El usuario admin ya existe")
            return
        
        # Crear usuario administrador
        usuario = Usuario.objects.create_user(
            username='admin',
            email='admin@condominio.com',
            password='admin123',
            rol='administrador'
        )
        
        print("✅ Usuario admin creado exitosamente")
        print(f"   Usuario: admin")
        print(f"   Contraseña: admin123")
        print(f"   Rol: administrador")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")

if __name__ == "__main__":
    crear_usuario_admin()
