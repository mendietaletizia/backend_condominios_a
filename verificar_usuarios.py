#!/usr/bin/env python
"""
Script para verificar usuarios y roles en el sistema
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from usuarios.models import Usuario, Roles
from django.contrib.auth.models import User

def verificar_usuarios():
    """Verificar usuarios y roles en el sistema"""
    print("=== VERIFICACIÓN DE USUARIOS Y ROLES ===\n")
    
    # 1. Verificar roles existentes
    print("1. ROLES DISPONIBLES:")
    roles = Roles.objects.all()
    if roles.exists():
        for rol in roles:
            print(f"   - ID: {rol.id}, Nombre: {rol.nombre}")
    else:
        print("   ❌ No hay roles creados")
    
    print()
    
    # 2. Verificar usuarios del sistema
    print("2. USUARIOS DEL SISTEMA:")
    usuarios = Usuario.objects.all()
    if usuarios.exists():
        for usuario in usuarios:
            rol_info = "Sin rol"
            if usuario.rol:
                rol_info = f"Rol: {usuario.rol.nombre} (ID: {usuario.rol.id})"
            print(f"   - Username: {usuario.username}")
            print(f"     Email: {usuario.email}")
            print(f"     {rol_info}")
            print(f"     Activo: {usuario.is_active}")
            print()
    else:
        print("   ❌ No hay usuarios creados")
    
    print()
    
    # 3. Verificar usuarios con rol residente
    print("3. USUARIOS CON ROL RESIDENTE:")
    usuarios_residentes = Usuario.objects.filter(rol__nombre__iexact='residente')
    if usuarios_residentes.exists():
        for usuario in usuarios_residentes:
            print(f"   - {usuario.username} ({usuario.email})")
    else:
        print("   ❌ No hay usuarios con rol 'residente'")
        print("   💡 Necesitas crear usuarios con rol 'residente' para que aparezcan en el campo 'Usuario Asociado'")
    
    print()
    
    # 4. Crear rol residente si no existe
    if not Roles.objects.filter(nombre__iexact='residente').exists():
        print("4. CREANDO ROL 'RESIDENTE':")
        rol_residente = Roles.objects.create(nombre='residente')
        print(f"   ✅ Rol 'residente' creado con ID: {rol_residente.id}")
    else:
        print("4. ROL 'RESIDENTE' YA EXISTE")
    
    print()
    
    # 5. Sugerencias
    print("5. SUGERENCIAS:")
    if not usuarios_residentes.exists():
        print("   - Crear usuarios con rol 'residente' usando el panel de administración")
        print("   - O crear usuarios programáticamente")
        print("   - Los usuarios con rol 'residente' aparecerán en el campo 'Usuario Asociado'")

if __name__ == "__main__":
    verificar_usuarios()