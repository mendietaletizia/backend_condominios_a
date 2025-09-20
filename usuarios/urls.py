from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import (
    UsuarioViewSet, PersonaViewSet, RolesViewSet,
    PermisoViewSet, RolPermisoViewSet, EmpleadoViewSet
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'personas', PersonaViewSet)
router.register(r'roles', RolesViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'rol-permisos', RolPermisoViewSet)
router.register(r'empleados', EmpleadoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
