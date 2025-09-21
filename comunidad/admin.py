from django.contrib import admin
from .models import Unidad, ResidentesUnidad, Evento, Notificacion, NotificacionResidente, Acta

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ['numero_casa', 'metros_cuadrados', 'cantidad_residentes']
    search_fields = ['numero_casa']

@admin.register(ResidentesUnidad)
class ResidentesUnidadAdmin(admin.ModelAdmin):
    list_display = ['id_residente', 'id_unidad', 'fecha_inicio', 'estado']
    list_filter = ['estado', 'fecha_inicio']

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'fecha', 'estado']
    list_filter = ['estado', 'fecha']

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'fecha']
    list_filter = ['tipo', 'fecha']

@admin.register(NotificacionResidente)
class NotificacionResidenteAdmin(admin.ModelAdmin):
    list_display = ['notificacion', 'residente', 'leido']
    list_filter = ['leido']

@admin.register(Acta)
class ActaAdmin(admin.ModelAdmin):
    list_display = ['fecha_creacion', 'residente']
    list_filter = ['fecha_creacion']
