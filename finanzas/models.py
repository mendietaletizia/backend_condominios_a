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
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('cheque', 'Cheque'),
    ]
    
    id = models.AutoField(primary_key=True)
    fecha_pago = models.DateField(null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='transferencia')
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    comprobante_url = models.TextField(null=True, blank=True)
    fecha_vencimiento = models.DateField()
    estado_pago = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    referencia = models.CharField(max_length=100, null=True, blank=True)
    expensa = models.ForeignKey('Expensa', on_delete=models.CASCADE, null=True, blank=True)
