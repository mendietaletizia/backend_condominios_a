from rest_framework import viewsets, permissions, serializers
from usuarios.models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo, Residentes
)
from usuarios.serializers.usuarios_serializer import (
    UsuarioSerializer, PersonaSerializer, RolesSerializer,
    PermisoSerializer, RolPermisoSerializer, EmpleadoSerializer,
    VehiculoSerializer, AccesoVehicularSerializer, VisitaSerializer,
    InvitadoSerializer, ReclamoSerializer, ResidentesSerializer,
    UsuarioResidenteSerializer
)
from rest_framework.permissions import IsAuthenticated


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
        persona_id = serializer.validated_data.get('persona')
        if not persona_id:
            raise serializers.ValidationError("Debe especificar una persona asociada")
        
        # Validar que no se duplique el usuario si se especifica
        usuario_id = serializer.validated_data.get('usuario')
        usuario_asociado_id = serializer.validated_data.get('usuario_asociado')
        
        if usuario_id and usuario_asociado_id:
            raise serializers.ValidationError("Un residente no puede tener usuario propio y usuario asociado al mismo tiempo")
        
        # Si se está asociando un usuario_asociado, usar el método especial
        if usuario_asociado_id:
            residente = serializer.save()
            from usuarios.models import Usuario
            usuario = Usuario.objects.get(id=usuario_asociado_id)
            residente.asociar_usuario(usuario)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Validaciones adicionales al actualizar un residente"""
        # Validar que la persona asociada existe
        persona_id = serializer.validated_data.get('persona')
        if not persona_id:
            raise serializers.ValidationError("Debe especificar una persona asociada")
        
        # Validar que no se duplique el usuario si se especifica
        usuario_id = serializer.validated_data.get('usuario')
        usuario_asociado_id = serializer.validated_data.get('usuario_asociado')
        
        if usuario_id and usuario_asociado_id:
            raise serializers.ValidationError("Un residente no puede tener usuario propio y usuario asociado al mismo tiempo")
        
        # Si se está asociando un usuario_asociado, usar el método especial
        instance = serializer.instance
        if usuario_asociado_id and not instance.usuario_asociado:
            from usuarios.models import Usuario
            usuario = Usuario.objects.get(id=usuario_asociado_id)
            instance.asociar_usuario(usuario)
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
    permission_classes = [RolPermisoPermission]

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
