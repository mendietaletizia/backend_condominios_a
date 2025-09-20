from django.db import models

# Create your models here.
from django.db import models
from usuarios.models import Residentes

class AreaComun(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)  # Ej: "Gimnasio", "Salón de eventos"
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)  # Activa/Inactiva

class Reserva(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    area = models.ForeignKey(AreaComun, on_delete=models.CASCADE)
    estado = models.BooleanField(default=False)  # Confirmada o pendiente
