from django.urls import path, include
from rest_framework.routers import DefaultRouter
from comunidad.views import (
    UnidadViewSet, ResidentesUnidadViewSet, EventoViewSet,
    NotificacionViewSet, NotificacionResidenteViewSet, ActaViewSet
)

router = DefaultRouter()
router.register(r'unidades', UnidadViewSet)
router.register(r'residentes-unidad', ResidentesUnidadViewSet)
router.register(r'eventos', EventoViewSet)
router.register(r'notificaciones', NotificacionViewSet)
router.register(r'notificaciones-residente', NotificacionResidenteViewSet)
router.register(r'actas', ActaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
