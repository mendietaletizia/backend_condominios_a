from rest_framework import viewsets, permissions
from usuarios.models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo
)
from usuarios.serializers.usuarios_serializer import (
    UsuarioSerializer, PersonaSerializer, RolesSerializer,
    PermisoSerializer, RolPermisoSerializer, EmpleadoSerializer,
    VehiculoSerializer, AccesoVehicularSerializer, VisitaSerializer,
    InvitadoSerializer, ReclamoSerializer
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
        empleado = Empleado.objects.filter(usuario=request.user).first()
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
        if not self.request.user or not self.request.user.is_authenticated:
            return Persona.objects.none()
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
