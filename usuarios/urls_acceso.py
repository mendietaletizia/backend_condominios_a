from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views_acceso import (
    PlacaVehiculoViewSet, PlacaInvitadoViewSet,
    RegistroAccesoViewSet, ConfiguracionAccesoViewSet,
    DashboardAccesoView
)

# Crear router para los ViewSets
router = DefaultRouter()
router.register(r'placas-vehiculo', PlacaVehiculoViewSet, basename='placas-vehiculo')
router.register(r'placas-invitado', PlacaInvitadoViewSet, basename='placas-invitado')
router.register(r'registros-acceso', RegistroAccesoViewSet, basename='registros-acceso')
router.register(r'configuracion', ConfiguracionAccesoViewSet, basename='configuracion-acceso')

urlpatterns = [
    # Incluir las rutas del router
    path('', include(router.urls)),

    # Rutas adicionales
    path('dashboard/', DashboardAccesoView.as_view(), name='dashboard-acceso'),
    path('registros-acceso/registrar/', RegistroAccesoViewSet.as_view({'post': 'registrar_acceso'}), name='registrar-acceso'),
    path('registros-acceso/<int:pk>/autorizar/', RegistroAccesoViewSet.as_view({'post': 'autorizar_manual'}), name='autorizar-manual'),
    path('registros-acceso/<int:pk>/denegar/', RegistroAccesoViewSet.as_view({'post': 'denegar_manual'}), name='denegar-manual'),
    path('placas-invitado/activas/', PlacaInvitadoViewSet.as_view({'get': 'activas'}), name='placas-invitado-activas'),
    path('configuracion/probar-conexion/', ConfiguracionAccesoViewSet.as_view({'post': 'probar_conexion'}), name='probar-conexion'),
]
