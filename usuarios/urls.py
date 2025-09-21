from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import (
    UsuarioViewSet, PersonaViewSet, RolesViewSet,
    PermisoViewSet, RolPermisoViewSet, EmpleadoViewSet,
    VehiculoViewSet, AccesoVehicularViewSet, VisitaViewSet,
    InvitadoViewSet, ReclamoViewSet
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'personas', PersonaViewSet)
router.register(r'roles', RolesViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'rol-permisos', RolPermisoViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'accesos-vehiculares', AccesoVehicularViewSet)
router.register(r'visitas', VisitaViewSet)
router.register(r'invitados', InvitadoViewSet)
router.register(r'reclamos', ReclamoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
