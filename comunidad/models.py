from django.db import models

# Create your models here.
from django.db import models
from usuarios.models import Persona, Residentes

# CU6: Unidades
class Unidad(models.Model):
    id = models.AutoField(primary_key=True)
    numero_casa = models.CharField(max_length=10)
    metros_cuadrados = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_residentes = models.IntegerField()
    cantidad_mascotas = models.IntegerField()
    cantidad_vehiculos = models.IntegerField()

    def __str__(self):
        return f"Unidad {self.numero_casa}"

class ResidentesUnidad(models.Model):
    id = models.AutoField(primary_key=True)
    id_residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    id_unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.BooleanField(default=True)

# CU11: Eventos
class Evento(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField()
    estado = models.BooleanField(default=True)

# CU12: Comunicados / Noticias
class Notificacion(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    contenido = models.TextField()
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=50)  # Ej: "Comunicado", "Noticia"

class NotificacionResidente(models.Model):
    id = models.AutoField(primary_key=True)
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    leido = models.BooleanField(default=False)

# CU17: Actas / Asambleas
class Acta(models.Model):
    id = models.AutoField(primary_key=True)
    contenido = models.TextField()
    fecha_creacion = models.DateField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
