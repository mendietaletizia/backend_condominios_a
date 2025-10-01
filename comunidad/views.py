from django.shortcuts import render
from django.utils import timezone

# Create your views here.
from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, LecturaComunicado, Acta, Mascota, Reglamento, Reserva
from comunidad.serializers.comunidad_serializer import (
    UnidadSerializer, ResidentesUnidadSerializer,
    EventoSerializer, NotificacionSerializer,
    NotificacionResidenteSerializer, LecturaComunicadoSerializer, ActaSerializer, MascotaSerializer, ReglamentoSerializer,
    ReservaSerializer
)
from usuarios.models import Empleado
from django.db.models import Q
from usuarios.models import PlacaVehiculo
from usuarios.models import Invitado

class RolPermiso(permissions.BasePermission):
    """Solo Admin puede modificar; otros roles pueden ver"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar si el usuario tiene rol de administrador
        if hasattr(request.user, 'rol') and request.user.rol:
            if request.user.rol.nombre.lower() == "administrador":
                return True
        
        # Verificar si es empleado con cargo administrador (lógica de respaldo)
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        
        # Para vistas que solo consultan, permitimos GET
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

class ReservaPermiso(permissions.BasePermission):
    """Permisos específicos para reservas - residentes pueden crear, admin puede todo"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores pueden hacer todo
        if hasattr(request.user, 'rol') and request.user.rol:
            if request.user.rol.nombre.lower() == "administrador":
                return True
        
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        
        # Para reservas, permitir GET y POST a todos los usuarios autenticados
        if request.method in ['GET', 'POST']:
            return True
        
        # Para PUT/DELETE, solo administradores
        return False

