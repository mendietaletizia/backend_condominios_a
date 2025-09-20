from django.db import models

# Create your models here.
from django.db import models
from usuarios.models import Residentes

class Expensa(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.descripcion} - {self.monto}"

class Pago(models.Model):
    id = models.AutoField(primary_key=True)
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    comprobante_url = models.TextField(null=True, blank=True)
    fecha_vencimiento = models.DateField()
