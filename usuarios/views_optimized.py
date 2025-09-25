"""
Views optimizados para el módulo de usuarios
Incluye optimizaciones de consultas, logging y manejo de errores
"""

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from usuarios.models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo, Residentes
)
from usuarios.serializers.usuarios_serializer import (
    UsuarioSerializer, PersonaSerializer, RolesSerializer,
    PermisoSerializer, RolPermisoSerializer, EmpleadoSerializer,
    VehiculoSerializer, AccesoVehicularSerializer, VisitaSerializer,
    InvitadoSerializer, ReclamoSerializer, ResidentesSerializer
)
from backend_condominio_a.utils import (
    log_execution_time, log_database_queries, optimize_queryset,
    log_api_call, validate_request_data, DatabaseQueryOptimizer
)
import logging

logger = logging.getLogger(__name__)

# Permiso personalizado para acceso de administrador
class RolPermisoPermission(permissions.BasePermission):
    """
    Solo usuarios con cargo Administrador pueden acceder
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Permitir si es superusuario o tiene rol de administrador
        return request.user.is_superuser or (request.user.rol and request.user.rol.nombre == 'Administrador')


class ResidentesViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para residentes"""
    queryset = Residentes.objects.all()
    serializer_class = ResidentesSerializer
    permission_classes = [permissions.IsAuthenticated]

    @log_api_call
    @log_execution_time
    @log_database_queries
    def list(self, request, *args, **kwargs):
        """Listar residentes con optimización de consultas"""
        queryset = self.get_queryset().select_related(
            'persona',
            'usuario',
            'usuario__rol'
        ).prefetch_related('unidad_set')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para usuarios"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    @log_database_queries
    def list(self, request, *args, **kwargs):
        """Listar usuarios con optimización"""
        queryset = self.get_queryset().select_related(
            'persona',
            'rol'
        ).prefetch_related('rolpermiso_set__permiso')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @log_api_call
    @log_execution_time
    @validate_request_data(['username', 'email'])
    def create(self, request, *args, **kwargs):
        """Crear usuario con validación y logging"""
        return super().create(request, *args, **kwargs)


class PersonaViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para personas"""
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    @log_database_queries
    def get_queryset(self):
        """Optimizar queryset con filtros de seguridad"""
        if not self.request.user or not self.request.user.is_authenticated:
            return Persona.objects.none()

        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Persona.objects.select_related('usuario', 'usuario__rol').all()
        elif empleado:
            return Persona.objects.filter(id=empleado.persona.id)

        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Persona.objects.filter(id=residente.persona.id)
        return Persona.objects.none()

    def list(self, request, *args, **kwargs):
        """Listar personas con optimización"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RolesViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para roles"""
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar roles con optimización"""
        queryset = self.get_queryset().prefetch_related('rolpermiso_set__permiso')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PermisoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para permisos"""
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar permisos"""
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class RolPermisoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para permisos de roles"""
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar permisos de roles con optimización"""
        queryset = self.get_queryset().select_related('rol', 'permiso')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EmpleadoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para empleados"""
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    @log_database_queries
    def list(self, request, *args, **kwargs):
        """Listar empleados con optimización"""
        queryset = self.get_queryset().select_related(
            'persona',
            'usuario',
            'usuario__rol'
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VehiculoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para vehículos"""
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar vehículos con optimización"""
        queryset = self.get_queryset().select_related('residente__persona')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AccesoVehicularViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para accesos vehiculares"""
    queryset = AccesoVehicular.objects.all()
    serializer_class = AccesoVehicularSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar accesos vehiculares con optimización"""
        queryset = self.get_queryset().select_related(
            'vehiculo',
            'vehiculo__residente__persona'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VisitaViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para visitas"""
    queryset = Visita.objects.all()
    serializer_class = VisitaSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar visitas con optimización"""
        queryset = self.get_queryset().select_related(
            'invitado',
            'residente__persona'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InvitadoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para invitados"""
    queryset = Invitado.objects.all()
    serializer_class = InvitadoSerializer
    permission_classes = [RolPermisoPermission]

    @log_api_call
    @log_execution_time
    def list(self, request, *args, **kwargs):
        """Listar invitados con optimización"""
        queryset = self.get_queryset().select_related('visita__residente__persona')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReclamoViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para reclamos"""
    queryset = Reclamo.objects.all()
    serializer_class = ReclamoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @log_api_call
    @log_execution_time
    @log_database_queries
    def get_queryset(self):
        """Optimizar queryset con filtros de seguridad"""
        if not self.request.user or not self.request.user.is_authenticated:
            return Reclamo.objects.none()

        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Reclamo.objects.select_related(
                'residente__persona',
                'residente__usuario'
            ).all()

        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Reclamo.objects.filter(residente=residente)
        return Reclamo.objects.none()

    def list(self, request, *args, **kwargs):
        """Listar reclamos con optimización"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @log_api_call
    @log_execution_time
    @validate_request_data(['titulo', 'descripcion'])
    def create(self, request, *args, **kwargs):
        """Crear reclamo con validación y logging"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Asignar automáticamente el residente al crear el reclamo"""
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            serializer.save(residente=residente)
        else:
            logger.warning(
                f"Usuario {self.request.user.username} intentó crear reclamo sin ser residente"
            )
            raise ValidationError("Solo los residentes pueden crear reclamos")


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet para datos del dashboard optimizados"""
    permission_classes = [permissions.IsAuthenticated]

    @log_api_call
    @log_execution_time
    @log_database_queries
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtener resumen del dashboard"""
        try:
            dashboard_data = DatabaseQueryOptimizer.get_dashboard_data(request.user)
            return Response(dashboard_data)
        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'message': 'No se pudieron obtener los datos del dashboard'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @log_api_call
    @log_execution_time
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas generales"""
        try:
            from django.db.models import Count, Sum
            from economia.models import Gastos, Multa
            from finanzas.models import Pago
            from comunidad.models import Evento, Notificacion

            stats = {
                'total_usuarios': Usuario.objects.count(),
                'total_residentes': Residentes.objects.count(),
                'total_empleados': Empleado.objects.count(),
                'eventos_activos': Evento.objects.filter(fecha__gte='today').count(),
                'notificaciones_pendientes': Notificacion.objects.filter(leida=False).count(),
                'gastos_total': Gastos.objects.aggregate(total=Sum('monto'))['total'] or 0,
                'multas_total': Multa.objects.aggregate(total=Sum('monto'))['total'] or 0,
                'pagos_total': Pago.objects.aggregate(total=Sum('monto'))['total'] or 0,
            }

            return Response(stats)
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'message': 'No se pudieron obtener las estadísticas'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
