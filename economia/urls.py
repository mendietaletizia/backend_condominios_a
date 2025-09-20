from django.urls import path, include
from rest_framework.routers import DefaultRouter
from economia.views import GastosViewSet, MultaViewSet, ReporteViewSet, MorosidadViewSet

router = DefaultRouter()
router.register(r'gastos', GastosViewSet)
router.register(r'multas', MultaViewSet)
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'morosidad', MorosidadViewSet, basename='morosidad')

urlpatterns = [
    path('', include(router.urls)),
]
