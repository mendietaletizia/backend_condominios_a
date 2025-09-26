#!/usr/bin/env python3
"""
Script para crear unidades básicas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from comunidad.models import Unidad

def crear_unidades():
    """Crear unidades básicas"""
    print("🏠 Creando unidades básicas...")
    
    unidades_data = [
        {'numero_casa': 'A-101', 'metros_cuadrados': 85.5, 'cantidad_residentes': 0, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 0},
        {'numero_casa': 'A-102', 'metros_cuadrados': 95.0, 'cantidad_residentes': 0, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 0},
        {'numero_casa': 'B-201', 'metros_cuadrados': 75.0, 'cantidad_residentes': 0, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 0},
        {'numero_casa': 'B-202', 'metros_cuadrados': 90.0, 'cantidad_residentes': 0, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 0},
        {'numero_casa': 'C-301', 'metros_cuadrados': 110.0, 'cantidad_residentes': 0, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 0},
    ]
    
    for unidad_data in unidades_data:
        unidad, created = Unidad.objects.get_or_create(
            numero_casa=unidad_data['numero_casa'],
            defaults=unidad_data
        )
        if created:
            print(f"✅ Unidad creada: {unidad.numero_casa}")
        else:
            print(f"ℹ️  Unidad ya existe: {unidad.numero_casa}")
    
    print(f"\n🎉 Se crearon {len(unidades_data)} unidades básicas!")

if __name__ == "__main__":
    crear_unidades()
