#!/usr/bin/env python
"""
Script para crear superusuario usando Django shell
Ejecutar con: python crear_superusuario_shell.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Crear superusuario con datos predefinidos
username = 'admin'
email = 'admin@condominio.com'
password = 'admin123456'

try:
    # Verificar si ya existe
    if User.objects.filter(username=username).exists():
        print(f"El usuario '{username}' ya existe.")
    else:
        # Crear superusuario
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superusuario creado exitosamente!")
        print(f"   Usuario: {username}")
        print(f"   Contraseña: {password}")
        print(f"   Email: {email}")
        
except Exception as e:
    print(f"❌ Error: {e}")
