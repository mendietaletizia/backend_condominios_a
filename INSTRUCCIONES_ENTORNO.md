# Instrucciones para el Entorno Virtual

## ⚠️ Problema Resuelto

El entorno virtual original (`env`) tenía problemas con las dependencias. Se ha creado un nuevo entorno virtual funcional.

## 🚀 Cómo Ejecutar el Proyecto

### Opción 1: Usar el nuevo entorno virtual (Recomendado)
```bash
cd backend_condominio_a
.\env_working\Scripts\python.exe manage.py runserver
```

### Opción 2: Activar el entorno virtual
```bash
cd backend_condominio_a
.\env_working\Scripts\activate
python manage.py runserver
```

## 📋 Comandos Útiles

### Verificar configuración:
```bash
.\env_working\Scripts\python.exe manage.py check
```

### Aplicar migraciones:
```bash
.\env_working\Scripts\python.exe manage.py migrate
```

### Crear superusuario:
```bash
.\env_working\Scripts\python.exe manage.py createsuperuser
```

### Instalar nuevas dependencias:
```bash
.\env_working\Scripts\pip.exe install nombre_paquete
```

## ✅ Estado Actual

- ✅ **Entorno virtual funcional**: `env_working`
- ✅ **Todas las dependencias instaladas**
- ✅ **PostgreSQL configurado**
- ✅ **Servidor funcionando correctamente**

## 🔧 Configuración de Base de Datos

El proyecto está configurado para usar PostgreSQL:
- **Host**: localhost
- **Puerto**: 5432
- **Base de datos**: condominio_db
- **Usuario**: postgres
- **Password**: postgres

Asegúrate de que PostgreSQL esté ejecutándose y que la base de datos `condominio_db` exista.

## 📝 Notas

- El entorno virtual original (`env`) puede tener problemas
- Usa siempre `env_working` para desarrollo
- Todas las dependencias están correctamente instaladas en `env_working`
