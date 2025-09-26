#!/usr/bin/env python3
"""
Script para probar el frontend con autenticación
"""

import requests
import json

# URL base
BASE_URL = "http://localhost:8000/api"

def get_token():
    """Obtener token de autenticación"""
    login_data = {
        "username": "letiii",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Token obtenido: {token[:20]}...")
            return token
        else:
            print(f"❌ Error en login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_frontend_apis(token):
    """Probar las APIs que usa el frontend"""
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Probar las mismas APIs que usa el frontend
    apis_to_test = [
        "/usuarios/residentes/",
        "/comunidad/unidades/",
        "/usuarios/usuario/"  # Para usuarios residentes
    ]
    
    for api in apis_to_test:
        try:
            response = requests.get(f"{BASE_URL}{api}", headers=headers)
            print(f"\n🔍 Probando {api}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'results' in data:
                    print(f"✅ Datos paginados: {len(data['results'])} elementos")
                elif isinstance(data, list):
                    print(f"✅ Array directo: {len(data)} elementos")
                else:
                    print(f"✅ Otro formato: {type(data)}")
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

def main():
    print("🔍 Probando APIs del frontend...")
    print("=" * 50)
    
    token = get_token()
    if not token:
        print("❌ No se pudo obtener token")
        return
    
    test_frontend_apis(token)

if __name__ == "__main__":
    main()
