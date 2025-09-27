from django.db import models
from django.conf import settings
from django.utils import timezone
from comunidad.models import Unidad
from usuarios.models import Persona

class CuotaMensual(models.Model):
    """Cuotas mensuales del condominio - CU22"""
    mes_año = models.CharField(max_length=7)  # Formato: 2025-10
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_limite = models.DateField()
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('borrador', 'Borrador'),
        ('activa', 'Activa'),
        ('cerrada', 'Cerrada')
    ], default='borrador')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Cuota Mensual"
        verbose_name_plural = "Cuotas Mensuales"
        ordering = ['-mes_año']

    def __str__(self):
        return f"Cuota {self.mes_año}"

    def calcular_monto_por_unidad(self):
        """Calcula el monto que debe pagar cada unidad"""
        unidades_activas = Unidad.objects.filter(activa=True)
        if unidades_activas.exists():
            return self.monto_total / unidades_activas.count()
        return 0

class CuotaUnidad(models.Model):
    """Cuotas asignadas a cada unidad - CU22"""
    cuota_mensual = models.ForeignKey(CuotaMensual, on_delete=models.CASCADE, related_name='cuotas_unidad')
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('parcial', 'Pago Parcial')
    ], default='pendiente')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cuota por Unidad"
        verbose_name_plural = "Cuotas por Unidad"
        ordering = ['cuota_mensual', 'unidad']
        unique_together = ['cuota_mensual', 'unidad']

    def __str__(self):
        return f"Cuota {self.cuota_mensual.mes_año} - {self.unidad.numero_casa}"

    def calcular_saldo_pendiente(self):
        """Calcula el saldo pendiente de pago"""
        return self.monto - self.monto_pagado

    def actualizar_estado(self):
        """Actualiza el estado de la cuota según el pago"""
        if self.monto_pagado >= self.monto:
            self.estado = 'pagada'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        else:
            if timezone.now().date() > self.fecha_limite:
                self.estado = 'vencida'
            else:
                self.estado = 'pendiente'
        self.save()

class PagoCuota(models.Model):
    """Pagos realizados por los residentes - CU22"""
    cuota_unidad = models.ForeignKey(CuotaUnidad, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    metodo_pago = models.CharField(max_length=50, choices=[
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
        ('online', 'Pago Online')
    ])
    comprobante = models.FileField(upload_to='comprobantes_pagos/', blank=True, null=True)
    numero_referencia = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Pago de Cuota"
        verbose_name_plural = "Pagos de Cuotas"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago ${self.monto} - {self.fecha_pago}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el monto pagado de la cuota
        self.cuota_unidad.monto_pagado = sum(
            pago.monto for pago in self.cuota_unidad.pagos.all()
        )
        self.cuota_unidad.actualizar_estado()

    def delete(self, *args, **kwargs):
        # Actualizar el monto pagado antes de eliminar
        cuota_unidad = self.cuota_unidad
        super().delete(*args, **kwargs)
        # Recalcular el monto pagado después de eliminar
        cuota_unidad.monto_pagado = sum(
            pago.monto for pago in cuota_unidad.pagos.all()
        )
        cuota_unidad.actualizar_estado()