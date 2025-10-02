#!/usr/bin/env python3
"""
Script para crear datos de prueba para el sistema de acceso vehicular
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.utils import timezone
from usuarios.models import (
    PlacaVehiculo, PlacaInvitado, ConfiguracionAcceso,
    Residentes, Persona, Usuario, Roles
)

def crear_configuracion_acceso():
    """Crear configuración por defecto del sistema de acceso"""
    print("🔧 Creando configuración de acceso...")
    
    config, created = ConfiguracionAcceso.objects.get_or_create(
        pk=1,
        defaults={
            'umbral_confianza_placa': 75.0,
            'umbral_confianza_vehiculo': 80.0,
            'tiempo_max_procesamiento': 30.0,
            'notificar_accesos_denegados': True,
            'notificar_accesos_no_reconocidos': True,
            'notificar_mantenimiento': True,
            'camaras_activas': 1,
            'fps_captura': 15,
            'dias_retencion_imagenes': 30,
            'dias_retencion_registros': 90
        }
    )
    
    if created:
        print("✅ Configuración de acceso creada")
    else:
        print("ℹ️ Configuración de acceso ya existe")
    
    return config

def crear_usuario_admin():
    """Crear usuario administrador si no existe"""
    print("👤 Verificando usuario administrador...")
    
    # Crear rol de administrador si no existe
    rol_admin, created = Roles.objects.get_or_create(
        nombre='Administrador'
    )
    
    # Verificar si existe un usuario administrador
    admin_user = Usuario.objects.filter(is_superuser=True).first()
    if not admin_user:
        # Crear persona para el admin
        persona_admin, created = Persona.objects.get_or_create(
            ci='00000000',
            defaults={
                'nombre': 'Administrador Sistema',
                'telefono': '000000000',
                'email': 'admin@condominio.com'
            }
        )
        
        # Crear usuario admin
        admin_user = Usuario.objects.create_superuser(
            username='admin',
            email='admin@condominio.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        admin_user.rol = rol_admin
        admin_user.save()
        print("✅ Usuario administrador creado: admin/admin123")
    else:
        print("ℹ️ Usuario administrador ya existe")
    
    return admin_user

def crear_residentes_prueba():
    """Crear residentes de prueba"""
    print("🏠 Creando residentes de prueba...")
    
    residentes_data = [
        {
            'ci': '12345678',
            'nombre': 'Juan Carlos Pérez González',
            'telefono': '123456789',
            'email': 'juan.perez@email.com',
            'username': 'juan.perez'
        },
        {
            'ci': '87654321',
            'nombre': 'María Elena Rodríguez López',
            'telefono': '987654321',
            'email': 'maria.rodriguez@email.com',
            'username': 'maria.rodriguez'
        },
        {
            'ci': '11223344',
            'nombre': 'Carlos Alberto Gómez Martínez',
            'telefono': '112233445',
            'email': 'carlos.gomez@email.com',
            'username': 'carlos.gomez'
        }
    ]
    
    residentes_creados = []
    
    for data in residentes_data:
        # Crear persona
        persona, created = Persona.objects.get_or_create(
            ci=data['ci'],
            defaults={
                'nombre': data['nombre'],
                'telefono': data['telefono'],
                'email': data['email']
            }
        )
        
        # Crear usuario
        usuario, created = Usuario.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['nombre'].split()[0],
                'last_name': ' '.join(data['nombre'].split()[1:]) if len(data['nombre'].split()) > 1 else '',
                'is_active': True
            }
        )
        
        if created:
            usuario.set_password('123456')
            usuario.save()
        
        # Crear residente
        residente, created = Residentes.objects.get_or_create(
            persona=persona,
            defaults={'usuario': usuario}
        )
        
        residentes_creados.append(residente)
        
        if created:
            print(f"✅ Residente creado: {persona.nombre}")
        else:
            print(f"ℹ️ Residente ya existe: {persona.nombre}")
    
    return residentes_creados

def crear_placas_residentes(residentes):
    """Crear placas de vehículos para residentes"""
    print("🚗 Creando placas de vehículos de residentes...")
    
    placas_data = [
        # Residente 1 - Juan Carlos
        {'placa': 'ABC123', 'marca': 'Toyota', 'modelo': 'Corolla', 'color': 'Blanco'},
        {'placa': 'XYZ789', 'marca': 'Honda', 'modelo': 'Civic', 'color': 'Negro'},
        
        # Residente 2 - María Elena  
        {'placa': 'DEF456', 'marca': 'Nissan', 'modelo': 'Sentra', 'color': 'Gris'},
        {'placa': 'GHI012', 'marca': 'Chevrolet', 'modelo': 'Spark', 'color': 'Rojo'},
        
        # Residente 3 - Carlos Alberto
        {'placa': 'JKL345', 'marca': 'Hyundai', 'modelo': 'Accent', 'color': 'Azul'},
    ]
    
    placas_creadas = []
    
    for i, placa_data in enumerate(placas_data):
        residente = residentes[i % len(residentes)]  # Distribuir entre residentes
        
        placa_obj, created = PlacaVehiculo.objects.get_or_create(
            placa=placa_data['placa'],
            defaults={
                'residente': residente,
                'marca': placa_data['marca'],
                'modelo': placa_data['modelo'],
                'color': placa_data['color'],
                'activo': True
            }
        )
        
        placas_creadas.append(placa_obj)
        
        if created:
            print(f"✅ Placa creada: {placa_data['placa']} - {placa_data['marca']} {placa_data['modelo']} ({residente.persona.nombre})")
        else:
            print(f"ℹ️ Placa ya existe: {placa_data['placa']}")
    
    return placas_creadas

def crear_placas_invitados(residentes):
    """Crear placas de invitados"""
    print("👥 Creando placas de invitados...")
    
    invitados_data = [
        {
            'placa': 'INV001',
            'marca': 'Ford',
            'modelo': 'Fiesta',
            'color': 'Verde',
            'nombre_visitante': 'Ana García',
            'ci_visitante': '55667788',
            'dias_vigencia': 7
        },
        {
            'placa': 'INV002',
            'marca': 'Kia',
            'modelo': 'Rio',
            'color': 'Amarillo',
            'nombre_visitante': 'Pedro Martínez',
            'ci_visitante': '99887766',
            'dias_vigencia': 3
        },
        {
            'placa': 'VIS123',
            'marca': 'Mazda',
            'modelo': '3',
            'color': 'Plateado',
            'nombre_visitante': 'Laura Sánchez',
            'ci_visitante': '44556677',
            'dias_vigencia': 14
        }
    ]
    
    invitados_creados = []
    
    for i, invitado_data in enumerate(invitados_data):
        residente = residentes[i % len(residentes)]  # Distribuir entre residentes
        
        placa_obj, created = PlacaInvitado.objects.get_or_create(
            placa=invitado_data['placa'],
            defaults={
                'residente': residente,
                'marca': invitado_data['marca'],
                'modelo': invitado_data['modelo'],
                'color': invitado_data['color'],
                'nombre_visitante': invitado_data['nombre_visitante'],
                'ci_visitante': invitado_data['ci_visitante'],
                'fecha_autorizacion': timezone.now(),
                'fecha_vencimiento': timezone.now() + timedelta(days=invitado_data['dias_vigencia']),
                'activo': True
            }
        )
        
        invitados_creados.append(placa_obj)
        
        if created:
            print(f"✅ Invitado creado: {invitado_data['placa']} - {invitado_data['nombre_visitante']} (autorizado por {residente.persona.nombre})")
        else:
            print(f"ℹ️ Invitado ya existe: {invitado_data['placa']}")
    
    return invitados_creados

def mostrar_resumen():
    """Mostrar resumen de datos creados"""
    print("\n📊 RESUMEN DE DATOS CREADOS")
    print("=" * 50)
    
    total_residentes = PlacaVehiculo.objects.filter(activo=True).count()
    total_invitados = PlacaInvitado.objects.filter(
        activo=True,
        fecha_vencimiento__gte=timezone.now()
    ).count()
    
    print(f"🚗 Placas de residentes: {total_residentes}")
    print(f"👥 Placas de invitados: {total_invitados}")
    print(f"📋 Total placas: {total_residentes + total_invitados}")
    
    print("\n🚗 PLACAS DE RESIDENTES:")
    for placa in PlacaVehiculo.objects.filter(activo=True):
        print(f"  - {placa.placa}: {placa.marca} {placa.modelo} ({placa.residente.persona.nombre})")
    
    print("\n👥 PLACAS DE INVITADOS:")
    for placa in PlacaInvitado.objects.filter(activo=True, fecha_vencimiento__gte=timezone.now()):
        print(f"  - {placa.placa}: {placa.nombre_visitante} (autorizado por {placa.residente.persona.nombre})")
    
    print("\n🧪 PLACAS PARA PRUEBAS:")
    print("  ✅ Autorizadas: ABC123, XYZ789, DEF456, INV001, INV002")
    print("  ❌ No registradas: NOEXISTE, ZZZ999, TEST123")

def main():
    """Función principal"""
    print("🚗 CREANDO DATOS DE PRUEBA PARA SISTEMA DE ACCESO")
    print("=" * 60)
    
    try:
        # 1. Crear configuración
        crear_configuracion_acceso()
        
        # 2. Crear usuario admin
        crear_usuario_admin()
        
        # 3. Crear residentes
        residentes = crear_residentes_prueba()
        
        # 4. Crear placas de residentes
        crear_placas_residentes(residentes)
        
        # 5. Crear placas de invitados
        crear_placas_invitados(residentes)
        
        # 6. Mostrar resumen
        mostrar_resumen()
        
        print("\n✅ DATOS DE PRUEBA CREADOS EXITOSAMENTE")
        print("\n📝 INSTRUCCIONES:")
        print("1. Inicia el servidor: python manage.py runserver")
        print("2. Inicia el frontend: npm run dev")
        print("3. Accede como admin: admin/admin123")
        print("4. Ve a 'Control de Acceso Vehicular'")
        print("5. Prueba con placas: ABC123 (autorizada), NOEXISTE (pendiente)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
