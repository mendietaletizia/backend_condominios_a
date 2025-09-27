from django.shortcuts import render
from django.utils import timezone

# Create your views here.
from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, Acta, Mascota, Reglamento
from comunidad.serializers.comunidad_serializer import (
    UnidadSerializer, ResidentesUnidadSerializer,
    EventoSerializer, NotificacionSerializer,
    NotificacionResidenteSerializer, ActaSerializer, MascotaSerializer, ReglamentoSerializer
)
from usuarios.models import Empleado

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
    permission_classes = [RolPermiso]

    from rest_framework.decorators import action
    from rest_framework.response import Response

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Crear un comunicado y asignarlo a todos los residentes."""
        titulo = request.data.get('titulo')
        contenido = request.data.get('contenido')
        tipo = request.data.get('tipo') or 'Comunicado'
        fecha = request.data.get('fecha') or timezone.now()

        if not titulo:
            return self.Response({'error': 'El título es requerido'}, status=400)
        if not contenido:
            return self.Response({'error': 'El contenido es requerido'}, status=400)

        notif = Notificacion.objects.create(
            titulo=titulo,
            contenido=contenido,
            fecha=fecha,
            tipo=tipo,
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

        return self.Response({'detail': 'Comunicado enviado', 'notificacion_id': notif.id, 'asignados': created}, status=201)

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
