"""
URL configuration for backend_condominio_a project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('autenticacion.urls')),      # CU1, CU2
    path('api/', include('usuarios.urls')),       # CU3, CU4, CU5, CU13
    path('api/', include('comunidad.urls')),     # CU6, CU11, CU12, CU17
    path('api/', include('finanzas.urls')),       # CU18
    path('api/', include('economia.urls')),       # CU8, CU9, CU19, CU20
    path('api/', include('mantenimiento.urls')), # CU10
    path('api/', include('usuarios.urls_acceso')), # CU14 - Gestión de Accesos
]
