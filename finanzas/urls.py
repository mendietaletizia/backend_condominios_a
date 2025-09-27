from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CuotaMensualViewSet, CuotaUnidadViewSet, PagoCuotaViewSet
)

router = DefaultRouter()
# CU22: Gestión de Cuotas y Expensas
router.register(r'cuotas-mensuales', CuotaMensualViewSet)
router.register(r'cuotas-unidad', CuotaUnidadViewSet)
router.register(r'pagos', PagoCuotaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]