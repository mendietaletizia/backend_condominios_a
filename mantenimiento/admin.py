from django.contrib import admin
from .models import (
    AreaComun, Reserva, Mantenimiento, BitacoraMantenimientoAntigua, Reglamento,
    TipoMantenimiento, PlanMantenimiento, TareaMantenimiento, BitacoraMantenimiento, InventarioArea
)

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

@admin.register(BitacoraMantenimientoAntigua)
class BitacoraMantenimientoAntiguaAdmin(admin.ModelAdmin):
    list_display = ['mantenimiento', 'fecha', 'estado']
    list_filter = ['estado', 'fecha']

@admin.register(Reglamento)
class ReglamentoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'monto', 'estado']
    list_filter = ['tipo', 'estado']

# CU16: Admin para nuevos modelos
@admin.register(TipoMantenimiento)
class TipoMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'prioridad_default', 'activo']
    list_filter = ['tipo', 'prioridad_default', 'activo']
    search_fields = ['nombre', 'descripcion']

@admin.register(PlanMantenimiento)
class PlanMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'area_comun', 'tipo_mantenimiento', 'estado', 'fecha_inicio', 'fecha_fin_estimada']
    list_filter = ['estado', 'prioridad', 'tipo_mantenimiento', 'area_comun']
    search_fields = ['nombre', 'descripcion']
    date_hierarchy = 'fecha_inicio'

@admin.register(TareaMantenimiento)
class TareaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'plan_mantenimiento', 'estado', 'prioridad', 'fecha_inicio', 'fecha_fin_estimada']
    list_filter = ['estado', 'prioridad', 'plan_mantenimiento']
    search_fields = ['nombre', 'descripcion']
    date_hierarchy = 'fecha_inicio'

@admin.register(BitacoraMantenimiento)
class BitacoraMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['plan_mantenimiento', 'tipo_actividad', 'fecha_hora', 'empleado']
    list_filter = ['tipo_actividad', 'fecha_hora', 'plan_mantenimiento']
    search_fields = ['descripcion', 'observaciones']
    date_hierarchy = 'fecha_hora'

@admin.register(InventarioArea)
class InventarioAreaAdmin(admin.ModelAdmin):
    list_display = ['nombre_equipo', 'area_comun', 'estado_actual', 'fecha_proximo_mantenimiento']
    list_filter = ['estado_actual', 'area_comun']
    search_fields = ['nombre_equipo', 'marca', 'modelo', 'numero_serie']
    date_hierarchy = 'fecha_registro'
