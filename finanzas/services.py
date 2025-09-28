"""
Servicios para integración con pasarela de pagos - CU22
"""
import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PasarelaPagosService:
    """
    Servicio para integrar con la pasarela de pagos externa
    """
    
    def __init__(self):
        # Configuración de la pasarela de pagos
        self.api_url = getattr(settings, 'PASARELA_API_URL', 'https://api.pasarela-pago.com')
        self.api_key = getattr(settings, 'PASARELA_API_KEY', '')
        self.merchant_id = getattr(settings, 'PASARELA_MERCHANT_ID', '')
        self.webhook_secret = getattr(settings, 'PASARELA_WEBHOOK_SECRET', '')
        
        # Headers para las peticiones
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Merchant-ID': self.merchant_id
        }
    
    def crear_pago(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un pago en la pasarela externa
        
        Args:
            payment_data: Datos del pago
                - payment_id: ID único del pago
                - amount: Monto a pagar
                - currency: Moneda (BOB)
                - description: Descripción del pago
                - customer_info: Información del cliente
                - callback_url: URL de callback para webhook
                - return_url: URL de retorno exitoso
                - cancel_url: URL de cancelación
        
        Returns:
            Dict con la respuesta de la pasarela
        """
        try:
            # Preparar datos para la pasarela
            pasarela_data = {
                'merchant_id': self.merchant_id,
                'payment_id': payment_data['payment_id'],
                'amount': payment_data['amount'],
                'currency': payment_data.get('currency', 'BOB'),
                'description': payment_data['description'],
                'customer': {
                    'name': payment_data['customer_info']['name'],
                    'email': payment_data['customer_info']['email']
                },
                'webhook_url': self._build_webhook_url(payment_data['callback_url']),
                'return_url': self._build_return_url(payment_data['return_url']),
                'cancel_url': self._build_return_url(payment_data['cancel_url']),
                'metadata': {
                    'condominio': 'Sistema de Gestión de Condominio',
                    'tipo': 'cuota_mensual'
                }
            }
            
            # Realizar petición a la pasarela
            response = requests.post(
                f"{self.api_url}/payments",
                json=pasarela_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Pago creado exitosamente en pasarela: {payment_data['payment_id']}")
                return {
                    'success': True,
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('payment_id'),
                    'status': result.get('status', 'pending')
                }
            else:
                logger.error(f"Error creando pago en pasarela: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Error de la pasarela: {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con pasarela: {e}")
            return {
                'success': False,
                'error': 'Error de conexión con la pasarela',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Error inesperado creando pago: {e}")
            return {
                'success': False,
                'error': 'Error inesperado',
                'details': str(e)
            }
    
    def verificar_pago(self, payment_id: str) -> Dict[str, Any]:
        """
        Verificar el estado de un pago en la pasarela
        
        Args:
            payment_id: ID del pago a verificar
        
        Returns:
            Dict con el estado del pago
        """
        try:
            response = requests.get(
                f"{self.api_url}/payments/{payment_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': result.get('status'),
                    'payment_method': result.get('payment_method'),
                    'reference': result.get('reference'),
                    'amount': result.get('amount')
                }
            else:
                logger.error(f"Error verificando pago: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Error verificando pago: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error verificando pago {payment_id}: {e}")
            return {
                'success': False,
                'error': 'Error verificando pago',
                'details': str(e)
            }
    
    def validar_webhook(self, payload: str, signature: str) -> bool:
        """
        Validar la firma del webhook de la pasarela
        
        Args:
            payload: Cuerpo del webhook
            signature: Firma enviada por la pasarela
        
        Returns:
            True si la firma es válida
        """
        try:
            import hmac
            import hashlib
            
            # Generar firma esperada
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparar firmas
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validando webhook: {e}")
            return False
    
    def _build_webhook_url(self, callback_path: str) -> str:
        """Construir URL completa del webhook"""
        base_url = getattr(settings, 'BASE_URL', 'https://tu-dominio.com')
        return f"{base_url}{callback_path}"
    
    def _build_return_url(self, return_path: str) -> str:
        """Construir URL completa de retorno"""
        base_url = getattr(settings, 'FRONTEND_URL', 'https://tu-dominio.com')
        return f"{base_url}{return_path}"


class NotificacionPagoService:
    """
    Servicio para enviar notificaciones de pagos
    """
    
    @staticmethod
    def crear_notificacion_pago_exitoso(cuota_unidad):
        """
        Crear notificación de pago exitoso
        """
        try:
            from comunidad.services import NotificacionService
            
            # Obtener información del residente
            unidad = cuota_unidad.unidad
            residente = None
            
            try:
                from usuarios.models import Residentes
                residente = Residentes.objects.get(unidad=unidad)
            except:
                pass
            
            # Crear notificación
            titulo = f"Pago Confirmado - Cuota {cuota_unidad.cuota_mensual.mes_año}"
            mensaje = f"Su pago de Bs. {cuota_unidad.monto} ha sido confirmado exitosamente."
            
            if residente and residente.usuario:
                NotificacionService.crear_notificacion(
                    usuario=residente.usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo='pago_exitoso'
                )
            
            logger.info(f"Notificación de pago exitoso enviada para cuota {cuota_unidad.id}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago: {e}")
    
    @staticmethod
    def crear_notificacion_pago_fallido(cuota_unidad, motivo=""):
        """
        Crear notificación de pago fallido
        """
        try:
            from comunidad.services import NotificacionService
            
            # Obtener información del residente
            unidad = cuota_unidad.unidad
            residente = None
            
            try:
                from usuarios.models import Residentes
                residente = Residentes.objects.get(unidad=unidad)
            except:
                pass
            
            # Crear notificación
            titulo = f"Pago Fallido - Cuota {cuota_unidad.cuota_mensual.mes_año}"
            mensaje = f"Su pago de Bs. {cuota_unidad.monto} no pudo ser procesado. {motivo}"
            
            if residente and residente.usuario:
                NotificacionService.crear_notificacion(
                    usuario=residente.usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo='pago_fallido'
                )
            
            logger.info(f"Notificación de pago fallido enviada para cuota {cuota_unidad.id}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago fallido: {e}")


# Instancia global del servicio
pasarela_service = PasarelaPagosService()
