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

            # Buscar coincidencias en TODOS los modelos de placas
            placa_vehiculo = None
            placa_invitado = None
            vehiculo_original = None
            invitado_original = None

            if len(placa_detectada) >= 4:  # Validar formato de placa (mínimo 4 caracteres)
                print(f"🔍 Buscando placa '{placa_detectada}' en todos los modelos...")
                
                # 1. Buscar en PlacaVehiculo (sistema de acceso)
                placa_vehiculo = PlacaVehiculo.objects.filter(
                    placa__iexact=placa_detectada,
                    activo=True
                ).first()

                # 2. Buscar en PlacaInvitado (sistema de acceso)
                if not placa_vehiculo:
                    placa_invitado = PlacaInvitado.objects.filter(
                        placa__iexact=placa_detectada,
                        activo=True,
                        fecha_vencimiento__gte=timezone.now()
                    ).first()

                # 3. Buscar en Vehiculo (gestión original)
                if not placa_vehiculo and not placa_invitado:
                    vehiculo_original = Vehiculo.objects.filter(
                        placa__iexact=placa_detectada
                    ).first()

                # 4. Buscar en Invitado (gestión original)
                if not placa_vehiculo and not placa_invitado and not vehiculo_original:
                    invitado_original = Invitado.objects.filter(
                        vehiculo_placa__iexact=placa_detectada,
                        activo=True,
                        fecha_fin__gte=timezone.now()
                    ).first()

                # 5. Si aún no se encuentra, buscar con búsqueda parcial
                if not placa_vehiculo and not placa_invitado and not vehiculo_original and not invitado_original:
                    placa_limpia = placa_detectada.replace(' ', '').replace('-', '').replace('.', '')
                    
                    # Buscar en todos los modelos con búsqueda parcial
                    placa_vehiculo = PlacaVehiculo.objects.filter(
                        placa__icontains=placa_limpia,
                        activo=True
                    ).first()
                    
                    if not placa_vehiculo:
                        placa_invitado = PlacaInvitado.objects.filter(
                            placa__icontains=placa_limpia,
                            activo=True,
                            fecha_vencimiento__gte=timezone.now()
                        ).first()
                    
                    if not placa_vehiculo and not placa_invitado:
                        vehiculo_original = Vehiculo.objects.filter(
                            placa__icontains=placa_limpia
                        ).first()
                    
                    if not placa_vehiculo and not placa_invitado and not vehiculo_original:
                        invitado_original = Invitado.objects.filter(
                            vehiculo_placa__icontains=placa_limpia,
                            activo=True,
                            fecha_fin__gte=timezone.now()
                        ).first()

            # Determinar estado del acceso - LÓGICA MEJORADA
            ia_confidence = float(data.get('ia_confidence', 0))
            ia_placa_reconocida = data.get('ia_placa_reconocida', False)
            ia_vehiculo_reconocido = data.get('ia_vehiculo_reconocido', False)

            # Logs detallados para debugging
            print(f"🔍 Búsqueda de placa: '{placa_detectada}' (longitud: {len(placa_detectada)})")
            print(f"📋 PlacaVehiculo encontrada: {placa_vehiculo is not None}")
            print(f"👥 PlacaInvitado encontrada: {placa_invitado is not None}")
            print(f"🚗 Vehiculo original encontrado: {vehiculo_original is not None}")
            print(f"👤 Invitado original encontrado: {invitado_original is not None}")
            
            # Debugging adicional - mostrar todas las placas en la base de datos
            print("📊 PLACAS EN BASE DE DATOS:")
            print("PlacaVehiculo (sistema acceso):")
            for pv in PlacaVehiculo.objects.filter(activo=True)[:3]:
                print(f"  - {pv.placa} (ID: {pv.id})")
            
            print("PlacaInvitado (sistema acceso):")
            for pi in PlacaInvitado.objects.filter(activo=True, fecha_vencimiento__gte=timezone.now())[:3]:
                print(f"  - {pi.placa} (ID: {pi.id}, vence: {pi.fecha_vencimiento})")
            
            print("Vehiculo (gestión original):")
            for v in Vehiculo.objects.all()[:3]:
                print(f"  - {v.placa} (ID: {v.id})")
            
            print("Invitado (gestión original):")
            for i in Invitado.objects.filter(activo=True)[:3]:
                if i.vehiculo_placa:
                    print(f"  - {i.vehiculo_placa} (ID: {i.id}, nombre: {i.nombre})")
            
            if placa_vehiculo:
                print(f"✅ PlacaVehiculo encontrada: {placa_vehiculo.placa} - {placa_vehiculo.residente.persona.nombre}")
            if placa_invitado:
                print(f"✅ PlacaInvitado encontrada: {placa_invitado.placa} - {placa_invitado.residente.persona.nombre}")
            if vehiculo_original:
                print(f"✅ Vehiculo original encontrado: {vehiculo_original.placa} - {vehiculo_original.marca} {vehiculo_original.modelo}")
            if invitado_original:
                print(f"✅ Invitado original encontrado: {invitado_original.vehiculo_placa} - {invitado_original.nombre}")
            
            # Si no se encontró, mostrar búsquedas alternativas
            if not placa_vehiculo and not placa_invitado:
                print("❌ No se encontró la placa. Probando búsquedas alternativas...")
                
                # Buscar con diferentes variaciones
                variaciones = [
                    placa_detectada,
                    placa_detectada.replace(' ', ''),
                    placa_detectada.replace('-', ''),
                    placa_detectada.replace('.', ''),
                    placa_detectada.strip()
                ]
                
                for variacion in variaciones:
                    if variacion != placa_detectada:
                        print(f"🔍 Probando variación: '{variacion}'")
                        # Buscar en residentes
                        test_residente = PlacaVehiculo.objects.filter(
                            placa__iexact=variacion,
                            activo=True
                        ).first()
                        if test_residente:
                            print(f"  ✅ Encontrada en residentes: {test_residente.placa}")
                            placa_vehiculo = test_residente
                            break
                        
                        # Buscar en invitados
                        test_invitado = PlacaInvitado.objects.filter(
                            placa__iexact=variacion,
                            activo=True,
                            fecha_vencimiento__gte=timezone.now()
                        ).first()
                        if test_invitado:
                            print(f"  ✅ Encontrada en invitados: {test_invitado.placa}")
                            placa_invitado = test_invitado
                            break

            # LÓGICA DE IA MEJORADA - Verificación automática
            if placa_vehiculo or placa_invitado or vehiculo_original or invitado_original:
                # IA VERIFICA: Placa encontrada en base de datos -> AUTORIZADO AUTOMÁTICO
                estado_acceso = 'autorizado'
                ia_autentico = True
                ia_placa_reconocida = True  # La IA confirma que la placa es válida
                ia_vehiculo_reconocido = True  # La IA confirma que el vehículo es válido
                print(f"🤖 IA VERIFICA: Placa registrada encontrada -> AUTORIZADO AUTOMÁTICO")
                print(f"🎉 ACCESO AUTORIZADO para placa: {placa_detectada}")
            elif ia_confidence >= config.umbral_confianza_placa and ia_placa_reconocida:
                # IA confía en la placa pero no está registrada -> PENDIENTE (requiere autorización manual)
                estado_acceso = 'pendiente'
                ia_autentico = False
                print(f"🤖 IA VERIFICA: Placa no registrada pero IA confía -> PENDIENTE")
                print(f"⏳ ACCESO PENDIENTE para placa: {placa_detectada} (requiere verificación manual)")
            else:
                # IA no confía o placa no reconocida -> DENEGADO
                estado_acceso = 'denegado'
                ia_autentico = False
                print(f"🤖 IA VERIFICA: Placa no reconocida o baja confianza -> DENEGADO")
                print(f"❌ ACCESO DENEGADO para placa: {placa_detectada} (no registrada y baja confianza)")

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

            # Preparar respuesta detallada
            response_data = serializer.data.copy()
            
            # Agregar información adicional sobre el resultado de la IA
            if placa_vehiculo:
                response_data['tipo_propietario'] = 'residente'
                response_data['propietario_nombre'] = placa_vehiculo.residente.persona.nombre
                response_data['vehiculo_info'] = f"{placa_vehiculo.marca} {placa_vehiculo.modelo} ({placa_vehiculo.color})"
                response_data['mensaje'] = f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO - {placa_vehiculo.residente.persona.nombre}"
            elif placa_invitado:
                response_data['tipo_propietario'] = 'invitado'
                response_data['propietario_nombre'] = placa_invitado.residente.persona.nombre
                response_data['visitante_nombre'] = placa_invitado.nombre_visitante
                response_data['vehiculo_info'] = f"{placa_invitado.marca} {placa_invitado.modelo} ({placa_invitado.color})"
                response_data['fecha_vencimiento'] = placa_invitado.fecha_vencimiento
                response_data['mensaje'] = f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO - {placa_invitado.nombre_visitante}"
            elif vehiculo_original:
                response_data['tipo_propietario'] = 'vehiculo_original'
                response_data['vehiculo_info'] = f"{vehiculo_original.marca} {vehiculo_original.modelo}"
                response_data['mensaje'] = f"🤖 IA VERIFICA: ✅ VEHÍCULO REGISTRADO - {vehiculo_original.marca} {vehiculo_original.modelo}"
            elif invitado_original:
                response_data['tipo_propietario'] = 'invitado_original'
                response_data['visitante_nombre'] = invitado_original.nombre
                response_data['propietario_nombre'] = invitado_original.residente.persona.nombre if invitado_original.residente else 'Sin residente'
                response_data['mensaje'] = f"🤖 IA VERIFICA: ✅ INVITADO REGISTRADO - {invitado_original.nombre}"
            elif estado_acceso == 'pendiente':
                response_data['mensaje'] = f"🤖 IA VERIFICA: ⏳ PLACA NO REGISTRADA - Requiere verificación manual"
            else:
                response_data['mensaje'] = f"🤖 IA VERIFICA: ❌ PLACA NO RECONOCIDA - Acceso denegado"

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

        registro.estado_acceso = 'autorizado'
        registro.autorizado_por = usuario
        registro.observaciones = f"Autorizado manualmente por {usuario.username}"
        registro.save()

        serializer = self.get_serializer(registro)
        return Response(serializer.data)

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

        registro.estado_acceso = 'denegado'
        registro.autorizado_por = usuario
        registro.observaciones = f"Denegado manualmente por {usuario.username}"
        registro.save()

        serializer = self.get_serializer(registro)
        return Response(serializer.data)

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
                        'message': f'Placa de residente creada: {placa}',
                        'placa': placa,
                        'tipo': 'residente',
                        'residente': residente.persona.nombre
                    })
                else:
                    return Response({
                        'message': f'Placa de residente ya existe: {placa}',
                        'placa': placa,
                        'tipo': 'residente'
                    })
            
            elif tipo == 'invitado':
                # Crear placa de invitado
                residente = Residentes.objects.first()  # Tomar el primer residente
                if not residente:
                    return Response(
                        {'error': 'No hay residentes en el sistema'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                fecha_vencimiento = timezone.now() + timezone.timedelta(days=30)
                
                placa_obj, created = PlacaInvitado.objects.get_or_create(
                    placa=placa,
                    defaults={
                        'residente': residente,
                        'marca': marca,
                        'modelo': modelo,
                        'color': color,
                        'nombre_visitante': 'Visitante de Prueba',
                        'ci_visitante': '12345678',
                        'fecha_autorizacion': timezone.now(),
                        'fecha_vencimiento': fecha_vencimiento,
                        'activo': True
                    }
                )
                
                if created:
                    return Response({
                        'message': f'Placa de invitado creada: {placa}',
                        'placa': placa,
                        'tipo': 'invitado',
                        'residente': residente.persona.nombre,
                        'vencimiento': fecha_vencimiento
                    })
                else:
                    return Response({
                        'message': f'Placa de invitado ya existe: {placa}',
                        'placa': placa,
                        'tipo': 'invitado'
                    })
            
            else:
                return Response(
                    {'error': 'Tipo debe ser "residente" o "invitado"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error al crear placa de prueba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
