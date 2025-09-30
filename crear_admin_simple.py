#!/usr/bin/env python
"""
Script simple para crear superusuario
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def crear_admin():
    print("=== Creando Superusuario ===")
    
    username = 'admin'
    email = 'admin@condominio.com'
    password = 'admin123456'
    
    try:
        # Verificar si ya existe
        if User.objects.filter(username=username).exists():
            print(f"El usuario '{username}' ya existe.")
            return
        
        # Crear superusuario
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        print("SUPERUSUARIO CREADO EXITOSAMENTE!")
        print(f"Usuario: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
        print("Puedes acceder al admin en: http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    crear_admin()
