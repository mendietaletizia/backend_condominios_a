from django.urls import path
from autenticacion.views import LoginView, LogoutView, PlacaInvitadoListCreateView, PlacaInvitadoDetailView, PlacaInvitadoActivasView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('placas-invitados/', PlacaInvitadoListCreateView.as_view(), name='placas-invitados-list-create'),
    path('placas-invitados/<int:pk>/', PlacaInvitadoDetailView.as_view(), name='placas-invitados-detail'),
    path('placas-invitados/activas/', PlacaInvitadoActivasView.as_view(), name='placas-invitados-activas'),
]
