from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import json

from usuarios.models import (
    PlacaVehiculo, PlacaInvitado, RegistroAcceso, ConfiguracionAcceso,
    Residentes, Usuario, Empleado
)
from usuarios.serializers.usuarios_serializer import (
    PlacaVehiculoSerializer, PlacaInvitadoSerializer,
    RegistroAccesoSerializer, ConfiguracionAccesoSerializer
)

class PlacaVehiculoViewSet(ModelViewSet):
    """Gestión de placas de vehículos de residentes"""
    queryset = PlacaVehiculo.objects.all()
    serializer_class = PlacaVehiculoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _es_admin_o_seguridad(self, user):
        if user.is_superuser:
            return True
        if getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
            return True
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
            return True
        return False

    def get_queryset(self):
        queryset = PlacaVehiculo.objects.all()

        # Scoping por rol
        if not self._es_admin_o_seguridad(self.request.user):
            residente = Residentes.objects.filter(usuario=self.request.user).first()
            if residente:
                queryset = queryset.filter(residente=residente)
            else:
                return PlacaVehiculo.objects.none()

        # Filtros
        residente_id = self.request.query_params.get('residente_id')
        if residente_id:
            queryset = queryset.filter(residente_id=residente_id)

        unidad_id = self.request.query_params.get('unidad_id')
        if unidad_id:
            queryset = queryset.filter(residente__residentesunidad__id_unidad_id=unidad_id, residente__residentesunidad__estado=True)

        placa = self.request.query_params.get('placa')
        if placa:
            queryset = queryset.filter(placa__icontains=placa)

        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')

        return queryset.distinct().order_by('-fecha_registro')

    @action(detail=False, methods=['get'])
    def por_residente(self, request):
        """Obtener todas las placas de un residente específico"""
        residente_id = request.query_params.get('residente_id')
        if not residente_id:
            return Response(
                {'error': 'Debe proporcionar residente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        placas = self.get_queryset().filter(residente_id=residente_id)
        serializer = self.get_serializer(placas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_unidad(self, request):
        """Obtener placas activas asociadas a una unidad mediante relaciones de residentes activos."""
        unidad_id = self.request.query_params.get('unidad_id')
        if not unidad_id:
            return Response({'error': 'Debe proporcionar unidad_id'}, status=status.HTTP_400_BAD_REQUEST)

        placas = self.get_queryset().filter(
            residente__residentesunidad__id_unidad_id=unidad_id,
            residente__residentesunidad__estado=True
        ).distinct()
        serializer = self.get_serializer(placas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen_unidad(self, request):
        """Resumen de vehículos por unidad: totales, activos, últimos registrados."""
        unidad_id = self.request.query_params.get('unidad_id')
        if not unidad_id:
            return Response({'error': 'Debe proporcionar unidad_id'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(
            residente__residentesunidad__id_unidad_id=unidad_id,
            residente__residentesunidad__estado=True
        ).distinct()

        total = qs.count()
        activos = qs.filter(activo=True).count()
        ultimos = qs.order_by('-fecha_registro')[:10]
        serializer = self.get_serializer(ultimos, many=True)
        return Response({
            'unidad_id': int(unidad_id),
            'total': total,
            'activos': activos,
            'ultimos': serializer.data
        })

class PlacaInvitadoViewSet(ModelViewSet):
    """Gestión de placas de vehículos de invitados"""
    queryset = PlacaInvitado.objects.all()
    serializer_class = PlacaInvitadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = PlacaInvitado.objects.all()
        residente_id = self.request.query_params.get('residente_id', None)
        if residente_id:
            queryset = queryset.filter(residente_id=residente_id)
        return queryset

    @action(detail=False, methods=['get'])
    def por_residente(self, request):
        """Obtener todas las placas de invitados de un residente"""
        residente_id = request.query_params.get('residente_id')
        if not residente_id:
            return Response(
                {'error': 'Debe proporcionar residente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        placas = self.queryset.filter(residente_id=residente_id)
        serializer = self.get_serializer(placas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Obtener placas de invitados que no han vencido"""
        ahora = timezone.now()
        placas_activas = self.queryset.filter(
            activo=True,
            fecha_vencimiento__gte=ahora
        )
        serializer = self.get_serializer(placas_activas, many=True)
        return Response(serializer.data)

class RegistroAccesoViewSet(ModelViewSet):
    """Gestión de registros de acceso vehicular"""
    queryset = RegistroAcceso.objects.all()
    serializer_class = RegistroAccesoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = RegistroAcceso.objects.all()
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        estado = self.request.query_params.get('estado', None)
        tipo_acceso = self.request.query_params.get('tipo_acceso', None)

        if fecha_desde:
            queryset = queryset.filter(fecha_hora__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora__lte=fecha_hasta)
        if estado:
            queryset = queryset.filter(estado_acceso=estado)
        if tipo_acceso:
            queryset = queryset.filter(tipo_acceso=tipo_acceso)

        return queryset.order_by('-fecha_hora')

    @action(detail=False, methods=['post'])
    def registrar_acceso(self, request):
        """Registrar un nuevo acceso vehicular con IA"""
        try:
            data = request.data.copy()

            # Obtener configuración actual
            config = ConfiguracionAcceso.objects.first()
            if not config:
                config = ConfiguracionAcceso.objects.create()

            # Simular lógica de IA (por ahora)
            placa_detectada = data.get('placa_detectada', '').upper()

            # Buscar coincidencias en placas de residentes
            placa_vehiculo = None
            placa_invitado = None

            if len(placa_detectada) >= 6:  # Validar formato de placa
                placa_vehiculo = PlacaVehiculo.objects.filter(
                    placa=placa_detectada,
                    activo=True
                ).first()

                if not placa_vehiculo:
                    # Buscar en placas de invitados
                    placa_invitado = PlacaInvitado.objects.filter(
                        placa=placa_detectada,
                        activo=True,
                        fecha_vencimiento__gte=timezone.now()
                    ).first()

            # Determinar estado del acceso
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            if placa_vehiculo or placa_invitado:
                estado_acceso = 'autorizado'
                ia_autentico = True
            elif ia_confidence >= config.umbral_confianza_placa:
                estado_acceso = 'pendiente'
                ia_autentico = False
            else:
                estado_acceso = 'denegado'
                ia_autentico = False

            # Crear registro de acceso
            registro_data = {
                'placa_detectada': placa_detectada,
                'marca_detectada': data.get('marca_detectada', ''),
                'modelo_detectado': data.get('modelo_detectado', ''),
                'color_detectado': data.get('color_detectado', ''),
                'ia_confidence': ia_confidence,
                'ia_autentico': ia_autentico,
                'ia_placa_reconocida': ia_placa_reconocida,
                'ia_vehiculo_reconocido': ia_vehiculo_reconocido,
                'tipo_acceso': data.get('tipo_acceso', 'entrada'),
                'estado_acceso': estado_acceso,
                'imagen_url': data.get('imagen_url', ''),
                'imagen_path': data.get('imagen_path', ''),
                'camara_id': data.get('camara_id', ''),
                'tiempo_procesamiento': data.get('tiempo_procesamiento', 0),
                'observaciones': data.get('observaciones', ''),
                'placa_vehiculo': placa_vehiculo,
                'placa_invitado': placa_invitado,
            }

            serializer = self.get_serializer(data=registro_data)
            serializer.is_valid(raise_exception=True)
            registro = serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al registrar acceso: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def autorizar_manual(self, request, pk=None):
        """Autorizar manualmente un acceso denegado o pendiente"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso in ['autorizado', 'denegado']:
            return Response(
                {'error': 'Este registro ya ha sido procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro.estado_acceso = 'autorizado'
        registro.autorizado_por = usuario
        registro.observaciones = f"Autorizado manualmente por {usuario.username}"
        registro.save()

        serializer = self.get_serializer(registro)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def denegar_manual(self, request, pk=None):
        """Denegar manualmente un acceso"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso in ['autorizado', 'denegado']:
            return Response(
                {'error': 'Este registro ya ha sido procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro.estado_acceso = 'denegado'
        registro.autorizado_por = usuario
        registro.observaciones = f"Denegado manualmente por {usuario.username}"
        registro.save()

        serializer = self.get_serializer(registro)
        return Response(serializer.data)

class ConfiguracionAccesoViewSet(ModelViewSet):
    """Gestión de configuración del sistema de acceso"""
    queryset = ConfiguracionAcceso.objects.all()
    serializer_class = ConfiguracionAccesoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Siempre devolver la primera (y única) configuración
        obj, created = ConfiguracionAcceso.objects.get_or_create(pk=1)
        return obj

    def list(self, request, *args, **kwargs):
        # Devolver la configuración actual
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def probar_conexion(self, request):
        """Probar la conexión con el sistema de IA/cámaras"""
        # Aquí iría la lógica para probar la conexión
        return Response({
            'status': 'success',
            'message': 'Conexión exitosa',
            'timestamp': timezone.now()
        })

class DashboardAccesoView(APIView):
    """Dashboard con estadísticas del sistema de acceso"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)

        # Estadísticas generales
        total_registros = RegistroAcceso.objects.count()
        registros_hoy = RegistroAcceso.objects.filter(
            fecha_hora__date=hoy
        ).count()
        registros_mes = RegistroAcceso.objects.filter(
            fecha_hora__date__gte=inicio_mes
        ).count()

        # Estadísticas por estado
        autorizados = RegistroAcceso.objects.filter(
            estado_acceso='autorizado'
        ).count()
        denegados = RegistroAcceso.objects.filter(
            estado_acceso='denegado'
        ).count()
        pendientes = RegistroAcceso.objects.filter(
            estado_acceso='pendiente'
        ).count()

        # Placas activas
        placas_residentes = PlacaVehiculo.objects.filter(activo=True).count()
        placas_invitados = PlacaInvitado.objects.filter(
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        ).count()

        # Últimos registros
        ultimos_registros = RegistroAcceso.objects.all()[:10]
        serializer = RegistroAccesoSerializer(ultimos_registros, many=True)

        return Response({
            'estadisticas': {
                'total_registros': total_registros,
                'registros_hoy': registros_hoy,
                'registros_mes': registros_mes,
                'autorizados': autorizados,
                'denegados': denegados,
                'pendientes': pendientes,
                'tasa_exito': round((autorizados / total_registros * 100), 2) if total_registros > 0 else 0
            },
            'placas': {
                'residentes_activas': placas_residentes,
                'invitados_activos': placas_invitados
            },
            'ultimos_registros': serializer.data
        })
