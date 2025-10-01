from django.urls import path, include
from rest_framework.routers import DefaultRouter
from comunidad.views import (
    UnidadViewSet, ResidentesUnidadViewSet, EventoViewSet,
    NotificacionViewSet, NotificacionResidenteViewSet, ActaViewSet, MascotaViewSet, ReglamentoViewSet,
    ReservaViewSet
)

router = DefaultRouter()
router.register(r'unidades', UnidadViewSet)
router.register(r'residentes-unidad', ResidentesUnidadViewSet)
router.register(r'eventos', EventoViewSet)
router.register(r'notificaciones', NotificacionViewSet)
router.register(r'notificaciones-residente', NotificacionResidenteViewSet)
router.register(r'actas', ActaViewSet)
router.register(r'mascotas', MascotaViewSet)
router.register(r'reglamento', ReglamentoViewSet)
router.register(r'reservas', ReservaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
