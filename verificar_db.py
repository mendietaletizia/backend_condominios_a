#!/usr/bin/env python
"""
Script para verificar la conexión a la base de datos
Ejecutar con: python verificar_db.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def verificar_conexion():
    print("=== Verificando Conexión a la Base de Datos ===")
    
    try:
        # Probar la conexión
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print("✅ Conexión a la base de datos exitosa!")
        print(f"   Base de datos: {connection.settings_dict['NAME']}")
        print(f"   Host: {connection.settings_dict['HOST']}")
        print(f"   Puerto: {connection.settings_dict['PORT']}")
        
        # Verificar si las tablas existen
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
        print(f"\n📋 Tablas encontradas ({len(tables)}):")
        for table in tables[:10]:  # Mostrar solo las primeras 10
            print(f"   - {table[0]}")
        
        if len(tables) > 10:
            print(f"   ... y {len(tables) - 10} más")
            
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\n🔧 Posibles soluciones:")
        print("   1. Verifica que PostgreSQL esté ejecutándose")
        print("   2. Verifica las credenciales en tu archivo .env")
        print("   3. Verifica que la base de datos exista")
        print("   4. Verifica la URL de conexión")
        return False

def aplicar_migraciones():
    print("\n=== Aplicando Migraciones ===")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migraciones aplicadas exitosamente!")
        return True
    except Exception as e:
        print(f"❌ Error al aplicar migraciones: {e}")
        return False

if __name__ == '__main__':
    try:
        if verificar_conexion():
            aplicar_migraciones()
            print("\n🎉 Base de datos lista para usar!")
        else:
            print("\n❌ Hay problemas con la base de datos.")
            
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
