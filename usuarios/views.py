from rest_framework import viewsets, permissions
from usuarios.models import Usuario, Persona, Roles, Permiso, RolPermiso, Empleado
from usuarios.serializers.usuarios_serializer import (
    UsuarioSerializer, PersonaSerializer, RolesSerializer,
    PermisoSerializer, RolPermisoSerializer, EmpleadoSerializer
)
from rest_framework.permissions import IsAuthenticated


# Permiso personalizado para acceso de administrador
class RolPermisoPermission(permissions.BasePermission):
    """
    Solo usuarios con cargo Administrador pueden acceder
    """
    def has_permission(self, request, view):
        user = getattr(request.user, 'usuario', None)
        if not user:
            return False
        empleado = Empleado.objects.filter(usuario=user).first()
        return empleado and empleado.cargo.lower() == 'administrador'



class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [RolPermisoPermission]



class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [RolPermisoPermission]

    def get_queryset(self):
        user = getattr(self.request.user, 'usuario', None)
        empleado = Empleado.objects.filter(usuario=user).first()
        if empleado and empleado.cargo.lower() == "administrador":
            return Persona.objects.all()
        elif empleado:
            return Persona.objects.filter(id=empleado.persona.id)
        return Persona.objects.none()



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
