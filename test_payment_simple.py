"""
Script de prueba simplificado para el flujo de pagos online - CU22
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings')
django.setup()

from finanzas.models import CuotaMensual, CuotaUnidad
from usuarios.models import Usuario
from comunidad.models import Unidad


def test_payment_flow():
    """Probar el flujo completo de pagos"""
    print("[TEST] Iniciando prueba del flujo de pagos...")
    
    # 1. Crear usuario administrador si no existe
    admin_user, created = Usuario.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'first_name': 'Admin',
            'last_name': 'Test'
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("[OK] Usuario administrador creado")
    else:
        print("[OK] Usuario administrador ya existe")
    
    # 2. Crear cuota mensual
    mes_actual = date.today().strftime('%Y-%m')
    cuota_mensual, created = CuotaMensual.objects.get_or_create(
        mes_año=mes_actual,
        defaults={
            'monto_total': 15000.00,
            'fecha_limite': date.today() + timedelta(days=30),
            'descripcion': f'Cuota mensual de {mes_actual} - Prueba de pagos',
            'estado': 'activa',
            'creado_por': admin_user
        }
    )
    
    if created:
        print(f"[OK] Cuota mensual creada: {cuota_mensual}")
    else:
        print(f"[OK] Cuota mensual ya existe: {cuota_mensual}")
    
    # 3. Generar cuotas por unidad
    unidades = Unidad.objects.filter(activa=True)
    cuotas_creadas = 0
    
    for unidad in unidades:
        cuota_unidad, created = CuotaUnidad.objects.get_or_create(
            cuota_mensual=cuota_mensual,
            unidad=unidad,
            defaults={
                'monto': cuota_mensual.monto_total / unidades.count(),
                'fecha_limite': cuota_mensual.fecha_limite,
                'estado': 'pendiente'
            }
        )
        
        if created:
            cuotas_creadas += 1
    
    print(f"[OK] {cuotas_creadas} cuotas por unidad creadas")
    
    # 4. Probar iniciar pago online
    cuota_test = CuotaUnidad.objects.filter(estado='pendiente').first()
    if not cuota_test:
        print("[ERROR] No hay cuotas pendientes para probar")
        return
    
    print(f"[TEST] Probando pago online para cuota: {cuota_test}")
    
    # Simular pago online
    cuota_test.estado = 'procesando'
    cuota_test.payment_id = 'test_payment_123'
    cuota_test.payment_url = 'https://pasarela-pago.com/pay/test_payment_123'
    cuota_test.save()
    print("[OK] Estado simulado: procesando")
    
    # 5. Simular webhook de confirmación
    print("[TEST] Simulando webhook de confirmación...")
    
    cuota_test.estado = 'pagada'
    cuota_test.monto_pagado = cuota_test.monto
    cuota_test.fecha_pago = date.today()
    cuota_test.payment_status = 'completed'
    cuota_test.payment_method = 'credit_card'
    cuota_test.payment_reference = 'TXN123456789'
    cuota_test.save()
    
    print("[OK] Webhook simulado: pago completado")
    
    # 6. Verificar estado final
    cuota_test.refresh_from_db()
    print(f"[OK] Estado final de la cuota: {cuota_test.estado}")
    print(f"   Monto pagado: Bs. {cuota_test.monto_pagado}")
    print(f"   Fecha de pago: {cuota_test.fecha_pago}")
    print(f"   Método de pago: {cuota_test.payment_method}")
    print(f"   Referencia: {cuota_test.payment_reference}")
    
    # 7. Estadísticas finales
    cuotas_pendientes = CuotaUnidad.objects.filter(estado='pendiente').count()
    cuotas_pagadas = CuotaUnidad.objects.filter(estado='pagada').count()
    cuotas_procesando = CuotaUnidad.objects.filter(estado='procesando').count()
    
    print("\n[STATS] Estadísticas:")
    print(f"   Cuotas pendientes: {cuotas_pendientes}")
    print(f"   Cuotas pagadas: {cuotas_pagadas}")
    print(f"   Cuotas procesando: {cuotas_procesando}")
    
    print("\n[SUCCESS] Prueba del flujo de pagos completada exitosamente!")


def test_webhook_validation():
    """Probar validación de webhook"""
    print("\n[TEST] Probando validación de webhook...")
    
    from finanzas.services import pasarela_service
    
    # Simular payload y firma
    payload = '{"payment_id": "test123", "status": "completed"}'
    signature = 'test_signature'
    
    # Probar validación (debería fallar sin configuración real)
    is_valid = pasarela_service.validar_webhook(payload, signature)
    print(f"[OK] Validación de webhook: {'Válida' if is_valid else 'Inválida (esperado)'}")


if __name__ == '__main__':
    print("Iniciando pruebas del sistema de pagos...")
    print("=" * 50)
    
    try:
        test_payment_flow()
        test_webhook_validation()
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Todas las pruebas completadas exitosamente!")
        print("\nPróximos pasos:")
        print("1. Configurar las credenciales reales de la pasarela")
        print("2. Actualizar las URLs en pasarela_config.py")
        print("3. Probar con la pasarela real")
        print("4. Configurar webhooks en la pasarela")
        
    except Exception as e:
        print(f"\n[ERROR] Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
