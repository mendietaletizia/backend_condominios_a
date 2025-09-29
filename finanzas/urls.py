from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CuotaMensualViewSet, CuotaUnidadViewSet, PagoCuotaViewSet, CuotasResidenteViewSet,
    IngresoViewSet, ResumenIngresosViewSet
)

router = DefaultRouter()
# CU22: Gestión de Cuotas y Expensas
router.register(r'cuotas-mensuales', CuotaMensualViewSet)
router.register(r'cuotas-unidad', CuotaUnidadViewSet)
router.register(r'pagos', PagoCuotaViewSet)
router.register(r'cuotas-residente', CuotasResidenteViewSet, basename='cuotas-residente')

# CU18: Gestión de Ingresos
router.register(r'ingresos', IngresoViewSet)
router.register(r'resumen-ingresos', ResumenIngresosViewSet)

urlpatterns = [
    path('', include(router.urls)),
]