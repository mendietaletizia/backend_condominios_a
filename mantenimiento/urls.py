from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mantenimiento.views import (
    AreaComunViewSet, ReservaViewSet, MantenimientoViewSet,
    BitacoraMantenimientoViewSet, ReglamentoViewSet, TipoMantenimientoViewSet,
    PlanMantenimientoViewSet, TareaMantenimientoViewSet, InventarioAreaViewSet,
    EstadisticasMantenimientoViewSet
)

router = DefaultRouter()
router.register(r'areas-comunes', AreaComunViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'mantenimientos', MantenimientoViewSet)
router.register(r'bitacoras-mantenimiento', BitacoraMantenimientoViewSet)
router.register(r'reglamentos', ReglamentoViewSet)
router.register(r'tipos-mantenimiento', TipoMantenimientoViewSet)
router.register(r'planes-mantenimiento', PlanMantenimientoViewSet)
router.register(r'tareas-mantenimiento', TareaMantenimientoViewSet)
router.register(r'inventario-areas', InventarioAreaViewSet)
router.register(r'estadisticas-mantenimiento', EstadisticasMantenimientoViewSet, basename='estadisticas-mantenimiento')

urlpatterns = [
    path('', include(router.urls)),
]
