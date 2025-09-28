#!/usr/bin/env python3
"""
Script para probar la funcionalidad de actualización de comunicados
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
NOTIFICACIONES_URL = f"{BASE_URL}/api/comunidad/notificaciones/"

def get_token():
    """Obtener token de autenticación"""
    login_data = {
        "username": "test",
        "password": "password123"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Error de login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def test_create_comunicado(token):
    """Crear un comunicado de prueba"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    comunicado_data = {
        "titulo": "Comunicado de Prueba",
        "contenido": "Este es un comunicado de prueba para verificar la funcionalidad",
        "tipo": "Comunicado",
        "destinatarios": {
            "residentes": True,
            "empleados": False,
            "seguridad": True
        }
    }
    
    try:
        response = requests.post(NOTIFICACIONES_URL, json=comunicado_data, headers=headers)
        if response.status_code == 201:
            comunicado = response.json()
            print(f"OK: Comunicado creado ID {comunicado['id']}")
            return comunicado['id']
        else:
            print(f"ERROR: Error creando comunicado {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Error de conexion {e}")
        return None

def test_update_comunicado(token, comunicado_id):
    """Actualizar el comunicado creado"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    update_data = {
        "titulo": "Comunicado Actualizado",
        "contenido": "Este comunicado ha sido actualizado correctamente",
        "tipo": "Comunicado",
        "destinatarios": {
            "residentes": True,
            "empleados": True,
            "seguridad": False
        }
    }
    
    try:
        response = requests.put(f"{NOTIFICACIONES_URL}{comunicado_id}/", json=update_data, headers=headers)
        if response.status_code == 200:
            comunicado = response.json()
            print(f"OK: Comunicado actualizado ID {comunicado['id']}")
            print(f"   Titulo: {comunicado['titulo']}")
            print(f"   Destinatarios: {comunicado['destinatarios']}")
            return True
        else:
            print(f"ERROR: Error actualizando comunicado {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error de conexion {e}")
        return False

def test_delete_comunicado(token, comunicado_id):
    """Eliminar el comunicado"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.delete(f"{NOTIFICACIONES_URL}{comunicado_id}/", headers=headers)
        if response.status_code == 204:
            print(f"OK: Comunicado eliminado ID {comunicado_id}")
            return True
        else:
            print(f"ERROR: Error eliminando comunicado {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error de conexion {e}")
        return False

def main():
    print("Probando funcionalidad CRUD de comunicados...")
    
    # Obtener token
    token = get_token()
    if not token:
        print("ERROR: No se pudo obtener el token de autenticacion")
        return
    
    print("OK: Token obtenido correctamente")
    
    # Crear comunicado
    comunicado_id = test_create_comunicado(token)
    if not comunicado_id:
        print("ERROR: No se pudo crear el comunicado")
        return
    
    # Actualizar comunicado
    if test_update_comunicado(token, comunicado_id):
        print("OK: Actualizacion exitosa")
    else:
        print("ERROR: Error en la actualizacion")
    
    # Eliminar comunicado
    if test_delete_comunicado(token, comunicado_id):
        print("OK: Eliminacion exitosa")
    else:
        print("ERROR: Error en la eliminacion")
    
    print("\nPrueba completada!")

if __name__ == "__main__":
    main()