class NotificacionPermiso(permissions.BasePermission):
    """Permisos específicos para notificaciones"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Para acciones específicas como confirmar_lectura, permitir a todos los usuarios autenticados
        if hasattr(view, 'action') and view.action in ['confirmar_lectura', 'lecturas_confirmadas']:
            return True
        
        # Para operaciones CRUD normales, usar la lógica de RolPermiso
        # Verificar si el usuario tiene rol de administrador
        if hasattr(request.user, 'rol') and request.user.rol:
            if request.user.rol.nombre.lower() == "administrador":
                return True
        
        # Verificar si es empleado con cargo administrador (lógica de respaldo)
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        
        # Para vistas que solo consultan, permitimos GET
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

# CU6: Unidades
class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    permission_classes = [RolPermiso]
    
    def perform_create(self, serializer):
        """Validaciones adicionales al crear una unidad"""
        numero_casa = serializer.validated_data.get('numero_casa')
        metros_cuadrados = serializer.validated_data.get('metros_cuadrados')
        
        # Validar que el número de casa no esté duplicado
        if Unidad.objects.filter(numero_casa=numero_casa).exists():
            raise serializers.ValidationError("Ya existe una unidad con este número de casa")
        
        # Validar metros cuadrados
        if metros_cuadrados <= 0:
            raise serializers.ValidationError("Los metros cuadrados deben ser mayor a 0")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Validaciones adicionales al actualizar una unidad"""
        numero_casa = serializer.validated_data.get('numero_casa')
        metros_cuadrados = serializer.validated_data.get('metros_cuadrados')
        
        # Validar que el número de casa no esté duplicado (excluyendo el registro actual)
        if Unidad.objects.filter(numero_casa=numero_casa).exclude(id=self.get_object().id).exists():
            raise serializers.ValidationError("Ya existe otra unidad con este número de casa")
        
        # Validar metros cuadrados
        if metros_cuadrados <= 0:
            raise serializers.ValidationError("Los metros cuadrados deben ser mayor a 0")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Manejar la eliminación de una unidad"""
        try:
            # Verificar si hay residentes asociados
            from comunidad.models import ResidentesUnidad
            relaciones = ResidentesUnidad.objects.filter(id_unidad=instance.id, estado=True)
            if relaciones.exists():
                raise serializers.ValidationError("No se puede eliminar la unidad porque tiene residentes asociados")
            
            # Verificar si hay mascotas asociadas
            from comunidad.models import Mascota
            mascotas = Mascota.objects.filter(unidad=instance.id, activo=True)
            if mascotas.exists():
                raise serializers.ValidationError("No se puede eliminar la unidad porque tiene mascotas asociadas")
            
            instance.delete()
            
        except Exception as e:
            raise serializers.ValidationError(f"Error al eliminar unidad: {str(e)}")

    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        """Devuelve la unidad con info agregada: vehiculos y invitados activos de hoy."""
        unidad = self.get_object()
        data = UnidadSerializer(unidad).data

        # Vehículos por unidad (residentes activos)
        vehiculos = PlacaVehiculo.objects.filter(
            residente__residentesunidad__id_unidad=unidad,
            residente__residentesunidad__estado=True,
            activo=True
        ).distinct().order_by('-fecha_registro')
        data['vehiculos'] = [
            {
                'id': v.id,
                'placa': v.placa,
                'marca': v.marca,
                'modelo': v.modelo,
                'color': v.color,
                'residente_id': v.residente.id,
                'residente_nombre': v.residente.persona.nombre if v.residente.persona else 'Sin nombre',
                'fecha_registro': v.fecha_registro,
                'activo': v.activo
            } for v in vehiculos
        ]

        # Invitados activos de hoy vinculados a residentes de la unidad
        ahora = timezone.now()
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
        invitados_hoy = Invitado.objects.filter(
            residente__residentesunidad__id_unidad=unidad,
            residente__residentesunidad__estado=True,
            activo=True,
            fecha_inicio__lte=fin
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=inicio)
        ).select_related('residente', 'evento').order_by('fecha_inicio')

        data['invitados_hoy'] = [
            {
                'id': inv.id,
                'nombre': inv.nombre,
                'ci': inv.ci,
                'tipo': inv.tipo,
                'tipo_display': inv.get_tipo_display(),
                'vehiculo_placa': inv.vehiculo_placa,
                'residente': {
                    'id': inv.residente.id,
                    'nombre': inv.residente.persona.nombre if inv.residente.persona else 'Sin nombre'
                },
                'evento': {
                    'id': inv.evento.id,
                    'titulo': getattr(inv.evento, 'titulo', None)
                } if inv.evento else None,
                'fecha_inicio': inv.fecha_inicio,
                'fecha_fin': inv.fecha_fin,
                'check_in_at': inv.check_in_at,
                'check_out_at': inv.check_out_at,
            }
            for inv in invitados_hoy
        ]

        return Response(data)

    # Se remueve gestión de vehículos desde unidad para separar el CU

    @action(detail=True, methods=['delete'], url_path='vehiculos/(?P<vehiculo_id>[^/.]+)')
    def eliminar_vehiculo(self, request, vehiculo_id=None, pk=None):
        """Eliminar vehículo de un residente de esta unidad. Admin/Seguridad."""
        unidad = self.get_object()
        user = request.user
        permitido = False
        if user.is_superuser or (hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Administrador'):
            permitido = True
        else:
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
                permitido = True
        if not permitido:
            return Response({'error': 'No autorizado'}, status=403)

        try:
            vehiculo = PlacaVehiculo.objects.get(pk=int(vehiculo_id))
        except Exception:
            return Response({'error': 'vehiculo_id inválido'}, status=400)

        # Validar pertenencia a esta unidad
        if not ResidentesUnidad.objects.filter(id_residente=vehiculo.residente, id_unidad=unidad, estado=True).exists():
            return Response({'error': 'El vehículo no pertenece a un residente activo de esta unidad'}, status=400)

        vehiculo.delete()
        return Response(status=204)

    @action(detail=True, methods=['get'], url_path='vehiculos/resumen')
    def vehiculos_resumen(self, request, pk=None):
        """Resumen simple de vehículos por unidad."""
        unidad = self.get_object()
        qs = PlacaVehiculo.objects.filter(
            residente__residentesunidad__id_unidad=unidad,
            residente__residentesunidad__estado=True
        ).distinct()
        total = qs.count()
        activos = qs.filter(activo=True).count()
        ultimos = qs.order_by('-fecha_registro')[:10]
        from usuarios.serializers.usuarios_serializer import PlacaVehiculoSerializer
        serializer = PlacaVehiculoSerializer(ultimos, many=True)
        return Response({'total': total, 'activos': activos, 'ultimos': serializer.data})

class ResidentesUnidadViewSet(viewsets.ModelViewSet):
    queryset = ResidentesUnidad.objects.all()
    serializer_class = ResidentesUnidadSerializer
    permission_classes = [RolPermiso]
    
    def perform_create(self, serializer):
        """Crear relación residente-unidad"""
        serializer.save()
    
    def perform_update(self, serializer):
        """Actualizar relación residente-unidad"""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Eliminar relación residente-unidad"""
        instance.delete()

