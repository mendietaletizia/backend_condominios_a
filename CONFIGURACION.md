# Configuración del Backend - Condominio A

## ✅ Configuración Completada

El proyecto ahora está configurado para funcionar tanto en **desarrollo local** como en **producción en la nube**.

## 🔧 Configuración Actual

### Variables de Entorno
El proyecto usa las siguientes variables de entorno:

- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: Modo debug (True para desarrollo, False para producción)
- `DATABASE_URL`: URL de la base de datos
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`: Configuración de email
- `REDIS_URL`: URL de Redis para caché
- `SECURE_SSL_REDIRECT`: Redirección HTTPS

### Base de Datos
- **Desarrollo**: PostgreSQL (configurado por defecto)
- **Producción**: PostgreSQL (configurado con `DATABASE_URL`)

## 🚀 Cómo Usar

### Para Desarrollo Local:
1. **PostgreSQL configurado por defecto:**
   ```bash
   # Asegúrate de que PostgreSQL esté ejecutándose
   # La base de datos 'condominio_db' debe existir
   python manage.py runserver
   ```

2. **Si tienes credenciales diferentes:**
   ```bash
   # Configura las variables de entorno:
   set DATABASE_URL=postgresql://tu_usuario:tu_password@localhost:5432/condominio_db
   python manage.py runserver
   ```

### Para Producción (Railway/Cloud):
1. **Configura las variables de entorno en tu plataforma:**
   ```
   SECRET_KEY=tu-clave-secreta-super-segura
   DEBUG=False
   DATABASE_URL=postgresql://usuario:password@host:5432/database
   SECURE_SSL_REDIRECT=True
   ```

## 📁 Archivos de Configuración

- `settings.py`: Configuración principal (combinada y optimizada)
- `env_local`: Ejemplo de variables de entorno para desarrollo
- `env.example`: Ejemplo de variables de entorno para producción

## 🔒 Características de Seguridad

- **Headers de seguridad** automáticos en producción
- **HTTPS** configurado para producción
- **Cookies seguras** en producción
- **Validación de contraseñas** mejorada (mínimo 8 caracteres)

## 📊 Características de Rendimiento

- **Sistema de caché** (Redis en producción, memoria local en desarrollo)
- **Logging avanzado** con archivos separados
- **Paginación automática** en APIs (20 elementos por página)
- **Archivos estáticos optimizados** para producción

## 🛠️ Comandos Útiles

```bash
# Verificar configuración
python manage.py check

# Ejecutar servidor
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

## 🌐 URLs Configuradas

- **Desarrollo**: `http://localhost:8000`
- **Producción**: `https://backendcondominiosa-production.up.railway.app`

## 📝 Notas Importantes

1. **El proyecto funciona con PostgreSQL por defecto** para desarrollo local
2. **Asegúrate de que PostgreSQL esté ejecutándose** y la base de datos `condominio_db` exista
3. **Todas las optimizaciones están activas** automáticamente
4. **La configuración se adapta** según el entorno (desarrollo/producción)
5. **Los logs se guardan** en la carpeta `logs/`
6. **WhiteNoise** sirve archivos estáticos en producción

¡Tu proyecto está listo para desarrollo y despliegue en la nube! 🎉
