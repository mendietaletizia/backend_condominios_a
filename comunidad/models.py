from django.db import models
from usuarios.models import Persona, Residentes
from mantenimiento.models import AreaComun

# CU6: Unidades
class Unidad(models.Model):
    id = models.AutoField(primary_key=True)
    numero_casa = models.CharField(max_length=10, unique=True, help_text="Número único de la unidad (ej: A-101, B-205)")
    metros_cuadrados = models.DecimalField(max_digits=10, decimal_places=2, help_text="Área en metros cuadrados")
    cantidad_residentes = models.IntegerField(default=0, help_text="Número de residentes actuales")
    cantidad_mascotas = models.IntegerField(default=0, help_text="Número de mascotas registradas")
    cantidad_vehiculos = models.IntegerField(default=0, help_text="Número de vehículos registrados")
    activa = models.BooleanField(default=True, help_text="Indica si la unidad está activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['numero_casa']
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'

    def __str__(self):
        return f"Unidad {self.numero_casa}"
    
    @property
    def tiene_residentes(self):
        """Verifica si la unidad tiene residentes asociados"""
        return self.residentesunidad_set.filter(estado=True).exists()
    
    @property
    def tiene_mascotas(self):
        """Verifica si la unidad tiene mascotas asociadas"""
        return self.mascota_set.filter(activo=True).exists()

class ResidentesUnidad(models.Model):
    TIPO_RESIDENTE_CHOICES = [
        ('residente', 'Residente'),
        ('inquilino', 'Inquilino'),
        ('propietario', 'Propietario'),
        ('familiar', 'Familiar'),
    ]
    
    id = models.AutoField(primary_key=True)
    id_residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    id_unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    rol_en_unidad = models.CharField(max_length=20, choices=TIPO_RESIDENTE_CHOICES, default='residente')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['id_residente', 'id_unidad', 'fecha_inicio']

# CU11: Eventos
class Evento(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField()
    estado = models.BooleanField(default=True)
    areas = models.ManyToManyField(AreaComun, blank=True)

# CU12: Comunicados / Noticias
class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('cuota', 'Cuota'),
        ('multa', 'Multa'),
        ('comunicado', 'Comunicado'),
        ('evento', 'Evento'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    prioridad = models.CharField(max_length=20, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ], default='media')
    enviar_a_todos = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"

class NotificacionResidente(models.Model):
    id = models.AutoField(primary_key=True)
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)
    leido = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['notificacion', 'residente']
        verbose_name = 'Notificación por Residente'
        verbose_name_plural = 'Notificaciones por Residente'

# CU17: Actas / Asambleas
class Acta(models.Model):
    id = models.AutoField(primary_key=True)
    contenido = models.TextField()
    fecha_creacion = models.DateField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)

# REGLAMENTO DEL CONDOMINIO
class Reglamento(models.Model):
    TIPO_ARTICULO_CHOICES = [
        ('general', 'General'),
        ('multa', 'Multa'),
        ('sancion', 'Sanción'),
        ('cuota', 'Cuota'),
        ('mantenimiento', 'Mantenimiento'),
        ('convivencia', 'Convivencia'),
    ]
    
    id = models.AutoField(primary_key=True)
    articulo = models.CharField(max_length=10, unique=True)  # Art. 1, Art. 2, etc.
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_ARTICULO_CHOICES)
    monto_multa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dias_suspension = models.IntegerField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['articulo']
        verbose_name = 'Reglamento'
        verbose_name_plural = 'Reglamentos'
    
    def __str__(self):
        return f"{self.articulo} - {self.titulo}"

# CU5: Mascotas de Residentes
class Mascota(models.Model):
    TIPO_MASCOTA_CHOICES = [
        ('perro', 'Perro'),
        ('gato', 'Gato'),
        ('ave', 'Ave'),
        ('pez', 'Pez'),
        ('otro', 'Otro'),
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_MASCOTA_CHOICES)
    raza = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE, related_name='mascotas')
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo}) - {self.residente.persona.nombre}"
