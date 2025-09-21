from django.contrib import admin
from .models import Gastos, Multa

@admin.register(Gastos)
class GastosAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha_hora']
    list_filter = ['fecha_hora']

@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['motivo', 'monto', 'fecha', 'residente']
    list_filter = ['fecha']
