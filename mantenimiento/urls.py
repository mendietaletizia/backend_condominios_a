from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mantenimiento.views import (
    AreaComunViewSet, ReservaViewSet, MantenimientoViewSet,
    BitacoraMantenimientoViewSet, ReglamentoViewSet
)

router = DefaultRouter()
router.register(r'areas-comunes', AreaComunViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'mantenimientos', MantenimientoViewSet)
router.register(r'bitacoras-mantenimiento', BitacoraMantenimientoViewSet)
router.register(r'reglamentos', ReglamentoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
