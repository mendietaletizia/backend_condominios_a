from django.contrib import admin
from .models import Gastos, Multa

@admin.register(Gastos)
class GastosAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha_hora']
    list_filter = ['fecha_hora']

@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['motivo', 'monto', 'fecha_emision', 'fecha_vencimiento', 'estado', 'residente']
    list_filter = ['fecha_emision', 'estado', 'reglamento']
    search_fields = ['motivo', 'residente__persona__nombre', 'residente__persona__apellido']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
