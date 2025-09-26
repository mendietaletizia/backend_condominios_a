#!/usr/bin/env python
"""
Script para probar la API de usuarios
"""
import os
import django
import requests
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

def test_api_usuarios():
    """Probar la API de usuarios"""
    print("=== PROBANDO API DE USUARIOS ===\n")
    
    try:
        # URL de la API
        url = "http://localhost:8000/api/usuarios/"
        
        print(f"Probando URL: {url}")
        
        # Hacer petición GET
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta exitosa. Datos recibidos:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Analizar usuarios
            if isinstance(data, list):
                usuarios = data
            elif isinstance(data, dict) and 'results' in data:
                usuarios = data['results']
            else:
                usuarios = []
            
            print(f"\nTotal de usuarios: {len(usuarios)}")
            
            # Filtrar usuarios residentes
            usuarios_residentes = []
            for usuario in usuarios:
                print(f"\nUsuario: {usuario.get('username', 'N/A')}")
                print(f"Email: {usuario.get('email', 'N/A')}")
                print(f"Rol: {usuario.get('rol', 'N/A')}")
                
                # Verificar si es residente
                rol = usuario.get('rol')
                if isinstance(rol, dict) and rol.get('nombre', '').lower() == 'residente':
                    usuarios_residentes.append(usuario)
                    print("  ✅ Es residente")
                elif isinstance(rol, str) and rol.lower() == 'residente':
                    usuarios_residentes.append(usuario)
                    print("  ✅ Es residente")
                else:
                    print("  ❌ No es residente")
            
            print(f"\nUsuarios residentes encontrados: {len(usuarios_residentes)}")
            for usuario in usuarios_residentes:
                print(f"  - {usuario.get('username')} ({usuario.get('email')})")
                
        else:
            print(f"Error en la API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor. Asegúrate de que el servidor esté ejecutándose en localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_usuarios()
