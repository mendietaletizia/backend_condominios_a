"""
Configuración para la pasarela de pagos - CU22

Este archivo contiene la configuración necesaria para integrar 
con la pasarela de pagos de tu amiga.

INSTRUCCIONES:
1. Copia este archivo a tu archivo de settings.py
2. Reemplaza los valores con los datos reales de la pasarela
3. Asegúrate de que las URLs sean correctas
"""

# Configuración de la pasarela de pagos
PASARELA_CONFIG = {
    # URL base de la API de la pasarela
    'PASARELA_API_URL': 'https://api.pasarela-pago.com',  # Cambiar por la URL real
    
    # Credenciales de la pasarela
    'PASARELA_API_KEY': 'tu_api_key_aqui',  # Obtener de tu amiga
    'PASARELA_MERCHANT_ID': 'tu_merchant_id_aqui',  # Obtener de tu amiga
    'PASARELA_WEBHOOK_SECRET': 'tu_webhook_secret_aqui',  # Para validar webhooks
    
    # URLs de tu sistema
    'BASE_URL': 'https://tu-dominio.com',  # URL de tu backend
    'FRONTEND_URL': 'https://tu-dominio.com',  # URL de tu frontend
}

# Ejemplo de configuración para diferentes entornos
PASARELA_CONFIG_DEV = {
    'PASARELA_API_URL': 'https://sandbox.pasarela-pago.com',
    'PASARELA_API_KEY': 'dev_api_key',
    'PASARELA_MERCHANT_ID': 'dev_merchant_id',
    'PASARELA_WEBHOOK_SECRET': 'dev_webhook_secret',
    'BASE_URL': 'http://localhost:8000',
    'FRONTEND_URL': 'http://localhost:3000',
}

PASARELA_CONFIG_PROD = {
    'PASARELA_API_URL': 'https://api.pasarela-pago.com',
    'PASARELA_API_KEY': 'prod_api_key',
    'PASARELA_MERCHANT_ID': 'prod_merchant_id',
    'PASARELA_WEBHOOK_SECRET': 'prod_webhook_secret',
    'BASE_URL': 'https://tu-dominio.com',
    'FRONTEND_URL': 'https://tu-dominio.com',
}

# Configuración de monedas soportadas
PASARELA_CURRENCIES = ['BOB', 'USD']  # Bolivianos y Dólares

# Configuración de métodos de pago
PASARELA_PAYMENT_METHODS = [
    'credit_card',
    'debit_card', 
    'bank_transfer',
    'digital_wallet'
]

# Configuración de timeouts
PASARELA_TIMEOUTS = {
    'CREATE_PAYMENT': 30,  # segundos
    'VERIFY_PAYMENT': 30,  # segundos
    'WEBHOOK_TIMEOUT': 10,  # segundos
}

# Configuración de reintentos
PASARELA_RETRY_CONFIG = {
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5,  # segundos
    'BACKOFF_FACTOR': 2,
}
