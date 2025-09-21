from django.contrib import admin
from .models import AreaComun, Reserva, Mantenimiento, BitacoraMantenimiento, Reglamento

@admin.register(AreaComun)
class AreaComunAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'estado']
    list_filter = ['tipo', 'estado']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['residente', 'area', 'fecha', 'hora_inicio', 'estado']
    list_filter = ['estado', 'fecha']

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'fecha_inicio', 'fecha_fin', 'estado']
    list_filter = ['estado', 'fecha_inicio']

@admin.register(BitacoraMantenimiento)
class BitacoraMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['mantenimiento', 'fecha', 'estado']
    list_filter = ['estado', 'fecha']

@admin.register(Reglamento)
class ReglamentoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'monto', 'estado']
    list_filter = ['tipo', 'estado']
