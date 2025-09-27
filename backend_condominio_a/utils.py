"""
Utilidades y funciones comunes para el proyecto Condominio
"""

import logging
import functools
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from functools import wraps
from time import time

logger = logging.getLogger(__name__)

def log_execution_time(func):
    """
    Decorador para medir y loguear el tiempo de ejecución de funciones
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()
        execution_time = end_time - start_time

        logger.info(
            f"{func.__name__} ejecutado en {execution_time:.4f} segundos",
            extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'module': func.__module__
            }
        )

        return result
    return wrapper

def log_database_queries(func):
    """
    Decorador para loguear consultas de base de datos
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Contar consultas antes
        initial_count = len(connection.queries)

        result = func(*args, **kwargs)

        # Contar consultas después
        final_count = len(connection.queries)
        query_count = final_count - initial_count

        if query_count > 0:
            logger.info(
                f"{func.__name__} ejecutó {query_count} consultas de base de datos",
                extra={
                    'function': func.__name__,
                    'query_count': query_count,
                    'queries': connection.queries[initial_count:] if settings.DEBUG else []
                }
            )

        return result
    return wrapper

def cache_result(timeout=300):
    """
    Decorador para cachear resultados de funciones
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crear una clave de cache basada en el nombre de la función y argumentos
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Intentar obtener del cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit para {func.__name__}")
                return result

            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss para {func.__name__}, resultado cacheado")

            return result
        return wrapper
    return decorator

def optimize_queryset(queryset_func):
    """
    Decorador para optimizar querysets con select_related y prefetch_related
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener el queryset
            queryset = func(*args, **kwargs)

            # Aplicar optimizaciones comunes
            if hasattr(queryset, 'select_related'):
                # Optimizar relaciones comunes
                queryset = queryset.select_related(
                    'usuario', 'persona', 'rol', 'residente'
                )

            if hasattr(queryset, 'prefetch_related'):
                # Optimizar relaciones many-to-many y reverse foreign keys
                queryset = queryset.prefetch_related(
                    'rolpermiso_set__permiso',
                    'vehiculo_set',
                    'accesovehicular_set'
                )

            return queryset
        return wrapper
    return decorator

def safe_database_operation(max_retries=3):
    """
    Decorador para operaciones de base de datos con reintentos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Intento {attempt + 1} fallido para {func.__name__}: {str(e)}"
                    )

                    if attempt < max_retries - 1:
                        # Esperar antes del siguiente intento (backoff exponencial)
                        import time
                        time.sleep(2 ** attempt)

            # Si todos los intentos fallaron, loguear error y relanzar
            logger.error(
                f"Todos los intentos fallaron para {func.__name__}",
                exc_info=True
            )
            raise last_exception
        return wrapper
    return decorator

def validate_request_data(required_fields=None):
    """
    Decorador para validar datos de request
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in request.data:
                        missing_fields.append(field)

                if missing_fields:
                    logger.warning(
                        f"Campos requeridos faltantes en {func.__name__}: {missing_fields}",
                        extra={'missing_fields': missing_fields}
                    )
                    return Response({
                        'error': 'Campos requeridos faltantes',
                        'missing_fields': missing_fields
                    }, status=status.HTTP_400_BAD_REQUEST)

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def log_api_call(func):
    """
    Decorador para loguear llamadas a la API
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        # Log de la llamada API
        logger.info(
            f"API Call: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'user': getattr(request.user, 'username', 'Anonymous'),
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        # Ejecutar la función
        response = func(self, request, *args, **kwargs)

        # Log de la respuesta
        logger.info(
            f"API Response: {request.method} {request.path} - Status: {response.status_code}",
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'user': getattr(request.user, 'username', 'Anonymous'),
            }
        )

        return response
    return wrapper

class DatabaseQueryOptimizer:
    """
    Clase para optimizar consultas de base de datos comunes
    """

    @staticmethod
    def get_user_with_profile(user_id):
        """Obtener usuario con perfil optimizado"""
        from usuarios.models import Usuario, Persona, Empleado, Residentes

        return Usuario.objects.select_related(
            'persona',
            'rol'
        ).prefetch_related(
            'rolpermiso_set__permiso'
        ).get(id=user_id)

    @staticmethod
    def get_residents_with_units():
        """Obtener residentes con sus unidades optimizado"""
        from usuarios.models import Residentes
        from comunidad.models import Unidad

        return Residentes.objects.select_related(
            'persona',
            'usuario'
        ).prefetch_related(
            'unidad_set'
        ).all()

    @staticmethod
    def get_financial_summary():
        """Obtener resumen financiero optimizado"""
        from economia.models import Gastos, Multa
        from finanzas.models import Pago, Expensa
        from django.db.models import Sum

        return {
            'gastos': Gastos.objects.aggregate(total=Sum('monto'))['total'] or 0,
            'multas': Multa.objects.aggregate(total=Sum('monto'))['total'] or 0,
            'pagos': 0,  # CU7 eliminado
            'expensas': Expensa.objects.aggregate(total=Sum('monto'))['total'] or 0,
        }

    @staticmethod
    def get_dashboard_data(user):
        """Obtener datos del dashboard optimizados"""
        from usuarios.models import Empleado, Residentes
        from comunidad.models import Evento, Notificacion
        from economia.models import Multa
        from finanzas.models import Pago

        # Determinar si es administrador
        is_admin = (
            user.is_superuser or
            (hasattr(user, 'rol') and user.rol and user.rol.nombre.lower() == 'administrador') or
            Empleado.objects.filter(usuario=user, cargo__icontains='admin').exists()
        )

        if is_admin:
            # Datos para administrador
            return {
                'eventos_pendientes': Evento.objects.filter(fecha__gte='today').count(),
                'notificaciones_sin_leer': Notificacion.objects.filter(leida=False).count(),
                'multas_pendientes': Multa.objects.filter(pagada=False).count(),
                'pagos_pendientes': Pago.objects.filter(estado_pago='pendiente').count(),
            }
        else:
            # Datos para residente
            residente = Residentes.objects.filter(usuario=user).first()
            if residente:
                return {
                    'mis_multas': Multa.objects.filter(residente=residente, pagada=False).count(),
                    'mis_pagos': Pago.objects.filter(residente=residente, estado_pago='pendiente').count(),
                    'mis_notificaciones': Notificacion.objects.filter(usuario=user, leida=False).count(),
                }
            return {}
