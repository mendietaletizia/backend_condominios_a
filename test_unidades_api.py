#!/usr/bin/env python
"""
Script para probar la API de unidades directamente
"""
import requests
import json

def test_unidades_api():
    """Probar la API de unidades"""
    base_url = "http://localhost:8000/api"
    
    # Datos de prueba para crear una unidad
    test_data = {
        "numero_casa": "TEST-001",
        "metros_cuadrados": 85.5,
        "cantidad_residentes": 2,
        "cantidad_mascotas": 1,
        "cantidad_vehiculos": 1
    }
    
    try:
        # Probar GET sin autenticación
        print("🔍 Probando GET /comunidad/unidades/ sin autenticación...")
        response = requests.get(f"{base_url}/comunidad/unidades/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ GET funciona sin autenticación")
        else:
            print(f"❌ GET falló: {response.text}")
        
        # Probar POST sin autenticación
        print("\n🔍 Probando POST /comunidad/unidades/ sin autenticación...")
        response = requests.post(
            f"{base_url}/comunidad/unidades/",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ POST funciona sin autenticación")
        elif response.status_code == 403:
            print("⚠️ POST requiere autenticación (esperado)")
        else:
            print(f"❌ POST falló: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está ejecutándose?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_unidades_api()
