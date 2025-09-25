from django.db import models
from usuarios.models import Residentes

class AreaComun(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)  # Ej: "Gimnasio", "Salón de eventos"
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)  # Activa/Inactiva

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    area = models.ForeignKey(AreaComun, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField(null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['area', 'fecha', 'hora_inicio']

class Mantenimiento(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.BooleanField(default=True)
    area = models.ForeignKey(AreaComun, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Mantenimiento: {self.descripcion[:50]}"

class BitacoraMantenimiento(models.Model):
    id = models.AutoField(primary_key=True)
    avance = models.TextField()
    fecha = models.DateField()
    estado = models.BooleanField(default=True)
    mantenimiento = models.ForeignKey(Mantenimiento, on_delete=models.CASCADE)

    def __str__(self):
        return f"Bitácora: {self.avance[:30]}"

class Reglamento(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.BooleanField(default=True)
    area = models.ForeignKey(AreaComun, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Reglamento: {self.tipo}"