# CU11: Eventos
class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [RolPermiso]

# CU12: Comunicados / Noticias
class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [NotificacionPermiso]

    from rest_framework.decorators import action
    from rest_framework.response import Response

    def update(self, request, *args, **kwargs):
        """Override update method to add logging"""
        print(f"Update request data: {request.data}")
        print(f"Update request user: {request.user}")
        print(f"Update kwargs: {kwargs}")
        
        # Obtener la instancia
        instance = self.get_object()
        print(f"Update instance: {instance}")
        
        # Crear serializer con datos
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        print(f"Serializer created with data: {serializer.initial_data}")
        
        if serializer.is_valid():
            print(f"Serializer is valid, validated_data: {serializer.validated_data}")
            serializer.save()
            return Response(serializer.data)
        else:
            print(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Crear un comunicado y asignarlo a todos los residentes."""
        titulo = request.data.get('titulo')
        contenido = request.data.get('contenido')
        tipo = request.data.get('tipo') or 'Comunicado'
        fecha = request.data.get('fecha') or timezone.now()
        destinatarios = request.data.get('destinatarios', {})

        if not titulo:
            return Response({'error': 'El título es requerido'}, status=400)
        if not contenido:
            return Response({'error': 'El contenido es requerido'}, status=400)

        # Crear la notificación con destinatarios
        notif = Notificacion.objects.create(
            titulo=titulo,
            contenido=contenido,
            fecha=fecha,
            tipo=tipo,
            destinatarios=destinatarios
        )

        # Crear NotificacionResidente para todos los residentes activos
        from usuarios.models import Residentes
        residentes = Residentes.objects.all()
        created = 0
        bulk = []
        for r in residentes:
            bulk.append(NotificacionResidente(notificacion=notif, residente=r, leido=False))
        if bulk:
            NotificacionResidente.objects.bulk_create(bulk)
            created = len(bulk)

        return Response({'detail': 'Comunicado enviado', 'notificacion_id': notif.id, 'asignados': created}, status=201)

    @action(detail=True, methods=['post'])
    def confirmar_lectura(self, request, pk=None):
        """Confirmar que un usuario ha leído un comunicado"""
        notificacion = self.get_object()
        usuario = request.user
        
        if not usuario or not usuario.is_authenticated:
            return Response({'error': 'Usuario no autenticado'}, status=401)
        
        # Obtener el rol del usuario
        rol = 'usuario'  # Por defecto
        if hasattr(usuario, 'rol') and usuario.rol:
            rol = usuario.rol.nombre.lower()
        else:
            # Verificar si es empleado
            empleado = Empleado.objects.filter(usuario=usuario).first()
            if empleado:
                rol = empleado.cargo.lower()
            else:
                # Verificar si es residente
                from usuarios.models import Residentes
                residente = Residentes.objects.filter(usuario_asociado=usuario).first()
                if residente:
                    rol = 'residente'
        
        # Crear o actualizar el registro de lectura
        lectura, created = LecturaComunicado.objects.get_or_create(
            notificacion=notificacion,
            usuario=usuario,
            defaults={'rol': rol}
        )
        
        if not created:
            # Si ya existe, actualizar la fecha de lectura
            lectura.fecha_lectura = timezone.now()
            lectura.rol = rol  # Actualizar rol por si cambió
            lectura.save()
        
        return Response({
            'detail': 'Lectura confirmada',
            'usuario': usuario.username,
            'rol': rol,
            'fecha_lectura': lectura.fecha_lectura,
            'created': created
        }, status=200)

    @action(detail=True, methods=['get'])
    def lecturas_confirmadas(self, request, pk=None):
        """Obtener lista de usuarios que han leído este comunicado"""
        notificacion = self.get_object()
        lecturas = LecturaComunicado.objects.filter(notificacion=notificacion)
        serializer = LecturaComunicadoSerializer(lecturas, many=True)
        return Response(serializer.data)

class NotificacionResidenteViewSet(viewsets.ModelViewSet):
    queryset = NotificacionResidente.objects.all()
    serializer_class = NotificacionResidenteSerializer
    permission_classes = [permissions.IsAuthenticated]  # Todos los usuarios pueden ver sus notificaciones
    
    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return NotificacionResidente.objects.none()
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return NotificacionResidente.objects.all()
        # Residentes solo ven sus propias notificaciones
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return NotificacionResidente.objects.filter(residente=residente)
        return NotificacionResidente.objects.none()

# CU17: Actas
class ActaViewSet(viewsets.ModelViewSet):
    queryset = Acta.objects.all()
    serializer_class = ActaSerializer
    permission_classes = [RolPermiso]

# CU5: Mascotas
class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.all()
    serializer_class = MascotaSerializer
    permission_classes = [RolPermiso]
    
    def get_queryset(self):
        """Filtrar mascotas según permisos del usuario"""
        if not self.request.user or not self.request.user.is_authenticated:
            return Mascota.objects.none()
        
        # Administradores pueden ver todas las mascotas
        if self.request.user.is_superuser or (self.request.user.rol and self.request.user.rol.nombre == 'Administrador'):
            return Mascota.objects.all()
        
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Mascota.objects.all()
        
        # Residentes solo pueden ver sus propias mascotas
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Mascota.objects.filter(residente=residente)
        
        return Mascota.objects.none()

class ReglamentoViewSet(viewsets.ModelViewSet):
    """CRUD para gestión de reglamento del condominio"""
    queryset = Reglamento.objects.all()
    serializer_class = ReglamentoSerializer
    permission_classes = [RolPermiso]
    
    def get_queryset(self):
        """Filtrar reglamentos activos por defecto"""
        queryset = super().get_queryset()
        activo = self.request.query_params.get('activo', None)
        
        if activo is not None:
            if activo.lower() == 'true':
                queryset = queryset.filter(activo=True)
            elif activo.lower() == 'false':
                queryset = queryset.filter(activo=False)
        
        return queryset.order_by('articulo')
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Obtener reglamentos por tipo"""
        tipo = request.query_params.get('tipo')
        if not tipo:
            return Response(
                {'error': 'Parámetro tipo es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reglamentos = self.get_queryset().filter(tipo=tipo, activo=True)
        serializer = self.get_serializer(reglamentos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtener solo reglamentos activos"""
        reglamentos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(reglamentos, many=True)
        return Response(serializer.data)

# CU10: Reservas
class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [ReservaPermiso]

    def get_queryset(self):
        # Residente solo ve sus reservas, admin ve todas
        if not self.request.user or not self.request.user.is_authenticated:
            return Reserva.objects.none()
        
        # Administradores pueden ver todas las reservas
        if self.request.user.is_superuser or (hasattr(self.request.user, 'rol') and self.request.user.rol and self.request.user.rol.nombre.lower() == 'administrador'):
            return Reserva.objects.all()
        
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Reserva.objects.all()
        
        # Residentes solo ven sus propias reservas
        from usuarios.models import Residentes
        try:
            residente = Residentes.objects.get(usuario_asociado=self.request.user)
            return Reserva.objects.filter(residente=residente)
        except Residentes.DoesNotExist:
            # Si no es residente, devolver todas las reservas (para debug)
            return Reserva.objects.all()
    
    def perform_create(self, serializer):
        # Asignar automáticamente el residente al crear la reserva
        from usuarios.models import Residentes
        residente = Residentes.objects.filter(usuario_asociado=self.request.user).first()
        if residente:
            serializer.save(residente=residente)
    
    @action(detail=False, methods=['get'])
    def disponibilidad(self, request):
        """Verificar disponibilidad de un área en una fecha y hora específica"""
        area_id = request.query_params.get('area_id')
        fecha = request.query_params.get('fecha')
        hora_inicio = request.query_params.get('hora_inicio')
        hora_fin = request.query_params.get('hora_fin')
        
        if not all([area_id, fecha, hora_inicio, hora_fin]):
            return Response({'error': 'Faltan parámetros requeridos'}, status=400)
        
        # Verificar si hay conflictos de horario
        reservas_conflicto = Reserva.objects.filter(
            area_id=area_id,
            fecha=fecha,
            estado__in=['pendiente', 'confirmada']
        ).filter(
            Q(hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio)
        )
        
        disponible = not reservas_conflicto.exists()
        
        return Response({
            'disponible': disponible,
            'conflictos': reservas_conflicto.count()
        })

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirmar una reserva y generar un evento en la agenda (CU11)."""
        reserva = self.get_object()
        
        # Solo permitir confirmar reservas pendientes
        if reserva.estado != 'pendiente':
            return Response({
                'error': f'No se puede confirmar una reserva en estado "{reserva.estado}". Solo se pueden confirmar reservas pendientes.'
            }, status=400)
        
        reserva.estado = 'confirmada'
        reserva.save()

        # Crear evento asociado (sin FK directa, guardamos datos descriptivos)
        try:
            from datetime import datetime
            from django.utils import timezone
            fecha_evento = datetime.combine(reserva.fecha, reserva.hora_inicio)
            if timezone.is_naive(fecha_evento):
                fecha_evento = timezone.make_aware(fecha_evento)
        except Exception:
            fecha_evento = timezone.now()

        titulo = f"Reserva confirmada - {reserva.area.nombre}"
        residente_nombre = getattr(getattr(reserva.residente, 'persona', None), 'nombre', None) or getattr(getattr(reserva.residente, 'usuario_asociado', None), 'username', 'Residente')
        residente_ci = getattr(getattr(reserva.residente, 'persona', None), 'ci', None)
        if residente_ci:
            descripcion = (
                f"Evento por reserva del área {reserva.area.nombre} de {reserva.hora_inicio} a {reserva.hora_fin} "
                f"por {residente_nombre} (CI: {residente_ci}). Residente ID: {reserva.residente_id}. Reserva ID: {reserva.id}."
            )
        else:
            descripcion = (
                f"Evento por reserva del área {reserva.area.nombre} de {reserva.hora_inicio} a {reserva.hora_fin} "
                f"por {residente_nombre}. Residente ID: {reserva.residente_id}. Reserva ID: {reserva.id}."
            )
        evento = Evento.objects.create(titulo=titulo, descripcion=descripcion, fecha=fecha_evento, estado=True)
        # Asociar el área al evento para que aparezca en areas_info del serializer
        try:
            evento.areas.add(reserva.area)
        except Exception:
            pass

        return Response({
            'detail': 'Reserva confirmada y evento creado',
            'reserva_id': reserva.id,
            'estado': reserva.estado
        }, status=200)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancelar una reserva (y no crear evento)."""
        reserva = self.get_object()
        
        # Solo permitir cancelar reservas pendientes
        if reserva.estado != 'pendiente':
            return Response({
                'error': f'No se puede cancelar una reserva en estado "{reserva.estado}". Solo se pueden cancelar reservas pendientes.'
            }, status=400)
        
        reserva.estado = 'cancelada'
        reserva.save()
        return Response({
            'detail': 'Reserva cancelada',
            'reserva_id': reserva.id,
            'estado': reserva.estado
        }, status=200)
