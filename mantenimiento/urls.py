from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mantenimiento.views import AreaComunViewSet, ReservaViewSet

router = DefaultRouter()
router.register(r'areas-comunes', AreaComunViewSet)
router.register(r'reservas', ReservaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
