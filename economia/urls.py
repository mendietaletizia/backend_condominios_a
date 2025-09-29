from django.urls import path, include
from rest_framework.routers import DefaultRouter
from economia.views import (
    GastosViewSet, MultaViewSet, ReporteViewSet, MorosidadViewSet,
    ReporteFinancieroViewSet, AnalisisFinancieroViewSet, 
    IndicadorFinancieroViewSet, DashboardFinancieroViewSet
)

router = DefaultRouter()
# CU8 y CU9 - Gestión Económica Básica
router.register(r'gastos', GastosViewSet)
router.register(r'multas', MultaViewSet)
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'morosidad', MorosidadViewSet, basename='morosidad')

# CU19 - Reportes y Analítica Avanzada
router.register(r'reportes-financieros', ReporteFinancieroViewSet)
router.register(r'analisis-financieros', AnalisisFinancieroViewSet)
router.register(r'indicadores-financieros', IndicadorFinancieroViewSet)
router.register(r'dashboards-financieros', DashboardFinancieroViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
