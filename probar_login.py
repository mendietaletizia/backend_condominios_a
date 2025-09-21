#!/usr/bin/env python
import os
import django
import requests
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

def probar_login():
    print("🔍 Probando login con el backend...")
    
    # URL del endpoint de login
    url = "http://localhost:8000/api/auth/login/"
    
    # Datos de prueba
    data = {
        "username": "jael",
        "password": "password123"
    }
    
    try:
        print(f"📤 Enviando petición a: {url}")
        print(f"📤 Datos: {data}")
        
        response = requests.post(url, json=data)
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login exitoso!")
            response_data = response.json()
            print(f"🎉 Token: {response_data.get('token', 'N/A')}")
            print(f"👤 Usuario: {response_data.get('username', 'N/A')}")
            print(f"📧 Email: {response_data.get('email', 'N/A')}")
            print(f"🔑 Rol: {response_data.get('rol', 'N/A')}")
        else:
            print("❌ Login falló")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data}")
            except:
                print(f"❌ Error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor. ¿Está ejecutándose?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    probar_login()

