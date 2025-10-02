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
    Residentes, Usuario, Empleado, Vehiculo, Invitado
)
from django.db.models import F
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
    
    def buscar_placa_inteligente(self, placa_detectada):
        """
        Búsqueda inteligente de placas con múltiples estrategias
        Retorna un diccionario con la información encontrada
        """
        resultado = {
            'encontrada': False,
            'tipo': None,
            'objeto': None,
            'info_detallada': {},
            'mensaje_ia': '',
            'confianza_busqueda': 0
        }
        
        if not placa_detectada or len(placa_detectada) < 4:
            return resultado
            
        placa_limpia = placa_detectada.upper().strip()
        
        # Estrategia 1: Búsqueda exacta en PlacaVehiculo (residentes)
        placa_vehiculo = PlacaVehiculo.objects.filter(
            placa__iexact=placa_limpia,
            activo=True
        ).first()
        
        if placa_vehiculo:
            resultado.update({
                'encontrada': True,
                'tipo': 'residente',
                'objeto': placa_vehiculo,
                'info_detallada': {
                    'propietario_nombre': placa_vehiculo.residente.persona.nombre,
                    'vehiculo_info': f"{placa_vehiculo.marca} {placa_vehiculo.modelo} ({placa_vehiculo.color})",
                    'unidad': placa_vehiculo.residente.residentesunidad_set.filter(estado=True).first(),
                    'fecha_registro': placa_vehiculo.fecha_registro
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE REGISTRADO - {placa_vehiculo.residente.persona.nombre}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 2: Búsqueda exacta en PlacaInvitado (invitados activos)
        placa_invitado = PlacaInvitado.objects.filter(
            placa__iexact=placa_limpia,
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        ).first()
        
        if placa_invitado:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado',
                'objeto': placa_invitado,
                'info_detallada': {
                    'visitante_nombre': placa_invitado.nombre_visitante,
                    'propietario_nombre': placa_invitado.residente.persona.nombre,
                    'vehiculo_info': f"{placa_invitado.marca or 'N/A'} {placa_invitado.modelo or 'N/A'} ({placa_invitado.color or 'N/A'})",
                    'fecha_vencimiento': placa_invitado.fecha_vencimiento,
                    'ci_visitante': placa_invitado.ci_visitante
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO REGISTRADO - {placa_invitado.nombre_visitante}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 3: Búsqueda en sistema original de Vehiculos
        vehiculo_original = Vehiculo.objects.filter(placa__iexact=placa_limpia).first()
        if vehiculo_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'vehiculo_original',
                'objeto': vehiculo_original,
                'info_detallada': {
                    'vehiculo_info': f"{vehiculo_original.marca} {vehiculo_original.modelo} ({vehiculo_original.color})",
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO EN SISTEMA ORIGINAL - {vehiculo_original.marca} {vehiculo_original.modelo}",
                'confianza_busqueda': 95
            })
            return resultado
        
        # Estrategia 4: Búsqueda en sistema original de Invitados
        invitado_original = Invitado.objects.filter(
            vehiculo_placa__iexact=placa_limpia,
            activo=True,
            fecha_fin__gte=timezone.now()
        ).first()
        
        if invitado_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado_original',
                'objeto': invitado_original,
                'info_detallada': {
                    'visitante_nombre': invitado_original.nombre,
                    'propietario_nombre': invitado_original.residente.persona.nombre if invitado_original.residente else 'Sin residente',
                    'fecha_fin': invitado_original.fecha_fin
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO EN SISTEMA ORIGINAL - {invitado_original.nombre}",
                'confianza_busqueda': 90
            })
            return resultado
        
        # Estrategia 5: Búsqueda parcial/fuzzy (sin espacios, guiones, etc.)
        variaciones_placa = [
            placa_limpia.replace(' ', ''),
            placa_limpia.replace('-', ''),
            placa_limpia.replace('.', ''),
            placa_limpia.replace(' ', '').replace('-', '').replace('.', '')
        ]
        
        for variacion in variaciones_placa:
            if variacion != placa_limpia and len(variacion) >= 4:
                # Buscar en residentes con variación
                placa_vehiculo_var = PlacaVehiculo.objects.filter(
                    placa__icontains=variacion,
                    activo=True
                ).first()
                
                if placa_vehiculo_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'residente',
                        'objeto': placa_vehiculo_var,
                        'info_detallada': {
                            'propietario_nombre': placa_vehiculo_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_vehiculo_var.marca} {placa_vehiculo_var.modelo} ({placa_vehiculo_var.color})",
                            'placa_original': placa_vehiculo_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE (coincidencia parcial) - {placa_vehiculo_var.residente.persona.nombre}",
                        'confianza_busqueda': 85
                    })
                    return resultado
                
                # Buscar en invitados con variación
                placa_invitado_var = PlacaInvitado.objects.filter(
                    placa__icontains=variacion,
                    activo=True,
                    fecha_vencimiento__gte=timezone.now()
                ).first()
                
                if placa_invitado_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'invitado',
                        'objeto': placa_invitado_var,
                        'info_detallada': {
                            'visitante_nombre': placa_invitado_var.nombre_visitante,
                            'propietario_nombre': placa_invitado_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_invitado_var.marca or 'N/A'} {placa_invitado_var.modelo or 'N/A'}",
                            'placa_original': placa_invitado_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO (coincidencia parcial) - {placa_invitado_var.nombre_visitante}",
                        'confianza_busqueda': 80
                    })
                    return resultado
        
        # No se encontró nada
        resultado.update({
            'mensaje_ia': f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO REGISTRADA EN EL SISTEMA",
            'confianza_busqueda': 0
        })
        
        return resultado

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
        """Registrar un nuevo acceso vehicular con IA mejorada"""
        try:
            data = request.data.copy()

            # Obtener configuración actual
            config = ConfiguracionAcceso.objects.first()
            if not config:
                config = ConfiguracionAcceso.objects.create()

            # Obtener placa detectada
            placa_detectada = data.get('placa_detectada', '').upper().strip()
            
            print(f"\n🔍 INICIANDO BÚSQUEDA INTELIGENTE DE PLACA: '{placa_detectada}'")
            
            # Usar búsqueda inteligente
            resultado_busqueda = self.buscar_placa_inteligente(placa_detectada)
            
            # Obtener parámetros de IA
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            print(f"📊 RESULTADO DE BÚSQUEDA:")
            print(f"   - Encontrada: {resultado_busqueda['encontrada']}")
            print(f"   - Tipo: {resultado_busqueda['tipo']}")
            print(f"   - Confianza: {resultado_busqueda['confianza_busqueda']}%")
            print(f"   - Mensaje IA: {resultado_busqueda['mensaje_ia']}")

            # LÓGICA DE AUTORIZACIÓN MEJORADA
            if resultado_busqueda['encontrada']:
                # ✅ PLACA ENCONTRADA -> AUTORIZADO AUTOMÁTICO
                estado_acceso = 'autorizado'
                ia_autentico = True
                ia_placa_reconocida = True
                ia_vehiculo_reconocido = True
                print(f"🎉 ACCESO AUTORIZADO AUTOMÁTICAMENTE")
            elif ia_confidence >= config.umbral_confianza_placa and ia_placa_reconocida:
                # ⏳ PLACA NO REGISTRADA PERO IA CONFÍA -> PENDIENTE
                estado_acceso = 'pendiente'
                ia_autentico = False
                print(f"⏳ ACCESO PENDIENTE - Requiere autorización manual")
            else:
                # ❌ PLACA NO RECONOCIDA O BAJA CONFIANZA -> DENEGADO
                estado_acceso = 'denegado'
                ia_autentico = False
                print(f"❌ ACCESO DENEGADO - Placa no registrada y baja confianza")

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
                'placa_vehiculo': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'residente' else None,
                'placa_invitado': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'invitado' else None,
            }

            serializer = self.get_serializer(data=registro_data)
            serializer.is_valid(raise_exception=True)
            registro = serializer.save()

            # Preparar respuesta detallada con información de la búsqueda inteligente
            response_data = serializer.data.copy()
            
            # Agregar información detallada del resultado de búsqueda
            response_data['mensaje'] = resultado_busqueda['mensaje_ia']
            response_data['confianza_busqueda'] = resultado_busqueda['confianza_busqueda']
            
            if resultado_busqueda['encontrada']:
                response_data['tipo_propietario'] = resultado_busqueda['tipo']
                response_data.update(resultado_busqueda['info_detallada'])
                
                # Información adicional según el tipo
                if resultado_busqueda['tipo'] == 'residente':
                    unidad = resultado_busqueda['info_detallada'].get('unidad')
                    if unidad:
                        response_data['unidad_numero'] = unidad.id_unidad.numero
                        response_data['unidad_tipo'] = unidad.id_unidad.tipo
                        
                elif resultado_busqueda['tipo'] == 'invitado':
                    response_data['fecha_vencimiento'] = resultado_busqueda['info_detallada'].get('fecha_vencimiento')
                    
            else:
                # Placa no encontrada
                if estado_acceso == 'pendiente':
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ⏳ PLACA '{placa_detectada}' NO REGISTRADA - Requiere verificación manual del administrador o seguridad"
                else:
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO RECONOCIDA - Acceso denegado por baja confianza de IA"

            print(f"\n✅ REGISTRO CREADO EXITOSAMENTE:")
            print(f"   - ID: {registro.id}")
            print(f"   - Estado: {estado_acceso.upper()}")
            print(f"   - Mensaje: {response_data['mensaje']}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al registrar acceso: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def autorizar_manual(self, request, pk=None):
        """Autorizar manualmente un acceso pendiente o denegado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'autorizado':
            return Response(
                {'error': 'Este registro ya está autorizado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden autorizar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'autorizado'
        registro.observaciones = f"Autorizado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔓 AUTORIZACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Autorizado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"✅ Acceso autorizado manualmente por {usuario.username}"
        response_data['autorizado_por'] = usuario.username
        
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def denegar_manual(self, request, pk=None):
        """Denegar manualmente un acceso pendiente o autorizado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'denegado':
            return Response(
                {'error': 'Este registro ya está denegado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden denegar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'denegado'
        registro.observaciones = f"Denegado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔒 DENEGACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Denegado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"❌ Acceso denegado manualmente por {usuario.username}"
        response_data['denegado_por'] = usuario.username
        
        return Response(response_data)
    
    def _es_admin_o_seguridad(self, user):
        """Verificar si el usuario es administrador o personal de seguridad"""
        if user.is_superuser:
            return True
        if getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
            return True
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
            return True
        return False

    @action(detail=True, methods=['delete'])
    def eliminar_registro(self, request, pk=None):
        """Eliminar un registro de acceso (solo administradores)"""
        registro = self.get_object()
        usuario = request.user

        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden eliminar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        registro_id = registro.id
        registro.delete()
        
        return Response({
            'message': f'Registro {registro_id} eliminado exitosamente'
        })

    @action(detail=False, methods=['delete'])
    def limpiar_registros_antiguos(self, request):
        """Limpiar registros antiguos (más de 90 días)"""
        usuario = request.user
        
        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden limpiar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        from datetime import timedelta
        fecha_limite = timezone.now() - timedelta(days=90)
        
        registros_antiguos = RegistroAcceso.objects.filter(
            fecha_hora__lt=fecha_limite
        )
        cantidad = registros_antiguos.count()
        registros_antiguos.delete()
        
        return Response({
            'message': f'Se eliminaron {cantidad} registros antiguos'
        })

    @action(detail=False, methods=['get'])
    def placas_registradas(self, request):
        """Obtener todas las placas registradas para debugging"""
        try:
            # Obtener placas del sistema de acceso
            placas_residentes = PlacaVehiculo.objects.filter(activo=True).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            placas_invitados = PlacaInvitado.objects.filter(
                activo=True,
                fecha_vencimiento__gte=timezone.now()
            ).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro', 'fecha_vencimiento',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            # Obtener placas de los modelos originales
            vehiculos_originales = Vehiculo.objects.all().values(
                'id', 'placa', 'marca', 'modelo', 'color'
            )
            
            invitados_originales = Invitado.objects.filter(
                activo=True,
                vehiculo_placa__isnull=False
            ).values(
                'id', 'nombre', 'vehiculo_placa', 'fecha_inicio', 'fecha_fin',
                residente_nombre=F('residente__persona__nombre')
            )
            
            return Response({
                'sistema_acceso': {
                    'placas_residentes': list(placas_residentes),
                    'placas_invitados': list(placas_invitados),
                    'total_residentes': placas_residentes.count(),
                    'total_invitados': placas_invitados.count()
                },
                'gestion_original': {
                    'vehiculos': list(vehiculos_originales),
                    'invitados': list(invitados_originales),
                    'total_vehiculos': vehiculos_originales.count(),
                    'total_invitados': invitados_originales.count()
                },
                'total_general': {
                    'total_placas': placas_residentes.count() + placas_invitados.count() + vehiculos_originales.count() + invitados_originales.count()
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener placas registradas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def crear_placa_prueba(self, request):
        """Crear una placa de prueba para testing"""
        try:
            data = request.data
            tipo = data.get('tipo', 'residente')  # 'residente' o 'invitado'
            placa = data.get('placa', 'ABC123').upper()
            marca = data.get('marca', 'Toyota')
            modelo = data.get('modelo', 'Corolla')
            color = data.get('color', 'Blanco')
            
            if tipo == 'residente':
                # Crear placa de residente
                residente = Residentes.objects.first()  # Tomar el primer residente
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaVehiculo.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de residente {placa} creada exitosamente',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                    
            elif tipo == 'invitado':
                # Crear placa de invitado
                residente = Residentes.objects.first()
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaInvitado.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'nombre_visitante': data.get('nombre_visitante', 'Visitante Test'),
                        'ci_visitante': data.get('ci_visitante', '12345678'),
                        'fecha_autorizacion': timezone.now(),
                        'fecha_vencimiento': timezone.now() + timedelta(days=7),
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de invitado {placa} creada exitosamente',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear placa de prueba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

        # Placas activas de residentes
        placas_residentes = PlacaVehiculo.objects.filter(activo=True).count()
        # Placas de invitados vigentes
        invitados_activos = PlacaInvitado.objects.filter(
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
                'invitados_activos': invitados_activos
            },
            'ultimos_registros': serializer.data
        })

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
    Residentes, Usuario, Empleado, Vehiculo, Invitado
)
from django.db.models import F
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
    
    def buscar_placa_inteligente(self, placa_detectada):
        """
        Búsqueda inteligente de placas con múltiples estrategias
        Retorna un diccionario con la información encontrada
        """
        resultado = {
            'encontrada': False,
            'tipo': None,
            'objeto': None,
            'info_detallada': {},
            'mensaje_ia': '',
            'confianza_busqueda': 0
        }
        
        if not placa_detectada or len(placa_detectada) < 4:
            return resultado
            
        placa_limpia = placa_detectada.upper().strip()
        
        # Estrategia 1: Búsqueda exacta en PlacaVehiculo (residentes)
        placa_vehiculo = PlacaVehiculo.objects.filter(
            placa__iexact=placa_limpia,
            activo=True
        ).first()
        
        if placa_vehiculo:
            resultado.update({
                'encontrada': True,
                'tipo': 'residente',
                'objeto': placa_vehiculo,
                'info_detallada': {
                    'propietario_nombre': placa_vehiculo.residente.persona.nombre,
                    'vehiculo_info': f"{placa_vehiculo.marca} {placa_vehiculo.modelo} ({placa_vehiculo.color})",
                    'unidad': placa_vehiculo.residente.residentesunidad_set.filter(estado=True).first(),
                    'fecha_registro': placa_vehiculo.fecha_registro
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE REGISTRADO - {placa_vehiculo.residente.persona.nombre}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 2: Búsqueda exacta en PlacaInvitado (invitados activos)
        placa_invitado = PlacaInvitado.objects.filter(
            placa__iexact=placa_limpia,
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        ).first()
        
        if placa_invitado:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado',
                'objeto': placa_invitado,
                'info_detallada': {
                    'visitante_nombre': placa_invitado.nombre_visitante,
                    'propietario_nombre': placa_invitado.residente.persona.nombre,
                    'vehiculo_info': f"{placa_invitado.marca or 'N/A'} {placa_invitado.modelo or 'N/A'} ({placa_invitado.color or 'N/A'})",
                    'fecha_vencimiento': placa_invitado.fecha_vencimiento,
                    'ci_visitante': placa_invitado.ci_visitante
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO REGISTRADO - {placa_invitado.nombre_visitante}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 3: Búsqueda en sistema original de Vehiculos
        vehiculo_original = Vehiculo.objects.filter(placa__iexact=placa_limpia).first()
        if vehiculo_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'vehiculo_original',
                'objeto': vehiculo_original,
                'info_detallada': {
                    'vehiculo_info': f"{vehiculo_original.marca} {vehiculo_original.modelo} ({vehiculo_original.color})",
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO EN SISTEMA ORIGINAL - {vehiculo_original.marca} {vehiculo_original.modelo}",
                'confianza_busqueda': 95
            })
            return resultado
        
        # Estrategia 4: Búsqueda en sistema original de Invitados
        invitado_original = Invitado.objects.filter(
            vehiculo_placa__iexact=placa_limpia,
            activo=True,
            fecha_fin__gte=timezone.now()
        ).first()
        
        if invitado_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado_original',
                'objeto': invitado_original,
                'info_detallada': {
                    'visitante_nombre': invitado_original.nombre,
                    'propietario_nombre': invitado_original.residente.persona.nombre if invitado_original.residente else 'Sin residente',
                    'fecha_fin': invitado_original.fecha_fin
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO EN SISTEMA ORIGINAL - {invitado_original.nombre}",
                'confianza_busqueda': 90
            })
            return resultado
        
        # Estrategia 5: Búsqueda parcial/fuzzy (sin espacios, guiones, etc.)
        variaciones_placa = [
            placa_limpia.replace(' ', ''),
            placa_limpia.replace('-', ''),
            placa_limpia.replace('.', ''),
            placa_limpia.replace(' ', '').replace('-', '').replace('.', '')
        ]
        
        for variacion in variaciones_placa:
            if variacion != placa_limpia and len(variacion) >= 4:
                # Buscar en residentes con variación
                placa_vehiculo_var = PlacaVehiculo.objects.filter(
                    placa__icontains=variacion,
                    activo=True
                ).first()
                
                if placa_vehiculo_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'residente',
                        'objeto': placa_vehiculo_var,
                        'info_detallada': {
                            'propietario_nombre': placa_vehiculo_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_vehiculo_var.marca} {placa_vehiculo_var.modelo} ({placa_vehiculo_var.color})",
                            'placa_original': placa_vehiculo_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE (coincidencia parcial) - {placa_vehiculo_var.residente.persona.nombre}",
                        'confianza_busqueda': 85
                    })
                    return resultado
                
                # Buscar en invitados con variación
                placa_invitado_var = PlacaInvitado.objects.filter(
                    placa__icontains=variacion,
                    activo=True,
                    fecha_vencimiento__gte=timezone.now()
                ).first()
                
                if placa_invitado_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'invitado',
                        'objeto': placa_invitado_var,
                        'info_detallada': {
                            'visitante_nombre': placa_invitado_var.nombre_visitante,
                            'propietario_nombre': placa_invitado_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_invitado_var.marca or 'N/A'} {placa_invitado_var.modelo or 'N/A'}",
                            'placa_original': placa_invitado_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO (coincidencia parcial) - {placa_invitado_var.nombre_visitante}",
                        'confianza_busqueda': 80
                    })
                    return resultado
        
        # No se encontró nada
        resultado.update({
            'mensaje_ia': f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO REGISTRADA EN EL SISTEMA",
            'confianza_busqueda': 0
        })
        
        return resultado

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
        """Registrar un nuevo acceso vehicular con IA mejorada"""
        try:
            data = request.data.copy()

            # Obtener configuración actual
            config = ConfiguracionAcceso.objects.first()
            if not config:
                config = ConfiguracionAcceso.objects.create()

            # Obtener placa detectada
            placa_detectada = data.get('placa_detectada', '').upper().strip()
            
            print(f"\n🔍 INICIANDO BÚSQUEDA INTELIGENTE DE PLACA: '{placa_detectada}'")
            
            # Usar búsqueda inteligente
            resultado_busqueda = self.buscar_placa_inteligente(placa_detectada)
            
            # Obtener parámetros de IA
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            print(f"📊 RESULTADO DE BÚSQUEDA:")
            print(f"   - Encontrada: {resultado_busqueda['encontrada']}")
            print(f"   - Tipo: {resultado_busqueda['tipo']}")
            print(f"   - Confianza: {resultado_busqueda['confianza_busqueda']}%")
            print(f"   - Mensaje IA: {resultado_busqueda['mensaje_ia']}")

            # LÓGICA DE AUTORIZACIÓN MEJORADA
            if resultado_busqueda['encontrada']:
                # ✅ PLACA ENCONTRADA -> AUTORIZADO AUTOMÁTICO
                estado_acceso = 'autorizado'
                ia_autentico = True
                ia_placa_reconocida = True
                ia_vehiculo_reconocido = True
                print(f"🎉 ACCESO AUTORIZADO AUTOMÁTICAMENTE")
            elif ia_confidence >= config.umbral_confianza_placa and ia_placa_reconocida:
                # ⏳ PLACA NO REGISTRADA PERO IA CONFÍA -> PENDIENTE
                estado_acceso = 'pendiente'
                ia_autentico = False
                print(f"⏳ ACCESO PENDIENTE - Requiere autorización manual")
            else:
                # ❌ PLACA NO RECONOCIDA O BAJA CONFIANZA -> DENEGADO
                estado_acceso = 'denegado'
                ia_autentico = False
                print(f"❌ ACCESO DENEGADO - Placa no registrada y baja confianza")

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
                'placa_vehiculo': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'residente' else None,
                'placa_invitado': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'invitado' else None,
            }

            serializer = self.get_serializer(data=registro_data)
            serializer.is_valid(raise_exception=True)
            registro = serializer.save()

            # Preparar respuesta detallada con información de la búsqueda inteligente
            response_data = serializer.data.copy()
            
            # Agregar información detallada del resultado de búsqueda
            response_data['mensaje'] = resultado_busqueda['mensaje_ia']
            response_data['confianza_busqueda'] = resultado_busqueda['confianza_busqueda']
            
            if resultado_busqueda['encontrada']:
                response_data['tipo_propietario'] = resultado_busqueda['tipo']
                response_data.update(resultado_busqueda['info_detallada'])
                
                # Información adicional según el tipo
                if resultado_busqueda['tipo'] == 'residente':
                    unidad = resultado_busqueda['info_detallada'].get('unidad')
                    if unidad:
                        response_data['unidad_numero'] = unidad.id_unidad.numero
                        response_data['unidad_tipo'] = unidad.id_unidad.tipo
                        
                elif resultado_busqueda['tipo'] == 'invitado':
                    response_data['fecha_vencimiento'] = resultado_busqueda['info_detallada'].get('fecha_vencimiento')
                    
            else:
                # Placa no encontrada
                if estado_acceso == 'pendiente':
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ⏳ PLACA '{placa_detectada}' NO REGISTRADA - Requiere verificación manual del administrador o seguridad"
                else:
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO RECONOCIDA - Acceso denegado por baja confianza de IA"

            print(f"\n✅ REGISTRO CREADO EXITOSAMENTE:")
            print(f"   - ID: {registro.id}")
            print(f"   - Estado: {estado_acceso.upper()}")
            print(f"   - Mensaje: {response_data['mensaje']}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al registrar acceso: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def autorizar_manual(self, request, pk=None):
        """Autorizar manualmente un acceso pendiente o denegado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'autorizado':
            return Response(
                {'error': 'Este registro ya está autorizado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden autorizar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'autorizado'
        registro.observaciones = f"Autorizado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔓 AUTORIZACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Autorizado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"✅ Acceso autorizado manualmente por {usuario.username}"
        response_data['autorizado_por'] = usuario.username
        
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def denegar_manual(self, request, pk=None):
        """Denegar manualmente un acceso pendiente o autorizado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'denegado':
            return Response(
                {'error': 'Este registro ya está denegado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden denegar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'denegado'
        registro.observaciones = f"Denegado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔒 DENEGACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Denegado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"❌ Acceso denegado manualmente por {usuario.username}"
        response_data['denegado_por'] = usuario.username
        
        return Response(response_data)
    
    def _es_admin_o_seguridad(self, user):
        """Verificar si el usuario es administrador o personal de seguridad"""
        if user.is_superuser:
            return True
        if getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
            return True
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
            return True
        return False

    @action(detail=True, methods=['delete'])
    def eliminar_registro(self, request, pk=None):
        """Eliminar un registro de acceso (solo administradores)"""
        registro = self.get_object()
        usuario = request.user

        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden eliminar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        registro_id = registro.id
        registro.delete()
        
        return Response({
            'message': f'Registro {registro_id} eliminado exitosamente'
        })

    @action(detail=False, methods=['delete'])
    def limpiar_registros_antiguos(self, request):
        """Limpiar registros antiguos (más de 90 días)"""
        usuario = request.user
        
        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden limpiar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        from datetime import timedelta
        fecha_limite = timezone.now() - timedelta(days=90)
        
        registros_antiguos = RegistroAcceso.objects.filter(
            fecha_hora__lt=fecha_limite
        )
        cantidad = registros_antiguos.count()
        registros_antiguos.delete()
        
        return Response({
            'message': f'Se eliminaron {cantidad} registros antiguos'
        })

    @action(detail=False, methods=['get'])
    def placas_registradas(self, request):
        """Obtener todas las placas registradas para debugging"""
        try:
            # Obtener placas del sistema de acceso
            placas_residentes = PlacaVehiculo.objects.filter(activo=True).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            placas_invitados = PlacaInvitado.objects.filter(
                activo=True,
                fecha_vencimiento__gte=timezone.now()
            ).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro', 'fecha_vencimiento',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            # Obtener placas de los modelos originales
            vehiculos_originales = Vehiculo.objects.all().values(
                'id', 'placa', 'marca', 'modelo', 'color'
            )
            
            invitados_originales = Invitado.objects.filter(
                activo=True,
                vehiculo_placa__isnull=False
            ).values(
                'id', 'nombre', 'vehiculo_placa', 'fecha_inicio', 'fecha_fin',
                residente_nombre=F('residente__persona__nombre')
            )
            
            return Response({
                'sistema_acceso': {
                    'placas_residentes': list(placas_residentes),
                    'placas_invitados': list(placas_invitados),
                    'total_residentes': placas_residentes.count(),
                    'total_invitados': placas_invitados.count()
                },
                'gestion_original': {
                    'vehiculos': list(vehiculos_originales),
                    'invitados': list(invitados_originales),
                    'total_vehiculos': vehiculos_originales.count(),
                    'total_invitados': invitados_originales.count()
                },
                'total_general': {
                    'total_placas': placas_residentes.count() + placas_invitados.count() + vehiculos_originales.count() + invitados_originales.count()
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener placas registradas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def crear_placa_prueba(self, request):
        """Crear una placa de prueba para testing"""
        try:
            data = request.data
            tipo = data.get('tipo', 'residente')  # 'residente' o 'invitado'
            placa = data.get('placa', 'ABC123').upper()
            marca = data.get('marca', 'Toyota')
            modelo = data.get('modelo', 'Corolla')
            color = data.get('color', 'Blanco')
            
            if tipo == 'residente':
                # Crear placa de residente
                residente = Residentes.objects.first()  # Tomar el primer residente
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaVehiculo.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de residente {placa} creada exitosamente',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                    
            elif tipo == 'invitado':
                # Crear placa de invitado
                residente = Residentes.objects.first()
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaInvitado.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'nombre_visitante': data.get('nombre_visitante', 'Visitante Test'),
                        'ci_visitante': data.get('ci_visitante', '12345678'),
                        'fecha_autorizacion': timezone.now(),
                        'fecha_vencimiento': timezone.now() + timedelta(days=7),
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de invitado {placa} creada exitosamente',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear placa de prueba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

        # Placas activas de residentes
        placas_residentes = PlacaVehiculo.objects.filter(activo=True).count()
        # Placas de invitados vigentes
        invitados_activos = PlacaInvitado.objects.filter(
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
                'invitados_activos': invitados_activos
            },
            'ultimos_registros': serializer.data
        })
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
    Residentes, Usuario, Empleado, Vehiculo, Invitado
)
from django.db.models import F
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
    
    def buscar_placa_inteligente(self, placa_detectada):
        """
        Búsqueda inteligente de placas con múltiples estrategias
        Retorna un diccionario con la información encontrada
        """
        resultado = {
            'encontrada': False,
            'tipo': None,
            'objeto': None,
            'info_detallada': {},
            'mensaje_ia': '',
            'confianza_busqueda': 0
        }
        
        if not placa_detectada or len(placa_detectada) < 4:
            return resultado
            
        placa_limpia = placa_detectada.upper().strip()
        
        # Estrategia 1: Búsqueda exacta en PlacaVehiculo (residentes)
        placa_vehiculo = PlacaVehiculo.objects.filter(
            placa__iexact=placa_limpia,
            activo=True
        ).first()
        
        if placa_vehiculo:
            resultado.update({
                'encontrada': True,
                'tipo': 'residente',
                'objeto': placa_vehiculo,
                'info_detallada': {
                    'propietario_nombre': placa_vehiculo.residente.persona.nombre,
                    'vehiculo_info': f"{placa_vehiculo.marca} {placa_vehiculo.modelo} ({placa_vehiculo.color})",
                    'unidad': placa_vehiculo.residente.residentesunidad_set.filter(estado=True).first(),
                    'fecha_registro': placa_vehiculo.fecha_registro
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE REGISTRADO - {placa_vehiculo.residente.persona.nombre}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 2: Búsqueda exacta en PlacaInvitado (invitados activos)
        placa_invitado = PlacaInvitado.objects.filter(
            placa__iexact=placa_limpia,
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        ).first()
        
        if placa_invitado:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado',
                'objeto': placa_invitado,
                'info_detallada': {
                    'visitante_nombre': placa_invitado.nombre_visitante,
                    'propietario_nombre': placa_invitado.residente.persona.nombre,
                    'vehiculo_info': f"{placa_invitado.marca or 'N/A'} {placa_invitado.modelo or 'N/A'} ({placa_invitado.color or 'N/A'})",
                    'fecha_vencimiento': placa_invitado.fecha_vencimiento,
                    'ci_visitante': placa_invitado.ci_visitante
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO REGISTRADO - {placa_invitado.nombre_visitante}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 3: Búsqueda en sistema original de Vehiculos
        vehiculo_original = Vehiculo.objects.filter(placa__iexact=placa_limpia).first()
        if vehiculo_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'vehiculo_original',
                'objeto': vehiculo_original,
                'info_detallada': {
                    'vehiculo_info': f"{vehiculo_original.marca} {vehiculo_original.modelo} ({vehiculo_original.color})",
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO EN SISTEMA ORIGINAL - {vehiculo_original.marca} {vehiculo_original.modelo}",
                'confianza_busqueda': 95
            })
            return resultado
        
        # Estrategia 4: Búsqueda en sistema original de Invitados
        invitado_original = Invitado.objects.filter(
            vehiculo_placa__iexact=placa_limpia,
            activo=True,
            fecha_fin__gte=timezone.now()
        ).first()
        
        if invitado_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado_original',
                'objeto': invitado_original,
                'info_detallada': {
                    'visitante_nombre': invitado_original.nombre,
                    'propietario_nombre': invitado_original.residente.persona.nombre if invitado_original.residente else 'Sin residente',
                    'fecha_fin': invitado_original.fecha_fin
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO EN SISTEMA ORIGINAL - {invitado_original.nombre}",
                'confianza_busqueda': 90
            })
            return resultado
        
        # Estrategia 5: Búsqueda parcial/fuzzy (sin espacios, guiones, etc.)
        variaciones_placa = [
            placa_limpia.replace(' ', ''),
            placa_limpia.replace('-', ''),
            placa_limpia.replace('.', ''),
            placa_limpia.replace(' ', '').replace('-', '').replace('.', '')
        ]
        
        for variacion in variaciones_placa:
            if variacion != placa_limpia and len(variacion) >= 4:
                # Buscar en residentes con variación
                placa_vehiculo_var = PlacaVehiculo.objects.filter(
                    placa__icontains=variacion,
                    activo=True
                ).first()
                
                if placa_vehiculo_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'residente',
                        'objeto': placa_vehiculo_var,
                        'info_detallada': {
                            'propietario_nombre': placa_vehiculo_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_vehiculo_var.marca} {placa_vehiculo_var.modelo} ({placa_vehiculo_var.color})",
                            'placa_original': placa_vehiculo_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE (coincidencia parcial) - {placa_vehiculo_var.residente.persona.nombre}",
                        'confianza_busqueda': 85
                    })
                    return resultado
                
                # Buscar en invitados con variación
                placa_invitado_var = PlacaInvitado.objects.filter(
                    placa__icontains=variacion,
                    activo=True,
                    fecha_vencimiento__gte=timezone.now()
                ).first()
                
                if placa_invitado_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'invitado',
                        'objeto': placa_invitado_var,
                        'info_detallada': {
                            'visitante_nombre': placa_invitado_var.nombre_visitante,
                            'propietario_nombre': placa_invitado_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_invitado_var.marca or 'N/A'} {placa_invitado_var.modelo or 'N/A'}",
                            'placa_original': placa_invitado_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO (coincidencia parcial) - {placa_invitado_var.nombre_visitante}",
                        'confianza_busqueda': 80
                    })
                    return resultado
        
        # No se encontró nada
        resultado.update({
            'mensaje_ia': f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO REGISTRADA EN EL SISTEMA",
            'confianza_busqueda': 0
        })
        
        return resultado

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
        """Registrar un nuevo acceso vehicular con IA mejorada"""
        try:
            data = request.data.copy()

            # Obtener configuración actual
            config = ConfiguracionAcceso.objects.first()
            if not config:
                config = ConfiguracionAcceso.objects.create()

            # Obtener placa detectada
            placa_detectada = data.get('placa_detectada', '').upper().strip()
            
            print(f"\n🔍 INICIANDO BÚSQUEDA INTELIGENTE DE PLACA: '{placa_detectada}'")
            
            # Usar búsqueda inteligente
            resultado_busqueda = self.buscar_placa_inteligente(placa_detectada)
            
            # Obtener parámetros de IA
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            print(f"📊 RESULTADO DE BÚSQUEDA:")
            print(f"   - Encontrada: {resultado_busqueda['encontrada']}")
            print(f"   - Tipo: {resultado_busqueda['tipo']}")
            print(f"   - Confianza: {resultado_busqueda['confianza_busqueda']}%")
            print(f"   - Mensaje IA: {resultado_busqueda['mensaje_ia']}")

            # LÓGICA DE AUTORIZACIÓN MEJORADA
            if resultado_busqueda['encontrada']:
                # ✅ PLACA ENCONTRADA -> AUTORIZADO AUTOMÁTICO
                estado_acceso = 'autorizado'
                ia_autentico = True
                ia_placa_reconocida = True
                ia_vehiculo_reconocido = True
                print(f"🎉 ACCESO AUTORIZADO AUTOMÁTICAMENTE")
            elif ia_confidence >= config.umbral_confianza_placa and ia_placa_reconocida:
                # ⏳ PLACA NO REGISTRADA PERO IA CONFÍA -> PENDIENTE
                estado_acceso = 'pendiente'
                ia_autentico = False
                print(f"⏳ ACCESO PENDIENTE - Requiere autorización manual")
            else:
                # ❌ PLACA NO RECONOCIDA O BAJA CONFIANZA -> DENEGADO
                estado_acceso = 'denegado'
                ia_autentico = False
                print(f"❌ ACCESO DENEGADO - Placa no registrada y baja confianza")

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
                'placa_vehiculo': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'residente' else None,
                'placa_invitado': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'invitado' else None,
            }

            serializer = self.get_serializer(data=registro_data)
            serializer.is_valid(raise_exception=True)
            registro = serializer.save()

            # Preparar respuesta detallada con información de la búsqueda inteligente
            response_data = serializer.data.copy()
            
            # Agregar información detallada del resultado de búsqueda
            response_data['mensaje'] = resultado_busqueda['mensaje_ia']
            response_data['confianza_busqueda'] = resultado_busqueda['confianza_busqueda']
            
            if resultado_busqueda['encontrada']:
                response_data['tipo_propietario'] = resultado_busqueda['tipo']
                response_data.update(resultado_busqueda['info_detallada'])
                
                # Información adicional según el tipo
                if resultado_busqueda['tipo'] == 'residente':
                    unidad = resultado_busqueda['info_detallada'].get('unidad')
                    if unidad:
                        response_data['unidad_numero'] = unidad.id_unidad.numero
                        response_data['unidad_tipo'] = unidad.id_unidad.tipo
                        
                elif resultado_busqueda['tipo'] == 'invitado':
                    response_data['fecha_vencimiento'] = resultado_busqueda['info_detallada'].get('fecha_vencimiento')
                    
            else:
                # Placa no encontrada
                if estado_acceso == 'pendiente':
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ⏳ PLACA '{placa_detectada}' NO REGISTRADA - Requiere verificación manual del administrador o seguridad"
                else:
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO RECONOCIDA - Acceso denegado por baja confianza de IA"

            print(f"\n✅ REGISTRO CREADO EXITOSAMENTE:")
            print(f"   - ID: {registro.id}")
            print(f"   - Estado: {estado_acceso.upper()}")
            print(f"   - Mensaje: {response_data['mensaje']}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al registrar acceso: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def autorizar_manual(self, request, pk=None):
        """Autorizar manualmente un acceso pendiente o denegado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'autorizado':
            return Response(
                {'error': 'Este registro ya está autorizado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden autorizar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'autorizado'
        registro.observaciones = f"Autorizado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔓 AUTORIZACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Autorizado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"✅ Acceso autorizado manualmente por {usuario.username}"
        response_data['autorizado_por'] = usuario.username
        
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def denegar_manual(self, request, pk=None):
        """Denegar manualmente un acceso pendiente o autorizado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'denegado':
            return Response(
                {'error': 'Este registro ya está denegado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden denegar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'denegado'
        registro.observaciones = f"Denegado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔒 DENEGACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Denegado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"❌ Acceso denegado manualmente por {usuario.username}"
        response_data['denegado_por'] = usuario.username
        
        return Response(response_data)
    
    def _es_admin_o_seguridad(self, user):
        """Verificar si el usuario es administrador o personal de seguridad"""
        if user.is_superuser:
            return True
        if getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
            return True
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
            return True
        return False

    @action(detail=True, methods=['delete'])
    def eliminar_registro(self, request, pk=None):
        """Eliminar un registro de acceso (solo administradores)"""
        registro = self.get_object()
        usuario = request.user

        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden eliminar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        registro_id = registro.id
        registro.delete()
        
        return Response({
            'message': f'Registro {registro_id} eliminado exitosamente'
        })

    @action(detail=False, methods=['delete'])
    def limpiar_registros_antiguos(self, request):
        """Limpiar registros antiguos (más de 90 días)"""
        usuario = request.user
        
        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden limpiar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        from datetime import timedelta
        fecha_limite = timezone.now() - timedelta(days=90)
        
        registros_antiguos = RegistroAcceso.objects.filter(
            fecha_hora__lt=fecha_limite
        )
        cantidad = registros_antiguos.count()
        registros_antiguos.delete()
        
        return Response({
            'message': f'Se eliminaron {cantidad} registros antiguos'
        })

    @action(detail=False, methods=['get'])
    def placas_registradas(self, request):
        """Obtener todas las placas registradas para debugging"""
        try:
            # Obtener placas del sistema de acceso
            placas_residentes = PlacaVehiculo.objects.filter(activo=True).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            placas_invitados = PlacaInvitado.objects.filter(
                activo=True,
                fecha_vencimiento__gte=timezone.now()
            ).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro', 'fecha_vencimiento',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            # Obtener placas de los modelos originales
            vehiculos_originales = Vehiculo.objects.all().values(
                'id', 'placa', 'marca', 'modelo', 'color'
            )
            
            invitados_originales = Invitado.objects.filter(
                activo=True,
                vehiculo_placa__isnull=False
            ).values(
                'id', 'nombre', 'vehiculo_placa', 'fecha_inicio', 'fecha_fin',
                residente_nombre=F('residente__persona__nombre')
            )
            
            return Response({
                'sistema_acceso': {
                    'placas_residentes': list(placas_residentes),
                    'placas_invitados': list(placas_invitados),
                    'total_residentes': placas_residentes.count(),
                    'total_invitados': placas_invitados.count()
                },
                'gestion_original': {
                    'vehiculos': list(vehiculos_originales),
                    'invitados': list(invitados_originales),
                    'total_vehiculos': vehiculos_originales.count(),
                    'total_invitados': invitados_originales.count()
                },
                'total_general': {
                    'total_placas': placas_residentes.count() + placas_invitados.count() + vehiculos_originales.count() + invitados_originales.count()
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener placas registradas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def crear_placa_prueba(self, request):
        """Crear una placa de prueba para testing"""
        try:
            data = request.data
            tipo = data.get('tipo', 'residente')  # 'residente' o 'invitado'
            placa = data.get('placa', 'ABC123').upper()
            marca = data.get('marca', 'Toyota')
            modelo = data.get('modelo', 'Corolla')
            color = data.get('color', 'Blanco')
            
            if tipo == 'residente':
                # Crear placa de residente
                residente = Residentes.objects.first()  # Tomar el primer residente
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaVehiculo.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de residente {placa} creada exitosamente',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                    
            elif tipo == 'invitado':
                # Crear placa de invitado
                residente = Residentes.objects.first()
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaInvitado.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'nombre_visitante': data.get('nombre_visitante', 'Visitante Test'),
                        'ci_visitante': data.get('ci_visitante', '12345678'),
                        'fecha_autorizacion': timezone.now(),
                        'fecha_vencimiento': timezone.now() + timedelta(days=7),
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de invitado {placa} creada exitosamente',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear placa de prueba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

        # Placas activas de residentes
        placas_residentes = PlacaVehiculo.objects.filter(activo=True).count()
        # Placas de invitados vigentes
        invitados_activos = PlacaInvitado.objects.filter(
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
                'invitados_activos': invitados_activos
            },
            'ultimos_registros': serializer.data
        })

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
    Residentes, Usuario, Empleado, Vehiculo, Invitado
)
from django.db.models import F
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
    
    def buscar_placa_inteligente(self, placa_detectada):
        """
        Búsqueda inteligente de placas con múltiples estrategias
        Retorna un diccionario con la información encontrada
        """
        resultado = {
            'encontrada': False,
            'tipo': None,
            'objeto': None,
            'info_detallada': {},
            'mensaje_ia': '',
            'confianza_busqueda': 0
        }
        
        if not placa_detectada or len(placa_detectada) < 4:
            return resultado
            
        placa_limpia = placa_detectada.upper().strip()
        
        # Estrategia 1: Búsqueda exacta en PlacaVehiculo (residentes)
        placa_vehiculo = PlacaVehiculo.objects.filter(
            placa__iexact=placa_limpia,
            activo=True
        ).first()
        
        if placa_vehiculo:
            resultado.update({
                'encontrada': True,
                'tipo': 'residente',
                'objeto': placa_vehiculo,
                'info_detallada': {
                    'propietario_nombre': placa_vehiculo.residente.persona.nombre,
                    'vehiculo_info': f"{placa_vehiculo.marca} {placa_vehiculo.modelo} ({placa_vehiculo.color})",
                    'unidad': placa_vehiculo.residente.residentesunidad_set.filter(estado=True).first(),
                    'fecha_registro': placa_vehiculo.fecha_registro
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE REGISTRADO - {placa_vehiculo.residente.persona.nombre}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 2: Búsqueda exacta en PlacaInvitado (invitados activos)
        placa_invitado = PlacaInvitado.objects.filter(
            placa__iexact=placa_limpia,
            activo=True,
            fecha_vencimiento__gte=timezone.now()
        ).first()
        
        if placa_invitado:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado',
                'objeto': placa_invitado,
                'info_detallada': {
                    'visitante_nombre': placa_invitado.nombre_visitante,
                    'propietario_nombre': placa_invitado.residente.persona.nombre,
                    'vehiculo_info': f"{placa_invitado.marca or 'N/A'} {placa_invitado.modelo or 'N/A'} ({placa_invitado.color or 'N/A'})",
                    'fecha_vencimiento': placa_invitado.fecha_vencimiento,
                    'ci_visitante': placa_invitado.ci_visitante
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO REGISTRADO - {placa_invitado.nombre_visitante}",
                'confianza_busqueda': 100
            })
            return resultado
        
        # Estrategia 3: Búsqueda en sistema original de Vehiculos
        vehiculo_original = Vehiculo.objects.filter(placa__iexact=placa_limpia).first()
        if vehiculo_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'vehiculo_original',
                'objeto': vehiculo_original,
                'info_detallada': {
                    'vehiculo_info': f"{vehiculo_original.marca} {vehiculo_original.modelo} ({vehiculo_original.color})",
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO EN SISTEMA ORIGINAL - {vehiculo_original.marca} {vehiculo_original.modelo}",
                'confianza_busqueda': 95
            })
            return resultado
        
        # Estrategia 4: Búsqueda en sistema original de Invitados
        invitado_original = Invitado.objects.filter(
            vehiculo_placa__iexact=placa_limpia,
            activo=True,
            fecha_fin__gte=timezone.now()
        ).first()
        
        if invitado_original:
            resultado.update({
                'encontrada': True,
                'tipo': 'invitado_original',
                'objeto': invitado_original,
                'info_detallada': {
                    'visitante_nombre': invitado_original.nombre,
                    'propietario_nombre': invitado_original.residente.persona.nombre if invitado_original.residente else 'Sin residente',
                    'fecha_fin': invitado_original.fecha_fin
                },
                'mensaje_ia': f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO EN SISTEMA ORIGINAL - {invitado_original.nombre}",
                'confianza_busqueda': 90
            })
            return resultado
        
        # Estrategia 5: Búsqueda parcial/fuzzy (sin espacios, guiones, etc.)
        variaciones_placa = [
            placa_limpia.replace(' ', ''),
            placa_limpia.replace('-', ''),
            placa_limpia.replace('.', ''),
            placa_limpia.replace(' ', '').replace('-', '').replace('.', '')
        ]
        
        for variacion in variaciones_placa:
            if variacion != placa_limpia and len(variacion) >= 4:
                # Buscar en residentes con variación
                placa_vehiculo_var = PlacaVehiculo.objects.filter(
                    placa__icontains=variacion,
                    activo=True
                ).first()
                
                if placa_vehiculo_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'residente',
                        'objeto': placa_vehiculo_var,
                        'info_detallada': {
                            'propietario_nombre': placa_vehiculo_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_vehiculo_var.marca} {placa_vehiculo_var.modelo} ({placa_vehiculo_var.color})",
                            'placa_original': placa_vehiculo_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE RESIDENTE (coincidencia parcial) - {placa_vehiculo_var.residente.persona.nombre}",
                        'confianza_busqueda': 85
                    })
                    return resultado
                
                # Buscar en invitados con variación
                placa_invitado_var = PlacaInvitado.objects.filter(
                    placa__icontains=variacion,
                    activo=True,
                    fecha_vencimiento__gte=timezone.now()
                ).first()
                
                if placa_invitado_var:
                    resultado.update({
                        'encontrada': True,
                        'tipo': 'invitado',
                        'objeto': placa_invitado_var,
                        'info_detallada': {
                            'visitante_nombre': placa_invitado_var.nombre_visitante,
                            'propietario_nombre': placa_invitado_var.residente.persona.nombre,
                            'vehiculo_info': f"{placa_invitado_var.marca or 'N/A'} {placa_invitado_var.modelo or 'N/A'}",
                            'placa_original': placa_invitado_var.placa,
                            'placa_detectada': placa_detectada
                        },
                        'mensaje_ia': f"🤖 IA VERIFICA: ✅ VEHÍCULO DE INVITADO (coincidencia parcial) - {placa_invitado_var.nombre_visitante}",
                        'confianza_busqueda': 80
                    })
                    return resultado
        
        # No se encontró nada
        resultado.update({
            'mensaje_ia': f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO REGISTRADA EN EL SISTEMA",
            'confianza_busqueda': 0
        })
        
        return resultado

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
        """Registrar un nuevo acceso vehicular con IA mejorada"""
        try:
            data = request.data.copy()

            # Obtener configuración actual
            config = ConfiguracionAcceso.objects.first()
            if not config:
                config = ConfiguracionAcceso.objects.create()

            # Obtener placa detectada
            placa_detectada = data.get('placa_detectada', '').upper().strip()
            
            print(f"\n🔍 INICIANDO BÚSQUEDA INTELIGENTE DE PLACA: '{placa_detectada}'")
            
            # Usar búsqueda inteligente
            resultado_busqueda = self.buscar_placa_inteligente(placa_detectada)
            
            # Obtener parámetros de IA
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            print(f"📊 RESULTADO DE BÚSQUEDA:")
            print(f"   - Encontrada: {resultado_busqueda['encontrada']}")
            print(f"   - Tipo: {resultado_busqueda['tipo']}")
            print(f"   - Confianza: {resultado_busqueda['confianza_busqueda']}%")
            print(f"   - Mensaje IA: {resultado_busqueda['mensaje_ia']}")

            # LÓGICA DE AUTORIZACIÓN MEJORADA
            if resultado_busqueda['encontrada']:
                # ✅ PLACA ENCONTRADA -> AUTORIZADO AUTOMÁTICO
                estado_acceso = 'autorizado'
                ia_autentico = True
                ia_placa_reconocida = True
                ia_vehiculo_reconocido = True
                print(f"🎉 ACCESO AUTORIZADO AUTOMÁTICAMENTE")
            elif ia_confidence >= config.umbral_confianza_placa and ia_placa_reconocida:
                # ⏳ PLACA NO REGISTRADA PERO IA CONFÍA -> PENDIENTE
                estado_acceso = 'pendiente'
                ia_autentico = False
                print(f"⏳ ACCESO PENDIENTE - Requiere autorización manual")
            else:
                # ❌ PLACA NO RECONOCIDA O BAJA CONFIANZA -> DENEGADO
                estado_acceso = 'denegado'
                ia_autentico = False
                print(f"❌ ACCESO DENEGADO - Placa no registrada y baja confianza")

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
                'placa_vehiculo': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'residente' else None,
                'placa_invitado': resultado_busqueda['objeto'] if resultado_busqueda['tipo'] == 'invitado' else None,
            }

            serializer = self.get_serializer(data=registro_data)
            serializer.is_valid(raise_exception=True)
            registro = serializer.save()

            # Preparar respuesta detallada con información de la búsqueda inteligente
            response_data = serializer.data.copy()
            
            # Agregar información detallada del resultado de búsqueda
            response_data['mensaje'] = resultado_busqueda['mensaje_ia']
            response_data['confianza_busqueda'] = resultado_busqueda['confianza_busqueda']
            
            if resultado_busqueda['encontrada']:
                response_data['tipo_propietario'] = resultado_busqueda['tipo']
                response_data.update(resultado_busqueda['info_detallada'])
                
                # Información adicional según el tipo
                if resultado_busqueda['tipo'] == 'residente':
                    unidad = resultado_busqueda['info_detallada'].get('unidad')
                    if unidad:
                        response_data['unidad_numero'] = unidad.id_unidad.numero
                        response_data['unidad_tipo'] = unidad.id_unidad.tipo
                        
                elif resultado_busqueda['tipo'] == 'invitado':
                    response_data['fecha_vencimiento'] = resultado_busqueda['info_detallada'].get('fecha_vencimiento')
                    
            else:
                # Placa no encontrada
                if estado_acceso == 'pendiente':
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ⏳ PLACA '{placa_detectada}' NO REGISTRADA - Requiere verificación manual del administrador o seguridad"
                else:
                    response_data['mensaje'] = f"🤖 IA VERIFICA: ❌ PLACA '{placa_detectada}' NO RECONOCIDA - Acceso denegado por baja confianza de IA"

            print(f"\n✅ REGISTRO CREADO EXITOSAMENTE:")
            print(f"   - ID: {registro.id}")
            print(f"   - Estado: {estado_acceso.upper()}")
            print(f"   - Mensaje: {response_data['mensaje']}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error al registrar acceso: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def autorizar_manual(self, request, pk=None):
        """Autorizar manualmente un acceso pendiente o denegado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'autorizado':
            return Response(
                {'error': 'Este registro ya está autorizado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden autorizar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'autorizado'
        registro.observaciones = f"Autorizado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔓 AUTORIZACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Autorizado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"✅ Acceso autorizado manualmente por {usuario.username}"
        response_data['autorizado_por'] = usuario.username
        
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def denegar_manual(self, request, pk=None):
        """Denegar manualmente un acceso pendiente o autorizado"""
        registro = self.get_object()
        usuario = request.user

        if registro.estado_acceso == 'denegado':
            return Response(
                {'error': 'Este registro ya está denegado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permisos
        if not self._es_admin_o_seguridad(usuario):
            return Response(
                {'error': 'Solo administradores y personal de seguridad pueden denegar accesos'},
                status=status.HTTP_403_FORBIDDEN
            )

        estado_anterior = registro.estado_acceso
        registro.estado_acceso = 'denegado'
        registro.observaciones = f"Denegado manualmente por {usuario.username} (era: {estado_anterior})"
        registro.save()

        print(f"🔒 DENEGACIÓN MANUAL:")
        print(f"   - Registro ID: {registro.id}")
        print(f"   - Placa: {registro.placa_detectada}")
        print(f"   - Denegado por: {usuario.username}")
        print(f"   - Estado anterior: {estado_anterior}")

        serializer = self.get_serializer(registro)
        response_data = serializer.data.copy()
        response_data['mensaje'] = f"❌ Acceso denegado manualmente por {usuario.username}"
        response_data['denegado_por'] = usuario.username
        
        return Response(response_data)
    
    def _es_admin_o_seguridad(self, user):
        """Verificar si el usuario es administrador o personal de seguridad"""
        if user.is_superuser:
            return True
        if getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
            return True
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
            return True
        return False

    @action(detail=True, methods=['delete'])
    def eliminar_registro(self, request, pk=None):
        """Eliminar un registro de acceso (solo administradores)"""
        registro = self.get_object()
        usuario = request.user

        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden eliminar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        registro_id = registro.id
        registro.delete()
        
        return Response({
            'message': f'Registro {registro_id} eliminado exitosamente'
        })

    @action(detail=False, methods=['delete'])
    def limpiar_registros_antiguos(self, request):
        """Limpiar registros antiguos (más de 90 días)"""
        usuario = request.user
        
        # Verificar permisos de administrador
        if not (usuario.is_superuser or 
                (usuario.rol and usuario.rol.nombre == 'Administrador')):
            return Response(
                {'error': 'Solo administradores pueden limpiar registros'},
                status=status.HTTP_403_FORBIDDEN
            )

        from datetime import timedelta
        fecha_limite = timezone.now() - timedelta(days=90)
        
        registros_antiguos = RegistroAcceso.objects.filter(
            fecha_hora__lt=fecha_limite
        )
        cantidad = registros_antiguos.count()
        registros_antiguos.delete()
        
        return Response({
            'message': f'Se eliminaron {cantidad} registros antiguos'
        })

    @action(detail=False, methods=['get'])
    def placas_registradas(self, request):
        """Obtener todas las placas registradas para debugging"""
        try:
            # Obtener placas del sistema de acceso
            placas_residentes = PlacaVehiculo.objects.filter(activo=True).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            placas_invitados = PlacaInvitado.objects.filter(
                activo=True,
                fecha_vencimiento__gte=timezone.now()
            ).values(
                'id', 'placa', 'marca', 'modelo', 'color', 'fecha_registro', 'fecha_vencimiento',
                residente_nombre=F('residente__persona__nombre'),
                residente_email=F('residente__persona__email')
            )
            
            # Obtener placas de los modelos originales
            vehiculos_originales = Vehiculo.objects.all().values(
                'id', 'placa', 'marca', 'modelo', 'color'
            )
            
            invitados_originales = Invitado.objects.filter(
                activo=True,
                vehiculo_placa__isnull=False
            ).values(
                'id', 'nombre', 'vehiculo_placa', 'fecha_inicio', 'fecha_fin',
                residente_nombre=F('residente__persona__nombre')
            )
            
            return Response({
                'sistema_acceso': {
                    'placas_residentes': list(placas_residentes),
                    'placas_invitados': list(placas_invitados),
                    'total_residentes': placas_residentes.count(),
                    'total_invitados': placas_invitados.count()
                },
                'gestion_original': {
                    'vehiculos': list(vehiculos_originales),
                    'invitados': list(invitados_originales),
                    'total_vehiculos': vehiculos_originales.count(),
                    'total_invitados': invitados_originales.count()
                },
                'total_general': {
                    'total_placas': placas_residentes.count() + placas_invitados.count() + vehiculos_originales.count() + invitados_originales.count()
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error al obtener placas registradas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def crear_placa_prueba(self, request):
        """Crear una placa de prueba para testing"""
        try:
            data = request.data
            tipo = data.get('tipo', 'residente')  # 'residente' o 'invitado'
            placa = data.get('placa', 'ABC123').upper()
            marca = data.get('marca', 'Toyota')
            modelo = data.get('modelo', 'Corolla')
            color = data.get('color', 'Blanco')
            
            if tipo == 'residente':
                # Crear placa de residente
                residente = Residentes.objects.first()  # Tomar el primer residente
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaVehiculo.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de residente {placa} creada exitosamente',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaVehiculoSerializer(placa_obj).data
                    })
                    
            elif tipo == 'invitado':
                # Crear placa de invitado
                residente = Residentes.objects.first()
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                placa_obj, created = PlacaInvitado.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'nombre_visitante': data.get('nombre_visitante', 'Visitante Test'),
                        'ci_visitante': data.get('ci_visitante', '12345678'),
                        'fecha_autorizacion': timezone.now(),
                        'fecha_vencimiento': timezone.now() + timedelta(days=7),
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de invitado {placa} creada exitosamente',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
                else:
                    return Response({
                        'message': f'Placa {placa} ya existe',
                        'placa': PlacaInvitadoSerializer(placa_obj).data
                    })
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear placa de prueba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

        # Placas activas de residentes
        placas_residentes = PlacaVehiculo.objects.filter(activo=True).count()
        # Placas de invitados vigentes
        invitados_activos = PlacaInvitado.objects.filter(
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
                'invitados_activos': invitados_activos
            },
            'ultimos_registros': serializer.data
        })
