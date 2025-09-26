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
    ru_orphan1 = ResidentesUnidad.objects.filter(id_residente__isnull=True)
    ru_orphan2 = ResidentesUnidad.objects.filter(id_unidad__isnull=True)
    total_orphan = ru_orphan1.count() + ru_orphan2.count()
    print(f"Eliminando {total_orphan} relaciones huérfanas...")
    ru_orphan1.delete()
    ru_orphan2.delete()
    
    # 4. Limpiar datos de prueba incorrectos
    # Eliminar residentes de prueba con datos incorrectos
    residentes_test1 = Residentes.objects.filter(persona__nombre__icontains='test')
    residentes_test2 = Residentes.objects.filter(persona__nombre__icontains='prueba')
    residentes_test3 = Residentes.objects.filter(persona__nombre__icontains='demo')
    total_test = residentes_test1.count() + residentes_test2.count() + residentes_test3.count()
    print(f"Eliminando {total_test} residentes de prueba...")
    residentes_test1.delete()
    residentes_test2.delete()
    residentes_test3.delete()
    
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
