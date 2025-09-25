"""
Servicio de Reconocimiento de Placas con IA
Simula el funcionamiento de un sistema de IA para reconocimiento de placas
Preparado para integrar con servicios reales como OpenCV, TensorFlow, etc.
"""

import re
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone

logger = logging.getLogger(__name__)

class ReconocimientoPlacasService:
    """Servicio para reconocimiento de placas vehiculares con IA"""

    def __init__(self):
        # Configuración de umbrales (puede venir de ConfiguracionAcceso)
        self.umbral_confianza_placa = 80.0
        self.umbral_confianza_vehiculo = 70.0
        self.tiempo_max_procesamiento = 30.0

        # Patrones de placas comunes (puedes expandir esto)
        self.patrones_placas = [
            r'^[A-Z]{3}\d{3}$',  # ABC123
            r'^[A-Z]{2}\d{3}[A-Z]$',  # AB123C
            r'^\d{3}[A-Z]{3}$',  # 123ABC
            r'^[A-Z]\d{3}[A-Z]{2}$',  # A123BC
        ]

    def procesar_imagen(self, imagen_path: str, camara_id: str = "CAM01") -> Dict:
        """
        Procesa una imagen para reconocer placa vehicular
        En una implementación real, aquí iría:
        - OpenCV para procesamiento de imagen
        - TensorFlow/PyTorch para reconocimiento
        - OCR para lectura de texto
        """
        try:
            # Simular tiempo de procesamiento
            tiempo_inicio = datetime.now()

            # Simular reconocimiento de placa
            resultado = self._simular_reconocimiento_placa(imagen_path)

            tiempo_procesamiento = (datetime.now() - tiempo_inicio).total_seconds()

            return {
                'success': True,
                'placa_detectada': resultado['placa'],
                'marca_detectada': resultado['marca'],
                'modelo_detectado': resultado['modelo'],
                'color_detectado': resultado['color'],
                'ia_confidence': resultado['confidence'],
                'ia_placa_reconocida': resultado['placa_reconocida'],
                'ia_vehiculo_reconocido': resultado['vehiculo_reconocido'],
                'tiempo_procesamiento': tiempo_procesamiento,
                'camara_id': camara_id,
                'timestamp': timezone.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tiempo_procesamiento': 0,
                'camara_id': camara_id,
                'timestamp': timezone.now().isoformat()
            }

    def _simular_reconocimiento_placa(self, imagen_path: str) -> Dict:
        """
        Simula el reconocimiento de placa
        En producción, esto sería reemplazado por IA real
        """
        # Simular diferentes niveles de confianza
        confidence = random.uniform(60, 95)

        # Simular diferentes tipos de placas
        tipos_placa = [
            ('ABC123', 'Toyota', 'Corolla', 'Blanco'),
            ('XYZ789', 'Honda', 'Civic', 'Gris'),
            ('DEF456', 'Ford', 'Focus', 'Azul'),
            ('GHI012', 'Chevrolet', 'Spark', 'Rojo'),
            ('JKL345', 'Nissan', 'Sentra', 'Negro'),
            ('MNO678', 'Hyundai', 'Elantra', 'Plata'),
        ]

        # Elegir una placa aleatoria
        placa, marca, modelo, color = random.choice(tipos_placa)

        # Simular si la IA reconoce la placa correctamente
        placa_reconocida = confidence >= self.umbral_confianza_placa
        vehiculo_reconocido = confidence >= self.umbral_confianza_vehiculo

        # Simular errores ocasionales
        if random.random() < 0.1:  # 10% de error
            placa = self._generar_placa_erronea(placa)
            placa_reconocida = False
            confidence = max(30, confidence - 40)

        return {
            'placa': placa,
            'marca': marca,
            'modelo': modelo,
            'color': color,
            'confidence': round(confidence, 2),
            'placa_reconocida': placa_reconocida,
            'vehiculo_reconocido': vehiculo_reconocido
        }

    def _generar_placa_erronea(self, placa_original: str) -> str:
        """Genera una placa con errores para simular fallos de IA"""
        placa = list(placa_original)

        # Introducir 1-2 errores
        num_errores = random.randint(1, 2)
        for _ in range(num_errores):
            posicion = random.randint(0, len(placa) - 1)
            if placa[posicion].isalpha():
                placa[posicion] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            else:
                placa[posicion] = str(random.randint(0, 9))

        return ''.join(placa)

    def validar_formato_placa(self, placa: str) -> bool:
        """Valida si una placa tiene formato correcto"""
        placa = placa.upper().replace(' ', '').replace('-', '')

        for patron in self.patrones_placas:
            if re.match(patron, placa):
                return True

        return False

    def normalizar_placa(self, placa: str) -> str:
        """Normaliza el formato de una placa"""
        return placa.upper().replace(' ', '').replace('-', '')

    def calcular_similaridad(self, placa1: str, placa2: str) -> float:
        """
        Calcula el porcentaje de similaridad entre dos placas
        Útil para encontrar placas similares cuando hay errores de OCR
        """
        placa1 = self.normalizar_placa(placa1)
        placa2 = self.normalizar_placa(placa2)

        if placa1 == placa2:
            return 100.0

        # Calcular similaridad carácter por carácter
        if len(placa1) != len(placa2):
            return 0.0

        coincidencias = sum(c1 == c2 for c1, c2 in zip(placa1, placa2))
        return (coincidencias / len(placa1)) * 100

    def buscar_placas_similares(self, placa_detectada: str, umbral: float = 80.0) -> List[Dict]:
        """
        Busca placas similares en la base de datos
        Útil cuando la IA no reconoce perfectamente la placa
        """
        from usuarios.models import PlacaVehiculo, PlacaInvitado

        placa_detectada = self.normalizar_placa(placa_detectada)
        similares = []

        # Buscar en placas de residentes
        placas_residentes = PlacaVehiculo.objects.filter(activo=True)
        for placa_obj in placas_residentes:
            similaridad = self.calcular_similaridad(placa_detectada, placa_obj.placa)
            if similaridad >= umbral:
                similares.append({
                    'tipo': 'residente',
                    'placa': placa_obj.placa,
                    'similaridad': similaridad,
                    'residente': {
                        'id': placa_obj.residente.id,
                        'nombre': placa_obj.residente.persona.nombre,
                        'email': placa_obj.residente.persona.email
                    },
                    'vehiculo': {
                        'marca': placa_obj.marca,
                        'modelo': placa_obj.modelo,
                        'color': placa_obj.color
                    }
                })

        # Buscar en placas de invitados
        placas_invitados = PlacaInvitado.objects.filter(
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        )
        for placa_obj in placas_invitados:
            similaridad = self.calcular_similaridad(placa_detectada, placa_obj.placa)
            if similaridad >= umbral:
                similares.append({
                    'tipo': 'invitado',
                    'placa': placa_obj.placa,
                    'similaridad': similaridad,
                    'residente': {
                        'id': placa_obj.residente.id,
                        'nombre': placa_obj.residente.persona.nombre,
                        'email': placa_obj.residente.persona.email
                    },
                    'invitado': {
                        'nombre': placa_obj.nombre_visitante,
                        'ci': placa_obj.ci_visitante,
                        'fecha_vencimiento': placa_obj.fecha_vencimiento
                    },
                    'vehiculo': {
                        'marca': placa_obj.marca,
                        'modelo': placa_obj.modelo,
                        'color': placa_obj.color
                    }
                })

        # Ordenar por similaridad descendente
        similares.sort(key=lambda x: x['similaridad'], reverse=True)

        return similares

    def generar_reporte_diagnostico(self) -> Dict:
        """Genera un reporte de diagnóstico del sistema de IA"""
        from usuarios.models import RegistroAcceso, ConfiguracionAcceso

        config = ConfiguracionAcceso.objects.first()
        if not config:
            config = ConfiguracionAcceso.objects.create()

        # Estadísticas de los últimos 30 días
        fecha_desde = timezone.now() - timedelta(days=30)
        registros = RegistroAcceso.objects.filter(fecha_hora__gte=fecha_desde)

        total_registros = registros.count()
        if total_registros == 0:
            return {
                'status': 'sin_datos',
                'message': 'No hay datos suficientes para generar diagnóstico'
            }

        # Calcular métricas
        registros_autorizados = registros.filter(estado_acceso='autorizado').count()
        registros_denegados = registros.filter(estado_acceso='denegado').count()
        registros_pendientes = registros.filter(estado_acceso='pendiente').count()

        # Métricas de IA
        avg_confidence = registros.aggregate(
            avg_confidence=models.Avg('ia_confidence')
        )['avg_confidence'] or 0

        placas_reconocidas = registros.filter(ia_placa_reconocida=True).count()
        vehiculos_reconocidos = registros.filter(ia_vehiculo_reconocido=True).count()

        return {
            'status': 'success',
            'periodo': 'ultimos_30_dias',
            'metricas': {
                'total_registros': total_registros,
                'tasa_exito': round((registros_autorizados / total_registros) * 100, 2),
                'tasa_denegados': round((registros_denegados / total_registros) * 100, 2),
                'tasa_pendientes': round((registros_pendientes / total_registros) * 100, 2),
            },
            'ia_metrics': {
                'avg_confidence': round(avg_confidence, 2),
                'tasa_placas_reconocidas': round((placas_reconocidas / total_registros) * 100, 2),
                'tasa_vehiculos_reconocidos': round((vehiculos_reconocidos / total_registros) * 100, 2),
            },
            'configuracion': {
                'umbral_confianza_placa': config.umbral_confianza_placa,
                'umbral_confianza_vehiculo': config.umbral_confianza_vehiculo,
                'tiempo_max_procesamiento': config.tiempo_max_procesamiento,
            },
            'recomendaciones': self._generar_recomendaciones(
                registros_autorizados, registros_denegados, avg_confidence
            )
        }

    def _generar_recomendaciones(self, autorizados: int, denegados: int, avg_confidence: float) -> List[str]:
        """Genera recomendaciones basadas en las métricas"""
        recomendaciones = []

        if avg_confidence < 70:
            recomendaciones.append(
                "Considera ajustar los umbrales de confianza o mejorar la calidad de las cámaras"
            )

        if denegados > autorizados:
            recomendaciones.append(
                "Alta tasa de denegados. Revisa la configuración de umbrales y la calidad de las imágenes"
            )

        if avg_confidence < 60:
            recomendaciones.append(
                "La confianza de la IA es baja. Considera reentrenar el modelo o mejorar la iluminación"
            )

        if not recomendaciones:
            recomendaciones.append("El sistema está funcionando correctamente")

        return recomendaciones
