from django.contrib import admin
from .models import (
    CuotaMensual, CuotaUnidad, PagoCuota
)

@admin.register(CuotaMensual)
class CuotaMensualAdmin(admin.ModelAdmin):
    list_display = ['mes_año', 'monto_total', 'fecha_limite', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['mes_año', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']

@admin.register(CuotaUnidad)
class CuotaUnidadAdmin(admin.ModelAdmin):
    list_display = ['cuota_mensual', 'unidad', 'monto', 'estado', 'monto_pagado', 'fecha_limite']
    list_filter = ['estado', 'cuota_mensual', 'unidad']
    search_fields = ['unidad__numero_casa', 'cuota_mensual__mes_año']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']

@admin.register(PagoCuota)
class PagoCuotaAdmin(admin.ModelAdmin):
    list_display = ['cuota_unidad', 'monto', 'fecha_pago', 'metodo_pago', 'registrado_por']
    list_filter = ['metodo_pago', 'fecha_pago']
    search_fields = ['cuota_unidad__unidad__numero_casa', 'numero_referencia']
    readonly_fields = ['fecha_creacion']