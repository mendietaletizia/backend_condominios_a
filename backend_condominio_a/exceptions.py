"""
Módulo de manejo de excepciones personalizado para el proyecto Condominio
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DataError
from django.http import Http404

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado que registra errores y devuelve respuestas consistentes
    """
    # Log del error
    logger.error(
        f"Error en {context['view'].__class__.__name__}: {str(exc)}",
        exc_info=True,
        extra={
            'request': context['request'],
            'view': context['view'].__class__.__name__,
            'user': getattr(context['request'].user, 'username', 'Anonymous'),
        }
    )

    # Llamar al manejador por defecto de DRF
    response = exception_handler(exc, context)

    # Si DRF no manejó la excepción, crear una respuesta personalizada
    if response is None:
        return handle_unhandled_exception(exc, context)

    # Personalizar respuestas para diferentes tipos de errores
    if isinstance(exc, ValidationError):
        return handle_validation_error(exc, response)
    elif isinstance(exc, IntegrityError):
        return handle_integrity_error(exc, response)
    elif isinstance(exc, DataError):
        return handle_data_error(exc, response)
    elif isinstance(exc, Http404):
        return handle_not_found_error(exc, response)

    return response

def handle_unhandled_exception(exc, context):
    """Manejar excepciones no manejadas por DRF"""
    logger.critical(f"Excepción no manejada: {str(exc)}", exc_info=True)

    return Response({
        'error': 'Error interno del servidor',
        'message': 'Ha ocurrido un error inesperado. Por favor, contacte al administrador.',
        'details': str(exc) if context['request'].user.is_staff else None
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def handle_validation_error(exc, response):
    """Manejar errores de validación"""
    return Response({
        'error': 'Datos inválidos',
        'message': 'Los datos proporcionados no son válidos.',
        'details': exc.messages if hasattr(exc, 'messages') else str(exc)
    }, status=status.HTTP_400_BAD_REQUEST)

def handle_integrity_error(exc, response):
    """Manejar errores de integridad de base de datos"""
    return Response({
        'error': 'Error de integridad',
        'message': 'No se puede realizar la operación debido a restricciones de integridad.',
        'details': 'El registro está siendo utilizado por otros datos del sistema.'
    }, status=status.HTTP_409_CONFLICT)

def handle_data_error(exc, response):
    """Manejar errores de datos"""
    return Response({
        'error': 'Error de datos',
        'message': 'Los datos proporcionados no son válidos o están corruptos.',
        'details': str(exc)
    }, status=status.HTTP_400_BAD_REQUEST)

def handle_not_found_error(exc, response):
    """Manejar errores 404"""
    return Response({
        'error': 'Recurso no encontrado',
        'message': 'El recurso solicitado no existe.',
        'details': str(exc)
    }, status=status.HTTP_404_NOT_FOUND)

class CustomAPIException(Exception):
    """
    Excepción base personalizada para la API
    """
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

    def to_response(self):
        return Response({
            'error': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }, status=self.status_code)

class AuthenticationError(CustomAPIException):
    """Error de autenticación"""
    def __init__(self, message="Error de autenticación"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(CustomAPIException):
    """Error de autorización"""
    def __init__(self, message="No tiene permisos para realizar esta acción"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)

class NotFoundError(CustomAPIException):
    """Recurso no encontrado"""
    def __init__(self, message="Recurso no encontrado"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)

class ValidationError(CustomAPIException):
    """Error de validación"""
    def __init__(self, message="Datos inválidos", details=None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)

class BusinessLogicError(CustomAPIException):
    """Error de lógica de negocio"""
    def __init__(self, message="Operación no permitida por reglas de negocio"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)
