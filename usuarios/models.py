from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    
    # Remover campos que ya están en AbstractUser
    # username, password ya están en AbstractUser
    
    def __str__(self):
        return self.username

class Persona(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    email = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nombre

class Residentes(models.Model):
    id = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Residente: {self.persona.nombre}"

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
    evento = models.ForeignKey('comunidad.Evento', on_delete=models.CASCADE)

    def __str__(self):
        return f"Invitado: {self.nombre}"

class Reclamo(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    estado = models.BooleanField(default=False)
    fecha = models.DateTimeField()
    residente = models.ForeignKey(Residentes, on_delete=models.CASCADE)

    def __str__(self):
        return f"Reclamo: {self.titulo}"
