from django.db import models

# Create your models here.
from django.db import models
from usuarios.models import Residentes
from finanzas.models import Pago

# CU8: Gastos
class Gastos(models.Model):
    id = models.AutoField(primary_key=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField()

# CU9: Multas
class Multa(models.Model):
    id = models.AutoField(primary_key=True)
    motivo = models.TextField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
