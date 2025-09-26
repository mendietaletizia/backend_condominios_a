#!/usr/bin/env python
"""
Script para limpiar datos incorrectos en las tablas
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from usuarios.models import Residentes, Persona, Usuario
from comunidad.models import Mascota, Unidad, ResidentesUnidad

def cleanup_data():
    """Limpiar datos incorrectos"""
    print("Iniciando limpieza de datos...")
    
    # 1. Eliminar mascotas huérfanas (sin residente válido)
    mascotas_orphan = Mascota.objects.filter(residente__isnull=True)
    print(f"Eliminando {mascotas_orphan.count()} mascotas huérfanas...")
    mascotas_orphan.delete()
    
    # 2. Eliminar residentes sin persona válida
    residentes_orphan = Residentes.objects.filter(persona__isnull=True)
    print(f"Eliminando {residentes_orphan.count()} residentes huérfanos...")
    residentes_orphan.delete()
    
    # 3. Eliminar relaciones ResidentesUnidad huérfanas
    ru_orphan = ResidentesUnidad.objects.filter(
        id_residente__isnull=True
    ).union(
        ResidentesUnidad.objects.filter(id_unidad__isnull=True)
    )
    print(f"Eliminando {ru_orphan.count()} relaciones huérfanas...")
    ru_orphan.delete()
    
    # 4. Limpiar datos de prueba incorrectos
    # Eliminar residentes de prueba con datos incorrectos
    residentes_test = Residentes.objects.filter(
        persona__nombre__icontains='test'
    ).union(
        Residentes.objects.filter(persona__nombre__icontains='prueba')
    ).union(
        Residentes.objects.filter(persona__nombre__icontains='demo')
    )
    print(f"Eliminando {residentes_test.count()} residentes de prueba...")
    residentes_test.delete()
    
    # 5. Eliminar personas huérfanas
    personas_orphan = Persona.objects.filter(residentes__isnull=True)
    print(f"Eliminando {personas_orphan.count()} personas huérfanas...")
    personas_orphan.delete()
    
    print("Limpieza completada!")
    
    # Mostrar estadísticas finales
    print("\nEstadísticas finales:")
    print(f"- Personas: {Persona.objects.count()}")
    print(f"- Residentes: {Residentes.objects.count()}")
    print(f"- Mascotas: {Mascota.objects.count()}")
    print(f"- Unidades: {Unidad.objects.count()}")
    print(f"- Relaciones ResidentesUnidad: {ResidentesUnidad.objects.count()}")

if __name__ == "__main__":
    cleanup_data()
