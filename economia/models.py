from django.db import models
from django.conf import settings
from django.utils import timezone
from usuarios.models import Residentes
from comunidad.models import Reglamento, Unidad
from finanzas.models import Ingreso

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

# CU19: Reportes y Analítica
class ReporteFinanciero(models.Model):
    """Reportes financieros del condominio - CU19"""
    TIPO_REPORTE_CHOICES = [
        ('mensual', 'Reporte Mensual'),
        ('trimestral', 'Reporte Trimestral'),
        ('anual', 'Reporte Anual'),
        ('personalizado', 'Reporte Personalizado')
    ]
    
    ESTADO_CHOICES = [
        ('generando', 'Generando'),
        ('completado', 'Completado'),
        ('error', 'Error')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='generando')
    
    # Datos del reporte
    total_ingresos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gastos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_multas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_neto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Archivo del reporte
    archivo_pdf = models.FileField(upload_to='reportes/', blank=True, null=True)
    archivo_excel = models.FileField(upload_to='reportes/', blank=True, null=True)
    
    # Metadatos
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    generado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Reporte Financiero"
        verbose_name_plural = "Reportes Financieros"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_reporte_display()}"
    
    def calcular_totales(self):
        """Calcula los totales del reporte basado en las fechas"""
        # Ingresos
        ingresos = Ingreso.objects.filter(
            fecha_ingreso__range=[self.fecha_inicio, self.fecha_fin],
            estado='confirmado'
        )
        self.total_ingresos = sum(ing.monto for ing in ingresos)
        
        # Gastos
        gastos = Gastos.objects.filter(
            fecha_hora__date__range=[self.fecha_inicio, self.fecha_fin]
        )
        self.total_gastos = sum(g.monto for g in gastos)
        
        # Multas
        multas = Multa.objects.filter(
            fecha_emision__range=[self.fecha_inicio, self.fecha_fin],
            estado__in=['pagada', 'pendiente']
        )
        self.total_multas = sum(m.monto for m in multas)
        
        # Saldo neto
        self.saldo_neto = self.total_ingresos - self.total_gastos
        
        self.save()

class AnalisisFinanciero(models.Model):
    """Análisis financiero del condominio - CU19"""
    TIPO_ANALISIS_CHOICES = [
        ('tendencia', 'Análisis de Tendencia'),
        ('comparativo', 'Análisis Comparativo'),
        ('proyeccion', 'Proyección Financiera'),
        ('eficiencia', 'Análisis de Eficiencia'),
        ('morosidad', 'Análisis de Morosidad')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    tipo_analisis = models.CharField(max_length=20, choices=TIPO_ANALISIS_CHOICES)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    
    # Resultados del análisis
    datos_analisis = models.JSONField(default=dict)
    conclusiones = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Análisis Financiero"
        verbose_name_plural = "Análisis Financieros"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_analisis_display()}"

class IndicadorFinanciero(models.Model):
    """Indicadores financieros del condominio - CU19"""
    TIPO_INDICADOR_CHOICES = [
        ('liquidez', 'Liquidez'),
        ('solvencia', 'Solvencia'),
        ('rentabilidad', 'Rentabilidad'),
        ('eficiencia', 'Eficiencia'),
        ('morosidad', 'Morosidad')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo_indicador = models.CharField(max_length=20, choices=TIPO_INDICADOR_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=4)
    unidad = models.CharField(max_length=20, default='%')
    fecha_calculo = models.DateField()
    
    # Metadatos
    descripcion = models.TextField(blank=True)
    formula = models.CharField(max_length=200, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Indicador Financiero"
        verbose_name_plural = "Indicadores Financieros"
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f"{self.nombre}: {self.valor}{self.unidad}"

class DashboardFinanciero(models.Model):
    """Dashboard financiero personalizable - CU19"""
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # Configuración del dashboard
    widgets_config = models.JSONField(default=list)
    filtros_default = models.JSONField(default=dict)
    
    # Metadatos
    es_publico = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Dashboard Financiero"
        verbose_name_plural = "Dashboards Financieros"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.nombre
