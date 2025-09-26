#!/usr/bin/env python3
"""
Script para probar la API de unidades y obtener un token válido
"""

import requests
import json

# URL base
BASE_URL = "http://localhost:8000/api"

def test_login():
    """Probar login y obtener token"""
    # Probar diferentes contraseñas comunes
    passwords = ["admin123", "admin", "123456", "password", "letiii", "letiii123"]
    
    for password in passwords:
        login_data = {
            "username": "letiii",
            "password": password
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
            if response.status_code == 200:
                token = response.json().get('token')
                print(f"✅ Login exitoso con contraseña '{password}'. Token: {token[:20]}...")
                return token
            else:
                print(f"❌ Contraseña '{password}' falló: {response.status_code}")
        except Exception as e:
            print(f"❌ Error de conexión con contraseña '{password}': {e}")
    
    print("❌ No se pudo hacer login con ninguna contraseña")
    return None

def test_unidades_api(token):
    """Probar la API de unidades"""
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/comunidad/unidades/", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Unidades obtenidas. Tipo de datos: {type(data)}")
            if isinstance(data, list):
                print(f"   - Array con {len(data)} elementos")
            elif isinstance(data, dict):
                print(f"   - Objeto con keys: {list(data.keys())}")
                if 'results' in data:
                    print(f"   - Results array con {len(data['results'])} elementos")
            return True
        else:
            print(f"❌ Error al obtener unidades: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_residentes_api(token):
    """Probar la API de residentes"""
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/usuarios/residentes/", headers=headers)
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Residentes obtenidos. Tipo de datos: {type(data)}")
            if isinstance(data, list):
                print(f"   - Array con {len(data)} elementos")
            elif isinstance(data, dict):
                print(f"   - Objeto con keys: {list(data.keys())}")
                if 'results' in data:
                    print(f"   - Results array con {len(data['results'])} elementos")
            return True
        else:
            print(f"❌ Error al obtener residentes: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    print("🔍 Probando APIs del CU5...")
    print("=" * 50)
    
    # Probar login
    token = test_login()
    if not token:
        print("❌ No se pudo obtener token. Verifique credenciales.")
        return
    
    # Probar APIs
    print("\n🏠 Probando API de unidades...")
    test_unidades_api(token)
    
    print("\n👥 Probando API de residentes...")
    test_residentes_api(token)

if __name__ == "__main__":
    main()
