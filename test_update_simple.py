#!/usr/bin/env python3
"""
Script simple para probar la actualización de comunicados
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
NOTIFICACIONES_URL = f"{BASE_URL}/api/comunidad/notificaciones/"

def test_update():
    """Probar actualización de comunicado"""
    
    # 1. Login
    login_data = {"username": "admin", "password": "password123"}
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code != 200:
        print(f"Error login: {response.status_code} - {response.text}")
        return
    
    token = response.json().get('access')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # 2. Crear comunicado
    comunicado_data = {
        "titulo": "Comunicado Test",
        "contenido": "Contenido de prueba",
        "tipo": "Comunicado",
        "destinatarios": {"residentes": True, "empleados": False, "seguridad": False}
    }
    
    response = requests.post(NOTIFICACIONES_URL, json=comunicado_data, headers=headers)
    if response.status_code != 201:
        print(f"Error creando: {response.status_code} - {response.text}")
        return
    
    comunicado_id = response.json()['id']
    print(f"Comunicado creado: ID {comunicado_id}")
    
    # 3. Actualizar comunicado
    update_data = {
        "titulo": "Comunicado Actualizado",
        "contenido": "Contenido actualizado",
        "tipo": "Comunicado",
        "destinatarios": {"residentes": True, "empleados": True, "seguridad": False}
    }
    
    response = requests.put(f"{NOTIFICACIONES_URL}{comunicado_id}/", json=update_data, headers=headers)
    print(f"Update response: {response.status_code}")
    print(f"Update data: {response.text}")
    
    if response.status_code == 200:
        print("SUCCESS: Comunicado actualizado correctamente")
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
    
    # 4. Eliminar comunicado
    response = requests.delete(f"{NOTIFICACIONES_URL}{comunicado_id}/", headers=headers)
    print(f"Delete response: {response.status_code}")

if __name__ == "__main__":
    test_update()
