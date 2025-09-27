from django.db import models
from usuarios.models import Residentes
from comunidad.models import Reglamento

# CU8: Gastos
class Gastos(models.Model):
    id = models.AutoField(primary_key=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField()

# CU9: Multas
class Multa(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('anulada', 'Anulada'),
    ]
    
    id = models.AutoField(primary_key=True)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    reglamento = models.ForeignKey(Reglamento, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.TextField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_emision']
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'
    
    def __str__(self):
        return f"Multa {self.id} - {self.residente.persona.nombre} - Bs. {self.monto}"
