from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import (
    UsuarioViewSet, PersonaViewSet, ResidentesViewSet, RolesViewSet,
    PermisoViewSet, RolPermisoViewSet, EmpleadoViewSet,
    VehiculoViewSet, AccesoVehicularViewSet, VisitaViewSet,
    InvitadoViewSet, ReclamoViewSet, UsuariosResidentesViewSet
)

router = DefaultRouter()

router.register(r'usuario', UsuarioViewSet)  # Changed from 'usuarios' to 'usuario' to match frontend
router.register(r'persona', PersonaViewSet)  # Changed from 'personas' to 'persona' to match frontend
router.register(r'residentes', ResidentesViewSet)  # <-- NUEVO ENDPOINT
router.register(r'usuarios-residentes', UsuariosResidentesViewSet, basename='usuarios-residentes')  # <-- NUEVO ENDPOINT para usuarios con rol residente
router.register(r'roles', RolesViewSet)
router.register(r'permiso', PermisoViewSet)  # Changed from 'permisos' to 'permiso' to match frontend
router.register(r'rol-permiso', RolPermisoViewSet)  # Changed from 'rol-permisos' to 'rol-permiso' to match frontend
router.register(r'empleados', EmpleadoViewSet)
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'accesos-vehiculares', AccesoVehicularViewSet)
router.register(r'visitas', VisitaViewSet)
router.register(r'invitados', InvitadoViewSet)
router.register(r'reclamos', ReclamoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
