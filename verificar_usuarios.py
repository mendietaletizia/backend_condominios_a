#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from usuarios.models import Usuario
from django.contrib.auth.hashers import make_password

def verificar_y_crear_usuarios():
    print("🔍 Verificando usuarios existentes...")
    
    # Listar usuarios existentes
    usuarios = Usuario.objects.all()
    print(f"\n📋 Usuarios existentes ({usuarios.count()}):")
    for usuario in usuarios:
        print(f"  - {usuario.username} (activo: {usuario.is_active}, staff: {usuario.is_staff})")
    
    # Verificar si existe el usuario jael
    jael_user = Usuario.objects.filter(username='jael').first()
    if not jael_user:
        print("\n❌ Usuario 'jael' no existe. Creándolo...")
        jael_user = Usuario.objects.create(
            username='jael',
            email='jael@admin.com',
            first_name='Jael',
            last_name='Administrador',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        jael_user.set_password('password123')
        jael_user.save()
        print("✅ Usuario 'jael' creado exitosamente")
    else:
        print(f"\n✅ Usuario 'jael' existe (activo: {jael_user.is_active})")
        # Verificar contraseña
        if jael_user.check_password('password123'):
            print("✅ Contraseña correcta")
        else:
            print("❌ Contraseña incorrecta, actualizando...")
            jael_user.set_password('password123')
            jael_user.save()
            print("✅ Contraseña actualizada")
    
    # Verificar si existe el usuario residente1
    residente1_user = Usuario.objects.filter(username='residente1').first()
    if not residente1_user:
        print("\n❌ Usuario 'residente1' no existe. Creándolo...")
        residente1_user = Usuario.objects.create(
            username='residente1',
            email='residente1@test.com',
            first_name='Residente',
            last_name='Uno',
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        residente1_user.set_password('password123')
        residente1_user.save()
        print("✅ Usuario 'residente1' creado exitosamente")
    else:
        print(f"\n✅ Usuario 'residente1' existe (activo: {residente1_user.is_active})")
        # Verificar contraseña
        if residente1_user.check_password('password123'):
            print("✅ Contraseña correcta")
        else:
            print("❌ Contraseña incorrecta, actualizando...")
            residente1_user.set_password('password123')
            residente1_user.save()
            print("✅ Contraseña actualizada")
    
    print("\n🎉 Verificación completada!")

if __name__ == "__main__":
    verificar_y_crear_usuarios()

