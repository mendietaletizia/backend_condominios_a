from django.db import models
from django.conf import settings
from django.utils import timezone
from usuarios.models import Residentes, Empleado

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

class BitacoraMantenimientoAntigua(models.Model):
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

# CU16: Mantenimiento de Áreas Comunes - Modelos adicionales
class TipoMantenimiento(models.Model):
    """Tipos de mantenimiento para áreas comunes - CU16"""
    TIPO_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('correctivo', 'Mantenimiento Correctivo'),
        ('emergencia', 'Mantenimiento de Emergencia'),
        ('limpieza', 'Limpieza y Aseo'),
        ('reparacion', 'Reparación'),
        ('renovacion', 'Renovación'),
        ('inspeccion', 'Inspección')
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    prioridad_default = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    frecuencia_dias = models.IntegerField(default=30, help_text="Frecuencia en días para mantenimiento preventivo")
    duracion_estimada_horas = models.IntegerField(default=2, help_text="Duración estimada en horas")
    costo_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    requiere_especialista = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tipo de Mantenimiento"
        verbose_name_plural = "Tipos de Mantenimiento"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class PlanMantenimiento(models.Model):
    """Plan de mantenimiento para áreas comunes - CU16"""
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('pausado', 'Pausado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    area_comun = models.ForeignKey(AreaComun, on_delete=models.CASCADE, related_name='planes_mantenimiento')
    tipo_mantenimiento = models.ForeignKey(TipoMantenimiento, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField()
    fecha_fin_real = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    prioridad = models.CharField(max_length=10, choices=TipoMantenimiento.PRIORIDAD_CHOICES, default='media')
    
    # Asignación
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Costos y recursos
    costo_presupuestado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_real = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    materiales_necesarios = models.TextField(blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planes_creados')
    
    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.area_comun.nombre}"
    
    def calcular_progreso(self):
        """Calcula el progreso del plan de mantenimiento"""
        if self.fecha_fin_real:
            return 100
        
        hoy = timezone.now().date()
        if hoy <= self.fecha_inicio:
            return 0
        
        total_dias = (self.fecha_fin_estimada - self.fecha_inicio).days
        dias_transcurridos = (hoy - self.fecha_inicio).days
        
        if total_dias <= 0:
            return 100
        
        progreso = min((dias_transcurridos / total_dias) * 100, 100)
        return round(progreso, 2)
    
    def esta_vencido(self):
        """Verifica si el plan está vencido"""
        return self.estado == 'activo' and timezone.now().date() > self.fecha_fin_estimada

class TareaMantenimiento(models.Model):
    """Tareas específicas dentro de un plan de mantenimiento - CU16"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('pausada', 'Pausada')
    ]
    
    id = models.AutoField(primary_key=True)
    plan_mantenimiento = models.ForeignKey(PlanMantenimiento, on_delete=models.CASCADE, related_name='tareas')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField()
    fecha_fin_real = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    prioridad = models.CharField(max_length=10, choices=TipoMantenimiento.PRIORIDAD_CHOICES, default='media')
    
    # Asignación
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Recursos
    materiales_utilizados = models.TextField(blank=True)
    costo_real = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarea de Mantenimiento"
        verbose_name_plural = "Tareas de Mantenimiento"
        ordering = ['fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} - {self.plan_mantenimiento.nombre}"
    
    def calcular_progreso(self):
        """Calcula el progreso de la tarea"""
        if self.estado == 'completada':
            return 100
        elif self.estado == 'pendiente':
            return 0
        elif self.estado == 'en_progreso':
            hoy = timezone.now().date()
            if hoy <= self.fecha_inicio:
                return 0
            
            total_dias = (self.fecha_fin_estimada - self.fecha_inicio).days
            dias_transcurridos = (hoy - self.fecha_inicio).days
            
            if total_dias <= 0:
                return 100
            
            progreso = min((dias_transcurridos / total_dias) * 100, 100)
            return round(progreso, 2)
        
        return 0

class BitacoraMantenimiento(models.Model):
    """Bitácora de actividades de mantenimiento - CU16"""
    TIPO_ACTIVIDAD_CHOICES = [
        ('inicio', 'Inicio de Trabajo'),
        ('progreso', 'Progreso'),
        ('completado', 'Trabajo Completado'),
        ('problema', 'Problema Encontrado'),
        ('solucion', 'Solución Aplicada'),
        ('observacion', 'Observación'),
        ('material', 'Uso de Material'),
        ('pausa', 'Pausa en Trabajo')
    ]
    
    id = models.AutoField(primary_key=True)
    plan_mantenimiento = models.ForeignKey(PlanMantenimiento, on_delete=models.CASCADE, related_name='bitacoras', null=True, blank=True)
    tarea = models.ForeignKey(TareaMantenimiento, on_delete=models.CASCADE, null=True, blank=True, related_name='bitacoras')
    tipo_actividad = models.CharField(max_length=20, choices=TIPO_ACTIVIDAD_CHOICES, default='observacion')
    descripcion = models.TextField(default='')
    fecha_hora = models.DateTimeField(default=timezone.now)
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    materiales_usados = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    
    # Archivos adjuntos
    foto_antes = models.ImageField(upload_to='mantenimiento/fotos/', blank=True, null=True)
    foto_despues = models.ImageField(upload_to='mantenimiento/fotos/', blank=True, null=True)
    documento_adjunto = models.FileField(upload_to='mantenimiento/documentos/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Bitácora de Mantenimiento"
        verbose_name_plural = "Bitácoras de Mantenimiento"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.get_tipo_actividad_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

class InventarioArea(models.Model):
    """Inventario de equipos y materiales por área común - CU16"""
    ESTADO_CHOICES = [
        ('bueno', 'Buen Estado'),
        ('regular', 'Estado Regular'),
        ('malo', 'Mal Estado'),
        ('fuera_servicio', 'Fuera de Servicio'),
        ('reparacion', 'En Reparación')
    ]
    
    id = models.AutoField(primary_key=True)
    area_comun = models.ForeignKey(AreaComun, on_delete=models.CASCADE, related_name='inventario')
    nombre_equipo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    fecha_adquisicion = models.DateField(null=True, blank=True)
    costo_adquisicion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado_actual = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='bueno')
    
    # Mantenimiento
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True)
    fecha_proximo_mantenimiento = models.DateField(null=True, blank=True)
    frecuencia_mantenimiento_dias = models.IntegerField(default=90)
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Inventario de Área"
        verbose_name_plural = "Inventario de Áreas"
        ordering = ['area_comun', 'nombre_equipo']
    
    def __str__(self):
        return f"{self.nombre_equipo} - {self.area_comun.nombre}"
    
    def necesita_mantenimiento(self):
        """Verifica si el equipo necesita mantenimiento"""
        if not self.fecha_proximo_mantenimiento:
            return False
        return timezone.now().date() >= self.fecha_proximo_mantenimiento