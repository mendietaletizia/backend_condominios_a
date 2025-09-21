from django.contrib import admin
from .models import Expensa, Pago

@admin.register(Expensa)
class ExpensaAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'fecha_emision', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'fecha_emision']

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['residente', 'monto', 'fecha_pago', 'metodo_pago', 'fecha_vencimiento']
    list_filter = ['metodo_pago', 'fecha_pago']
