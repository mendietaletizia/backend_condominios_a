from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finanzas.views import ExpensaViewSet, PagoViewSet

router = DefaultRouter()
router.register(r'expensas', ExpensaViewSet)
router.register(r'pagos', PagoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
