#!/usr/bin/env python
"""
Script para crear un superusuario de Django
Ejecutar con: python crear_superusuario.py
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def crear_superusuario():
    print("=== Crear Superusuario ===")
    
    # Verificar si ya existe un superusuario
    if User.objects.filter(is_superuser=True).exists():
        print("Ya existe un superusuario en el sistema.")
        respuesta = input("¿Deseas crear otro? (s/n): ").lower()
        if respuesta != 's':
            print("Operación cancelada.")
            return
    
    # Solicitar datos del superusuario
    print("\nIngresa los datos del superusuario:")
    username = input("Nombre de usuario: ").strip()
    
    if not username:
        print("Error: El nombre de usuario es requerido.")
        return
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        print(f"Error: El usuario '{username}' ya existe.")
        return
    
    email = input("Email (opcional): ").strip()
    
    # Solicitar contraseña
    while True:
        password = input("Contraseña: ").strip()
        if len(password) < 8:
            print("Error: La contraseña debe tener al menos 8 caracteres.")
            continue
        
        password_confirm = input("Confirmar contraseña: ").strip()
        if password != password_confirm:
            print("Error: Las contraseñas no coinciden.")
            continue
        break
    
    try:
        # Crear el superusuario
        user = User.objects.create_superuser(
            username=username,
            email=email if email else '',
            password=password
        )
        
        print(f"\n✅ Superusuario '{username}' creado exitosamente!")
        print(f"   Usuario: {username}")
        print(f"   Email: {email if email else 'No especificado'}")
        print(f"   Es superusuario: {user.is_superuser}")
        print(f"   Es staff: {user.is_staff}")
        
    except Exception as e:
        print(f"❌ Error al crear el superusuario: {e}")

if __name__ == '__main__':
    try:
        crear_superusuario()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Asegúrate de que Django esté configurado correctamente.")
