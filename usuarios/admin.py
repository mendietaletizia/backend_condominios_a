from django.contrib import admin
from .models import (
    Usuario, Persona, Roles, Permiso, RolPermiso, Empleado,
    Vehiculo, AccesoVehicular, Visita, Invitado, Reclamo, Residentes
)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def save_model(self, request, obj, form, change):
        # Evitar el error de foreign key
        if not change:  # Solo para nuevos objetos
            obj.save()
        else:
            obj.save()

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'telefono']
    search_fields = ['nombre', 'email']

@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ['nombre']

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ['descripcion']

@admin.register(RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ['rol', 'permiso']

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['persona', 'usuario', 'cargo']
    list_filter = ['cargo']

@admin.register(Residentes)
class ResidentesAdmin(admin.ModelAdmin):
    list_display = ['persona']

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'marca', 'modelo', 'color']
    search_fields = ['placa', 'marca', 'modelo']

@admin.register(AccesoVehicular)
class AccesoVehicularAdmin(admin.ModelAdmin):
    list_display = ['placa_detectada', 'fecha', 'ia_autentico', 'confidence']
    list_filter = ['ia_autentico', 'fecha']

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ci', 'fecha_inicio', 'residente']
    list_filter = ['fecha_inicio']

@admin.register(Invitado)
class InvitadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ci', 'evento']

@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'estado', 'fecha', 'residente']
    list_filter = ['estado', 'fecha']
