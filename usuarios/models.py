from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    rol = models.ForeignKey('Roles', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    # Remover campos que ya están en AbstractUser
    # username, password ya están en AbstractUser
    
    @property
    def nombre_completo(self):
        """Obtener nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def __str__(self):
        return self.username

class Persona(models.Model):
    id = models.AutoField(primary_key=True)
    ci = models.CharField(max_length=20, null=True, blank=True, unique=True)
    nombre = models.CharField(max_length=150)
    email = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nombre

class Residentes(models.Model):
    id = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    usuario_asociado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='residentes_asociados', help_text='Usuario residente principal asociado (opcional)')

    def __str__(self):
        return f"Residente: {self.persona.nombre}"
    
    def save(self, *args, **kwargs):
        """Override save para manejar la asociación automática de usuario"""
        super().save(*args, **kwargs)
        
        # Si se asocia un usuario_asociado, crear automáticamente la relación como propietario
        if self.usuario_asociado and hasattr(self, '_creating_usuario_asociado'):
            self._create_propietario_relation()
    
    def _create_propietario_relation(self):
        """Crear relación automática como propietario si no existe"""
        try:
            from comunidad.models import ResidentesUnidad, Unidad
            
            # Buscar si ya existe una relación activa
            existing_relation = ResidentesUnidad.objects.filter(
                id_residente=self,
                estado=True,
                rol_en_unidad='propietario'
            ).first()
            
            if not existing_relation:
                # Buscar una unidad disponible (por ahora, la primera activa)
                # En el futuro, esto podría ser más específico
                unidad_disponible = Unidad.objects.filter(activa=True).first()
                
                if unidad_disponible:
                    # Verificar si la unidad ya tiene un propietario
                    propietario_existente = ResidentesUnidad.objects.filter(
                        id_unidad=unidad_disponible,
                        estado=True,
                        rol_en_unidad='propietario'
                    ).first()
                    
                    if not propietario_existente:
                        ResidentesUnidad.objects.create(
                            id_residente=self,
                            id_unidad=unidad_disponible,
                            rol_en_unidad='propietario',
                            fecha_inicio=timezone.now().date(),
                            estado=True
                        )
        except Exception as e:
            # Log the error but don't break the save
            print(f"Error creando relación propietario: {e}")
    
    def asociar_usuario(self, usuario):
        """Método para asociar un usuario y crear automáticamente la relación como propietario"""
        self.usuario_asociado = usuario
        self._creating_usuario_asociado = True
        self.save()
        delattr(self, '_creating_usuario_asociado')

class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Permiso(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.descripcion

class RolPermiso(models.Model):
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.rol} - {self.permiso}"

class Empleado(models.Model):
    id = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cargo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.persona} - {self.cargo}"

# Modelos adicionales para casos de uso faltantes
class Vehiculo(models.Model):
    placa = models.CharField(max_length=10, primary_key=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.placa}"

class AccesoVehicular(models.Model):
    id = models.AutoField(primary_key=True)
    placa = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField()
    placa_detectada = models.CharField(max_length=10)
    imagen_url = models.TextField(null=True, blank=True)
    ia_autentico = models.BooleanField(default=False)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Acceso {self.placa_detectada} - {self.fecha}"

class Visita(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    ci = models.CharField(max_length=20)
    vehiculo = models.CharField(max_length=10, null=True, blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_salida = models.DateTimeField(null=True, blank=True)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)

    def __str__(self):
        return f"Visita: {self.nombre} - {self.fecha_inicio}"

class Invitado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    ci = models.CharField(max_length=20)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE, related_name='invitados')
    TIPO_INVITADO_CHOICES = [
        ('casual', 'Visita Casual'),
        ('evento', 'Invitado Evento'),
    ]
    tipo = models.CharField(max_length=10, choices=TIPO_INVITADO_CHOICES, default='casual')
    evento = models.ForeignKey('comunidad.Evento', on_delete=models.CASCADE, null=True, blank=True)
    vehiculo_placa = models.CharField(max_length=10, null=True, blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    # Control de acceso humano (portería)
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_in_by = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitados_checkin')
    check_out_at = models.DateTimeField(null=True, blank=True)
    check_out_by = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitados_checkout')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invitado: {self.nombre} ({self.get_tipo_display()})"

class Reclamo(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    estado = models.BooleanField(default=False)
    fecha = models.DateTimeField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)

    def __str__(self):
        return f"Reclamo: {self.titulo}"

# Modelos para CU14: Gestión de Acceso con IA
class PlacaVehiculo(models.Model):
    """Placas de vehículos de residentes"""
    id = models.AutoField(primary_key=True)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE, related_name='placas_vehiculo')
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.placa} - {self.residente.persona.nombre}"

class PlacaInvitado(models.Model):
    """Placas de vehículos de visitantes autorizados"""
    id = models.AutoField(primary_key=True)
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE, related_name='placas_invitado')
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=50, null=True, blank=True)
    modelo = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)
    nombre_visitante = models.CharField(max_length=100, null=True, blank=True)
    ci_visitante = models.CharField(max_length=20, null=True, blank=True)
    fecha_autorizacion = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitado: {self.placa} - {self.residente.persona.nombre}"

class RegistroAcceso(models.Model):
    """Registro de accesos vehiculares con IA"""
    id = models.AutoField(primary_key=True)

    # Información del vehículo detectado
    placa_detectada = models.CharField(max_length=10)
    marca_detectada = models.CharField(max_length=50, null=True, blank=True)
    modelo_detectado = models.CharField(max_length=50, null=True, blank=True)
    color_detectado = models.CharField(max_length=30, null=True, blank=True)

    # Información de la IA
    ia_confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text='Confianza de la IA (0-100)')
    ia_autentico = models.BooleanField(default=False, help_text='¿La IA confirmó que es auténtico?')
    ia_placa_reconocida = models.BooleanField(default=False, help_text='¿La IA reconoció la placa?')
    ia_vehiculo_reconocido = models.BooleanField(default=False, help_text='¿La IA reconoció el vehículo?')

    # Estado del acceso
    TIPO_ACCESO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    tipo_acceso = models.CharField(max_length=10, choices=TIPO_ACCESO_CHOICES)

    ESTADO_ACCESO_CHOICES = [
        ('autorizado', 'Autorizado'),
        ('denegado', 'Denegado'),
        ('pendiente', 'Pendiente de Autorización'),
        ('error_ia', 'Error en IA'),
    ]
    estado_acceso = models.CharField(max_length=20, choices=ESTADO_ACCESO_CHOICES, default='pendiente')

    # Información técnica
    imagen_url = models.TextField(null=True, blank=True, help_text='URL de la imagen capturada')
    imagen_path = models.TextField(null=True, blank=True, help_text='Path local de la imagen')
    camara_id = models.CharField(max_length=50, null=True, blank=True, help_text='ID de la cámara que capturó')

    # Información de tiempo
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tiempo_procesamiento = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Tiempo en segundos que tomó procesar')

    # Información adicional
    observaciones = models.TextField(null=True, blank=True)
    autorizado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, help_text='Usuario que autorizó manualmente')

    # Relaciones con placas registradas (si se encontró coincidencia)
    placa_vehiculo = models.ForeignKey(PlacaVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    placa_invitado = models.ForeignKey(PlacaInvitado, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.placa_detectada} - {self.fecha_hora} - {self.estado_acceso}"

    class Meta:
        ordering = ['-fecha_hora']

class ConfiguracionAcceso(models.Model):
    """Configuración general del sistema de acceso"""
    id = models.AutoField(primary_key=True)

    # Configuración de horarios
    hora_inicio_restringida = models.TimeField(null=True, blank=True, help_text='Hora de inicio de restricción')
    hora_fin_restringida = models.TimeField(null=True, blank=True, help_text='Hora de fin de restricción')

    # Configuración de IA
    umbral_confianza_placa = models.DecimalField(max_digits=5, decimal_places=2, default=80.0, help_text='Umbral mínimo de confianza para placa (0-100)')
    umbral_confianza_vehiculo = models.DecimalField(max_digits=5, decimal_places=2, default=70.0, help_text='Umbral mínimo de confianza para vehículo (0-100)')
    tiempo_max_procesamiento = models.DecimalField(max_digits=6, decimal_places=2, default=30.0, help_text='Tiempo máximo de procesamiento en segundos')

    # Configuración de notificaciones
    notificar_accesos_denegados = models.BooleanField(default=True)
    notificar_accesos_no_reconocidos = models.BooleanField(default=True)
    notificar_mantenimiento = models.BooleanField(default=True)

    # Configuración de cámaras
    camaras_activas = models.IntegerField(default=1, help_text='Número de cámaras activas')
    fps_captura = models.IntegerField(default=15, help_text='Frames por segundo para captura')

    # Configuración de retención
    dias_retencion_imagenes = models.IntegerField(default=30, help_text='Días para retener imágenes')
    dias_retencion_registros = models.IntegerField(default=90, help_text='Días para retener registros de acceso')

    def __str__(self):
        return "Configuración del Sistema de Acceso"

# CU23: Asignación de Tareas para Empleados - Modelos adicionales
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class TipoTarea(models.Model):
    """Tipos de tareas que pueden asignarse a empleados - CU23"""
    CATEGORIA_CHOICES = [
        ('mantenimiento', 'Mantenimiento'),
        ('limpieza', 'Limpieza'),
        ('seguridad', 'Seguridad'),
        ('administrativo', 'Administrativo'),
        ('jardineria', 'Jardinería'),
        ('piscina', 'Piscina'),
        ('gimnasio', 'Gimnasio'),
        ('salon_eventos', 'Salón de Eventos'),
        ('otro', 'Otro')
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField(blank=True)
    prioridad_default = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    duracion_estimada_horas = models.IntegerField(default=1, help_text="Duración estimada en horas")
    requiere_especialista = models.BooleanField(default=False)
    requiere_herramientas = models.BooleanField(default=False)
    materiales_necesarios = models.TextField(blank=True)
    instrucciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tipo de Tarea"
        verbose_name_plural = "Tipos de Tareas"
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"

class TareaEmpleado(models.Model):
    """Tareas asignadas a empleados - CU23"""
    ESTADO_CHOICES = [
        ('asignada', 'Asignada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('pausada', 'Pausada'),
        ('rechazada', 'Rechazada')
    ]
    
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo_tarea = models.ForeignKey(TipoTarea, on_delete=models.CASCADE)
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='tareas_asignadas')
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tareas_supervisadas')
    
    # Fechas y tiempos
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Estado y prioridad
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='asignada')
    prioridad = models.CharField(max_length=10, choices=TipoTarea.PRIORIDAD_CHOICES, default='media')
    
    # Recursos y materiales
    materiales_proporcionados = models.TextField(blank=True)
    herramientas_necesarias = models.TextField(blank=True)
    costo_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_real = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Seguimiento
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    progreso_porcentaje = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    observaciones_empleado = models.TextField(blank=True)
    observaciones_supervisor = models.TextField(blank=True)
    
    # Archivos adjuntos
    foto_antes = models.ImageField(upload_to='tareas/fotos/', blank=True, null=True)
    foto_despues = models.ImageField(upload_to='tareas/fotos/', blank=True, null=True)
    documento_adjunto = models.FileField(upload_to='tareas/documentos/', blank=True, null=True)
    
    # Metadatos
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarea de Empleado"
        verbose_name_plural = "Tareas de Empleados"
        ordering = ['-fecha_asignacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.empleado_asignado.persona_relacionada.nombre}"
    
    def calcular_progreso(self):
        """Calcula el progreso basado en el estado"""
        if self.estado == 'completada':
            return 100
        elif self.estado == 'en_progreso':
            return self.progreso_porcentaje
        elif self.estado == 'asignada':
            return 0
        return self.progreso_porcentaje
    
    def esta_vencida(self):
        """Verifica si la tarea está vencida"""
        return self.estado not in ['completada', 'cancelada'] and timezone.now() > self.fecha_limite
    
    def tiempo_restante(self):
        """Calcula el tiempo restante para completar la tarea"""
        if self.estado in ['completada', 'cancelada']:
            return None
        
        ahora = timezone.now()
        if ahora > self.fecha_limite:
            return "Vencida"
        
        tiempo_restante = self.fecha_limite - ahora
        dias = tiempo_restante.days
        horas = tiempo_restante.seconds // 3600
        
        if dias > 0:
            return f"{dias} días, {horas} horas"
        else:
            return f"{horas} horas"

class ComentarioTarea(models.Model):
    """Comentarios en tareas de empleados - CU23"""
    id = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(TareaEmpleado, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comentario = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)
    es_interno = models.BooleanField(default=False, help_text="Si es True, solo lo ve el supervisor")
    
    class Meta:
        verbose_name = "Comentario de Tarea"
        verbose_name_plural = "Comentarios de Tareas"
        ordering = ['-fecha_comentario']
    
    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.tarea.titulo}"

class EvaluacionTarea(models.Model):
    """Evaluación de tareas completadas - CU23"""
    CALIFICACION_CHOICES = [
        (1, 'Muy Malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Excelente')
    ]
    
    id = models.AutoField(primary_key=True)
    tarea = models.OneToOneField(TareaEmpleado, on_delete=models.CASCADE, related_name='evaluacion')
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Calificaciones
    calidad_trabajo = models.IntegerField(choices=CALIFICACION_CHOICES)
    cumplimiento_tiempo = models.IntegerField(choices=CALIFICACION_CHOICES)
    uso_recursos = models.IntegerField(choices=CALIFICACION_CHOICES)
    comunicacion = models.IntegerField(choices=CALIFICACION_CHOICES)
    
    # Comentarios
    comentarios_positivos = models.TextField(blank=True)
    areas_mejora = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    
    # Metadatos
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Evaluación de Tarea"
        verbose_name_plural = "Evaluaciones de Tareas"
    
    def __str__(self):
        return f"Evaluación de {self.tarea.titulo}"
    
    def calificacion_promedio(self):
        """Calcula la calificación promedio"""
        return (self.calidad_trabajo + self.cumplimiento_tiempo + self.uso_recursos + self.comunicacion) / 4