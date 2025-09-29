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
        ('parcial', 'Pago Parcial'),
        ('procesando', 'Procesando Pago'),
        ('fallido', 'Pago Fallido')
    ], default='pendiente')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Campos para integración con pasarela de pago
    payment_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID del pago en la pasarela")
    payment_url = models.URLField(blank=True, null=True, help_text="URL de pago generada por la pasarela")
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado')
    ], default='pending', help_text="Estado del pago en la pasarela")
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="Método de pago usado")
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Referencia del pago")

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

class Ingreso(models.Model):
    """Gestión de Ingresos del Condominio - CU18"""
    TIPO_INGRESO_CHOICES = [
        ('cuotas', 'Cuotas Mensuales'),
        ('multas', 'Multas'),
        ('servicios', 'Servicios Adicionales'),
        ('alquiler', 'Alquiler de Áreas Comunes'),
        ('eventos', 'Eventos'),
        ('donaciones', 'Donaciones'),
        ('otros', 'Otros Ingresos')
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado')
    ]
    
    id = models.AutoField(primary_key=True)
    tipo_ingreso = models.CharField(max_length=20, choices=TIPO_INGRESO_CHOICES)
    concepto = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_ingreso = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Relaciones opcionales
    unidad_relacionada = models.ForeignKey(Unidad, on_delete=models.SET_NULL, null=True, blank=True, 
                                         help_text="Unidad relacionada con el ingreso")
    residente_relacionado = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True,
                                            help_text="Residente relacionado con el ingreso")
    cuota_relacionada = models.ForeignKey(CuotaUnidad, on_delete=models.SET_NULL, null=True, blank=True,
                                         help_text="Cuota relacionada con el ingreso")
    
    # Campos administrativos
    comprobante = models.FileField(upload_to='comprobantes_ingresos/', blank=True, null=True)
    numero_referencia = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
        ordering = ['-fecha_ingreso', '-fecha_registro']
    
    def __str__(self):
        return f"{self.get_tipo_ingreso_display()} - ${self.monto} - {self.fecha_ingreso}"
    
    def get_mes_año(self):
        """Retorna el mes y año del ingreso"""
        return self.fecha_ingreso.strftime('%Y-%m')
    
    def es_cuota_mensual(self):
        """Verifica si es un ingreso por cuota mensual"""
        return self.tipo_ingreso == 'cuotas'
    
    def es_multa(self):
        """Verifica si es un ingreso por multa"""
        return self.tipo_ingreso == 'multas'

class ResumenIngresos(models.Model):
    """Resumen mensual de ingresos - CU18"""
    mes_año = models.CharField(max_length=7)  # Formato: 2025-10
    total_cuotas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_multas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_servicios = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_alquiler = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_eventos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_donaciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_otros = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_general = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Resumen de Ingresos"
        verbose_name_plural = "Resúmenes de Ingresos"
        ordering = ['-mes_año']
        unique_together = ['mes_año']
    
    def __str__(self):
        return f"Resumen Ingresos {self.mes_año}"
    
    def calcular_totales(self):
        """Calcula los totales basado en los ingresos del mes"""
        ingresos = Ingreso.objects.filter(
            fecha_ingreso__year=self.fecha_ingreso.year,
            fecha_ingreso__month=self.fecha_ingreso.month,
            estado='confirmado'
        )
        
        self.total_cuotas = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'cuotas')
        self.total_multas = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'multas')
        self.total_servicios = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'servicios')
        self.total_alquiler = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'alquiler')
        self.total_eventos = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'eventos')
        self.total_donaciones = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'donaciones')
        self.total_otros = sum(ing.monto for ing in ingresos if ing.tipo_ingreso == 'otros')
        
        self.total_general = (
            self.total_cuotas + self.total_multas + self.total_servicios +
            self.total_alquiler + self.total_eventos + self.total_donaciones + self.total_otros
        )
        self.save()