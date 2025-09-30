from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from usuarios.models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo, Residentes,
    TipoTarea, TareaEmpleado, ComentarioTarea, EvaluacionTarea
)
from usuarios.serializers.usuarios_serializer import (
    UsuarioSerializer, PersonaSerializer, RolesSerializer,
    PermisoSerializer, RolPermisoSerializer, EmpleadoSerializer,
    VehiculoSerializer, AccesoVehicularSerializer, VisitaSerializer,
    InvitadoSerializer, ReclamoSerializer, ResidentesSerializer,
    UsuarioResidenteSerializer, TipoTareaSerializer, TareaEmpleadoSerializer,
    ComentarioTareaSerializer, EvaluacionTareaSerializer, ResumenTareasSerializer,
    EstadisticasTareasSerializer, ResumenEmpleadoSerializer
)
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, F, Avg
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone


# Permiso personalizado para acceso de administrador
class RolPermisoPermission(permissions.BasePermission):
    """
    Solo usuarios con cargo Administrador pueden acceder
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Permitir si es superusuario
        if request.user.is_superuser:
            return True
        
        # Permitir si tiene rol de administrador
        if request.user.rol and request.user.rol.nombre == 'Administrador':
            return True
        
        # Permitir si es empleado con cargo de administrador
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return True
        
        return False


# Residentes ViewSet para exponer /usuarios/residentes/
class ResidentesViewSet(viewsets.ModelViewSet):
    queryset = Residentes.objects.all()
    serializer_class = ResidentesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar residentes según permisos del usuario"""
        if not self.request.user or not self.request.user.is_authenticated:
            return Residentes.objects.none()
        
        # Administradores pueden ver todos los residentes
        if self.request.user.is_superuser:
            return Residentes.objects.all()
        
        # Si tiene rol de administrador
        if self.request.user.rol and self.request.user.rol.nombre == 'Administrador':
            return Residentes.objects.all()
        
        # Empleados administradores pueden ver todos los residentes
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Residentes.objects.all()
        
        # Para cualquier otro usuario autenticado, mostrar todos (temporal)
        return Residentes.objects.all()
    
    def perform_create(self, serializer):
        """Validaciones adicionales al crear un residente"""
        # Validar que la persona asociada existe
        persona = serializer.validated_data.get('persona')
        if not persona:
            raise serializers.ValidationError("Debe especificar una persona asociada")

        # Validar que no se duplique el usuario si se especifica
        usuario = serializer.validated_data.get('usuario')
        usuario_asociado = serializer.validated_data.get('usuario_asociado')

        if usuario and usuario_asociado:
            raise serializers.ValidationError("Un residente no puede tener usuario propio y usuario asociado al mismo tiempo")

        # Si se está asociando un usuario_asociado, usar el método especial
        if usuario_asociado:
            residente = serializer.save()
            try:
                # usuario_asociado viene como instancia (PrimaryKeyRelatedField)
                residente.asociar_usuario(usuario_asociado)
            except Exception as e:
                raise serializers.ValidationError(f"Error al asociar usuario: {str(e)}")
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Validaciones adicionales al actualizar un residente"""
        # Validar que la persona asociada existe
        persona = serializer.validated_data.get('persona')
        if not persona:
            raise serializers.ValidationError("Debe especificar una persona asociada")

        # Validar que no se duplique el usuario si se especifica
        usuario = serializer.validated_data.get('usuario')
        usuario_asociado = serializer.validated_data.get('usuario_asociado')

        if usuario and usuario_asociado:
            raise serializers.ValidationError("Un residente no puede tener usuario propio y usuario asociado al mismo tiempo")

        # Si se está asociando un usuario_asociado, usar el método especial
        instance = serializer.instance
        if usuario_asociado and not instance.usuario_asociado:
            try:
                instance.asociar_usuario(usuario_asociado)
            except Exception as e:
                raise serializers.ValidationError(f"Error al asociar usuario: {str(e)}")
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        """Manejar la eliminación de un residente"""
        try:
            # Eliminar relaciones con unidades primero
            from comunidad.models import ResidentesUnidad
            relaciones_unidad = ResidentesUnidad.objects.filter(id_residente=instance.id)
            for relacion in relaciones_unidad:
                relacion.delete()
            
            # Eliminar mascotas asociadas
            from comunidad.models import Mascota
            mascotas = Mascota.objects.filter(residente=instance.id)
            for mascota in mascotas:
                mascota.delete()
            
            # Eliminar el residente
            instance.delete()
            
        except Exception as e:
            raise serializers.ValidationError(f"Error al eliminar residente: {str(e)}")



class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [RolPermisoPermission]



class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [RolPermisoPermission]

    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return Persona.objects.none()
        
        # Administradores pueden ver todas las personas
        if self.request.user.is_superuser or (self.request.user.rol and self.request.user.rol.nombre == 'Administrador'):
            return Persona.objects.all()
        
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Persona.objects.all()
        elif empleado:
            return Persona.objects.filter(id=empleado.persona.id)
        
        # Si es residente, solo puede ver su propia información
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Persona.objects.filter(id=residente.persona.id)
        
        return Persona.objects.none()
    
    def perform_create(self, serializer):
        """Validaciones adicionales al crear una persona"""
        ci = serializer.validated_data.get('ci')
        if ci:
            # Verificar que el CI no esté duplicado
            if Persona.objects.filter(ci=ci).exists():
                raise serializers.ValidationError("Ya existe una persona con este CI")
        serializer.save()
    
    def perform_update(self, serializer):
        """Validaciones adicionales al actualizar una persona"""
        ci = serializer.validated_data.get('ci')
        if ci:
            # Verificar que el CI no esté duplicado (excluyendo el registro actual)
            if Persona.objects.filter(ci=ci).exclude(id=self.get_object().id).exists():
                raise serializers.ValidationError("Ya existe otra persona con este CI")
        serializer.save()



class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [RolPermisoPermission]



class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [RolPermisoPermission]



class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated]



class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [RolPermisoPermission]

# Vistas para los nuevos modelos
class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer
    permission_classes = [RolPermisoPermission]

class AccesoVehicularViewSet(viewsets.ModelViewSet):
    queryset = AccesoVehicular.objects.all()
    serializer_class = AccesoVehicularSerializer
    permission_classes = [RolPermisoPermission]

class VisitaViewSet(viewsets.ModelViewSet):
    queryset = Visita.objects.all()
    serializer_class = VisitaSerializer
    permission_classes = [RolPermisoPermission]

class InvitadoViewSet(viewsets.ModelViewSet):
    queryset = Invitado.objects.all()
    serializer_class = InvitadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Invitado.objects.all()
        user = self.request.user

        # Scoping: admin/superuser/empleado administrador ve todos, residente ve los propios
        is_admin = False
        if user and user.is_authenticated:
            if user.is_superuser:
                is_admin = True
            elif getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador':
                is_admin = True
            else:
                empleado = Empleado.objects.filter(usuario=user).first()
                if empleado and empleado.cargo.lower() == 'administrador':
                    is_admin = True

        if not is_admin:
            residente = Residentes.objects.filter(usuario=user).first()
            if residente:
                qs = qs.filter(residente=residente)
            else:
                qs = Invitado.objects.none()

        # Filtros
        residente_id = self.request.query_params.get('residente_id')
        if residente_id:
            qs = qs.filter(residente_id=residente_id)

        tipo = self.request.query_params.get('tipo')
        if tipo in ['casual', 'evento']:
            qs = qs.filter(tipo=tipo)

        evento_id = self.request.query_params.get('evento_id')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)

        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')

        return qs.order_by('-creado_en')

    def perform_create(self, serializer):
        # Asegurar residente por usuario autenticado si no viene en payload
        residente = None
        try:
            residente = Residentes.objects.filter(usuario=self.request.user).first()
        except Exception:
            pass
        if residente and not serializer.validated_data.get('residente'):
            serializer.save(residente=residente)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Listar invitados activos (fecha_fin nula o futura y activo=True)"""
        ahora = timezone.now()
        qs = self.get_queryset().filter(
            activo=True
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=ahora)
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_evento(self, request):
        evento_id = request.query_params.get('evento_id')
        if not evento_id:
            return Response({'error': 'Debe proporcionar evento_id'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(tipo='evento', evento_id=evento_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Registrar entrada del invitado. Solo Admin o Seguridad/Portero."""
        invitado = self.get_object()

        # Permisos: admin/superuser o empleado con cargo seguridad/portero/administrador
        user = request.user
        permitido = False
        if user.is_superuser or (getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador'):
            permitido = True
        else:
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado and empleado.cargo.lower() in ['seguridad', 'portero', 'administrador']:
                permitido = True
        if not permitido:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        if invitado.check_in_at is not None:
            return Response({'error': 'Ya tiene check-in registrado'}, status=status.HTTP_400_BAD_REQUEST)

        ahora = timezone.now()
        invitado.check_in_at = ahora
        invitado.check_in_by = user
        invitado.save(update_fields=['check_in_at', 'check_in_by', 'actualizado_en'])
        return Response(self.get_serializer(invitado).data)

    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """Registrar salida del invitado. Solo Admin o Seguridad/Portero."""
        invitado = self.get_object()

        user = request.user
        permitido = False
        if user.is_superuser or (getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador'):
            permitido = True
        else:
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado and empleado.cargo.lower() in ['seguridad', 'portero', 'administrador']:
                permitido = True
        if not permitido:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        if invitado.check_in_at is None:
            return Response({'error': 'No tiene check-in registrado'}, status=status.HTTP_400_BAD_REQUEST)
        if invitado.check_out_at is not None:
            return Response({'error': 'Ya tiene check-out registrado'}, status=status.HTTP_400_BAD_REQUEST)

        ahora = timezone.now()
        invitado.check_out_at = ahora
        invitado.check_out_by = user
        invitado.save(update_fields=['check_out_at', 'check_out_by', 'actualizado_en'])
        return Response(self.get_serializer(invitado).data)

    @action(detail=False, methods=['get'])
    def en_condominio(self, request):
        """Lista y conteo de invitados con check-in sin check-out. Scoping: Admin/Security todos; Residente solo propios."""
        qs = self.get_queryset().filter(check_in_at__isnull=False, check_out_at__isnull=True)
        conteo = qs.count()
        serializer = self.get_serializer(qs.order_by('check_in_at'), many=True)
        return Response({'conteo': conteo, 'invitados': serializer.data})

    @action(detail=False, methods=['get'], url_path='seguridad/hoy')
    def seguridad_hoy(self, request):
        """Invitados activos del día para seguridad. Admin y empleados de seguridad ven todos; residentes ven propios."""
        ahora = timezone.now()
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)

        user = request.user
        qs = Invitado.objects.filter(
            activo=True,
            fecha_inicio__lte=fin
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=inicio)
        )

        is_admin = False
        if user and user.is_authenticated:
            if user.is_superuser or (getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador'):
                is_admin = True
        if not is_admin:
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
                is_admin = True

        if not is_admin:
            residente = Residentes.objects.filter(usuario=user).first()
            if residente:
                qs = qs.filter(residente=residente)
            else:
                qs = Invitado.objects.none()

        serializer = self.get_serializer(qs.order_by('fecha_inicio'), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='seguridad/resumen')
    def seguridad_resumen(self, request):
        """Resumen del día para portería: totales y por tipo."""
        ahora = timezone.now()
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Base queryset similar a seguridad_hoy
        user = request.user
        qs = Invitado.objects.filter(
            activo=True,
            fecha_inicio__lte=fin
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=inicio)
        )

        is_admin = False
        if user and user.is_authenticated:
            if user.is_superuser or (getattr(user, 'rol', None) and user.rol and user.rol.nombre == 'Administrador'):
                is_admin = True
        if not is_admin:
            empleado = Empleado.objects.filter(usuario=user).first()
            if empleado and empleado.cargo.lower() in ['administrador', 'seguridad', 'portero']:
                is_admin = True

        if not is_admin:
            residente = Residentes.objects.filter(usuario=user).first()
            if residente:
                qs = qs.filter(residente=residente)
            else:
                qs = Invitado.objects.none()

        total = qs.count()
        total_evento = qs.filter(tipo='evento').count()
        total_casual = qs.filter(tipo='casual').count()

        # Próximos 10 ingresos ordenados
        proximos = qs.order_by('fecha_inicio')[:10]
        data_proximos = [
            {
                'id': inv.id,
                'nombre': inv.nombre,
                'ci': inv.ci,
                'tipo': inv.tipo,
                'tipo_display': inv.get_tipo_display(),
                'vehiculo_placa': inv.vehiculo_placa,
                'residente': {
                    'id': inv.residente.id,
                    'nombre': inv.residente.persona.nombre,
                },
                'evento': {
                    'id': inv.evento.id,
                    'titulo': getattr(inv.evento, 'titulo', None)
                } if inv.evento else None,
                'fecha_inicio': inv.fecha_inicio,
                'fecha_fin': inv.fecha_fin,
            }
            for inv in proximos
        ]

        return Response({
            'fecha': ahora.date(),
            'totales': {
                'total': total,
                'evento': total_evento,
                'casual': total_casual,
            },
            'proximos': data_proximos,
        })

class ReclamoViewSet(viewsets.ModelViewSet):
    queryset = Reclamo.objects.all()
    serializer_class = ReclamoSerializer
    permission_classes = [IsAuthenticated]  # Residentes pueden crear reclamos
    
    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return Reclamo.objects.none()
        empleado = Empleado.objects.filter(usuario=self.request.user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Reclamo.objects.all()
        # Residentes solo ven sus propios reclamos
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            return Reclamo.objects.filter(residente=residente)
        return Reclamo.objects.none()
    
    def perform_create(self, serializer):
        # Asignar automáticamente el residente al crear el reclamo
        residente = Residentes.objects.filter(usuario=self.request.user).first()
        if residente:
            serializer.save(residente=residente)

# ViewSet específico para obtener solo usuarios con rol de residente (para selección de propietarios)
class UsuariosResidentesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet que devuelve solo usuarios con rol de 'residente' para selección de propietarios
    """
    queryset = Usuario.objects.none()  # Se sobrescribe en get_queryset()
    serializer_class = UsuarioResidenteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Solo usuarios con rol de 'residente'"""
        if not self.request.user or not self.request.user.is_authenticated:
            return Usuario.objects.none()
        
        # Filtrar solo usuarios con rol de 'residente'
        return Usuario.objects.filter(
            rol__nombre__iexact='residente',
            is_active=True
        ).select_related('rol')

# CU23: Asignación de Tareas para Empleados - Nuevos ViewSets


class TipoTareaViewSet(viewsets.ModelViewSet):
    """Gestión de Tipos de Tareas - CU23"""
    queryset = TipoTarea.objects.all()
    serializer_class = TipoTareaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        requiere_especialista = self.request.query_params.get('requiere_especialista')
        if requiere_especialista is not None:
            queryset = queryset.filter(requiere_especialista=requiere_especialista.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtiene solo los tipos de tareas activos"""
        tipos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(tipos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_categoria(self, request):
        """Obtiene tipos de tareas agrupados por categoría"""
        tipos = self.get_queryset().filter(activo=True)
        resultado = {}
        
        for tipo in tipos:
            categoria = tipo.get_categoria_display()
            if categoria not in resultado:
                resultado[categoria] = []
            resultado[categoria].append(TipoTareaSerializer(tipo).data)
        
        return Response(resultado)


class TareaEmpleadoViewSet(viewsets.ModelViewSet):
    """Gestión de Tareas de Empleados - CU23"""
    queryset = TareaEmpleado.objects.all()
    serializer_class = TareaEmpleadoSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(supervisor=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        prioridad = self.request.query_params.get('prioridad')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        
        empleado = self.request.query_params.get('empleado')
        if empleado:
            queryset = queryset.filter(empleado_asignado_id=empleado)
        
        supervisor = self.request.query_params.get('supervisor')
        if supervisor:
            queryset = queryset.filter(supervisor_id=supervisor)
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(tipo_tarea__categoria=categoria)
        
        vencidas = self.request.query_params.get('vencidas')
        if vencidas is not None:
            if vencidas.lower() == 'true':
                queryset = queryset.filter(
                    fecha_limite__lt=timezone.now(),
                    estado__in=['asignada', 'en_progreso']
                )
            else:
                queryset = queryset.exclude(
                    fecha_limite__lt=timezone.now(),
                    estado__in=['asignada', 'en_progreso']
                )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def mis_tareas(self, request):
        """Obtiene las tareas del empleado autenticado"""
        empleado = Empleado.objects.filter(usuario=request.user).first()
        if not empleado:
            return Response({'error': 'Usuario no es un empleado'}, status=status.HTTP_400_BAD_REQUEST)
        
        tareas = self.get_queryset().filter(empleado_asignado=empleado)
        serializer = self.get_serializer(tareas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tareas_supervisadas(self, request):
        """Obtiene las tareas supervisadas por el usuario autenticado"""
        tareas = self.get_queryset().filter(supervisor=request.user)
        serializer = self.get_serializer(tareas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """Obtiene tareas vencidas"""
        tareas = self.get_queryset().filter(
            fecha_limite__lt=timezone.now(),
            estado__in=['asignada', 'en_progreso']
        )
        serializer = self.get_serializer(tareas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Inicia una tarea"""
        tarea = self.get_object()
        if tarea.estado != 'asignada':
            return Response(
                {'error': 'Solo se pueden iniciar tareas asignadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'en_progreso'
        tarea.fecha_inicio = timezone.now()
        tarea.save()
        
        # Crear comentario automático
        ComentarioTarea.objects.create(
            tarea=tarea,
            autor=request.user,
            comentario=f"Tarea iniciada por {request.user.username}",
            es_interno=False
        )
        
        return Response({'message': 'Tarea iniciada'})
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """Completa una tarea"""
        tarea = self.get_object()
        if tarea.estado != 'en_progreso':
            return Response(
                {'error': 'Solo se pueden completar tareas en progreso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'completada'
        tarea.fecha_completado = timezone.now()
        tarea.progreso_porcentaje = 100
        tarea.save()
        
        # Crear comentario automático
        ComentarioTarea.objects.create(
            tarea=tarea,
            autor=request.user,
            comentario=f"Tarea completada por {request.user.username}",
            es_interno=False
        )
        
        return Response({'message': 'Tarea completada'})
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """Pausa una tarea"""
        tarea = self.get_object()
        if tarea.estado != 'en_progreso':
            return Response(
                {'error': 'Solo se pueden pausar tareas en progreso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'pausada'
        tarea.save()
        
        return Response({'message': 'Tarea pausada'})
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """Reanuda una tarea pausada"""
        tarea = self.get_object()
        if tarea.estado != 'pausada':
            return Response(
                {'error': 'Solo se pueden reanudar tareas pausadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'en_progreso'
        tarea.save()
        
        return Response({'message': 'Tarea reanudada'})
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtiene resumen de tareas"""
        tareas = self.get_queryset()
        
        resumen = {
            'total_tareas': tareas.count(),
            'tareas_asignadas': tareas.filter(estado='asignada').count(),
            'tareas_en_progreso': tareas.filter(estado='en_progreso').count(),
            'tareas_completadas': tareas.filter(estado='completada').count(),
            'tareas_vencidas': tareas.filter(
                fecha_limite__lt=timezone.now(),
                estado__in=['asignada', 'en_progreso']
            ).count(),
            'tareas_canceladas': tareas.filter(estado='cancelada').count(),
            'horas_trabajadas_totales': tareas.aggregate(
                total=Sum('horas_trabajadas')
            )['total'] or Decimal('0'),
            'costo_total_estimado': tareas.aggregate(
                total=Sum('costo_estimado')
            )['total'] or Decimal('0'),
            'costo_total_real': tareas.aggregate(
                total=Sum('costo_real')
            )['total'] or Decimal('0')
        }
        
        serializer = ResumenTareasSerializer(resumen)
        return Response(serializer.data)


class ComentarioTareaViewSet(viewsets.ModelViewSet):
    """Gestión de Comentarios de Tareas - CU23"""
    queryset = ComentarioTarea.objects.all()
    serializer_class = ComentarioTareaSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        tarea = self.request.query_params.get('tarea')
        if tarea:
            queryset = queryset.filter(tarea_id=tarea)
        
        autor = self.request.query_params.get('autor')
        if autor:
            queryset = queryset.filter(autor_id=autor)
        
        es_interno = self.request.query_params.get('es_interno')
        if es_interno is not None:
            queryset = queryset.filter(es_interno=es_interno.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def por_tarea(self, request):
        """Obtiene comentarios de una tarea específica"""
        tarea_id = request.query_params.get('tarea_id')
        if not tarea_id:
            return Response(
                {'error': 'Se requiere el parámetro tarea_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comentarios = self.get_queryset().filter(tarea_id=tarea_id)
        serializer = self.get_serializer(comentarios, many=True)
        return Response(serializer.data)


class EvaluacionTareaViewSet(viewsets.ModelViewSet):
    """Gestión de Evaluaciones de Tareas - CU23"""
    queryset = EvaluacionTarea.objects.all()
    serializer_class = EvaluacionTareaSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(evaluador=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        evaluador = self.request.query_params.get('evaluador')
        if evaluador:
            queryset = queryset.filter(evaluador_id=evaluador)
        
        tarea = self.request.query_params.get('tarea')
        if tarea:
            queryset = queryset.filter(tarea_id=tarea)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def por_empleado(self, request):
        """Obtiene evaluaciones de tareas de un empleado específico"""
        empleado_id = request.query_params.get('empleado_id')
        if not empleado_id:
            return Response(
                {'error': 'Se requiere el parámetro empleado_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluaciones = self.get_queryset().filter(tarea__empleado_asignado_id=empleado_id)
        serializer = self.get_serializer(evaluaciones, many=True)
        return Response(serializer.data)


class EstadisticasTareasViewSet(viewsets.ViewSet):
    """Estadísticas de Tareas - CU23"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def generales(self, request):
        """Obtiene estadísticas generales de tareas"""
        tareas = TareaEmpleado.objects.all()
        evaluaciones = EvaluacionTarea.objects.all()
        
        # Estadísticas de tareas
        tareas_por_estado = dict(tareas.values('estado').annotate(count=Count('id')).values_list('estado', 'count'))
        tareas_por_prioridad = dict(tareas.values('prioridad').annotate(count=Count('id')).values_list('prioridad', 'count'))
        tareas_por_categoria = dict(tareas.values('tipo_tarea__categoria').annotate(count=Count('id')).values_list('tipo_tarea__categoria', 'count'))
        
        # Estadísticas por empleado
        empleados_stats = {}
        for empleado in Empleado.objects.all():
            empleado_tareas = tareas.filter(empleado_asignado=empleado)
            empleados_stats[f"{empleado.persona_relacionada.nombre} {empleado.persona_relacionada.apellido}"] = {
                'total_tareas': empleado_tareas.count(),
                'tareas_completadas': empleado_tareas.filter(estado='completada').count(),
                'horas_trabajadas': float(empleado_tareas.aggregate(total=Sum('horas_trabajadas'))['total'] or 0)
            }
        
        # Calificaciones promedio
        calificaciones_promedio = evaluaciones.aggregate(
            promedio=Avg('calidad_trabajo')
        )['promedio'] or 0
        
        estadisticas = {
            'tareas_por_estado': tareas_por_estado,
            'tareas_por_prioridad': tareas_por_prioridad,
            'tareas_por_categoria': tareas_por_categoria,
            'tareas_por_empleado': empleados_stats,
            'tareas_por_mes': [],  # Se puede implementar si es necesario
            'horas_por_mes': [],   # Se puede implementar si es necesario
            'calificaciones_promedio': calificaciones_promedio,
            'empleados_mas_productivos': []  # Se puede implementar si es necesario
        }
        
        serializer = EstadisticasTareasSerializer(estadisticas)
        return Response(serializer.data)