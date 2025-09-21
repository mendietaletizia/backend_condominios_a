# Documentación de la API - Sistema de Gestión de Condominio

## Resumen de Casos de Uso Implementados

### ✅ **Casos de Uso Completamente Implementados:**

#### **CU1/CU2: Autenticación (app: autenticacion)**
- **CU1**: Iniciar sesión
- **CU2**: Cerrar sesión
- **Endpoints**: 
  - `POST /api/auth/login/` - Iniciar sesión
  - `POST /api/auth/logout/` - Cerrar sesión

#### **CU3: Gestión de usuarios (app: usuarios)**
- Registrar, editar, eliminar usuarios
- **Endpoints**: `GET/POST/PUT/DELETE /api/usuarios/usuarios/`

#### **CU4: Gestión de roles y permisos (app: usuarios)**
- Configurar roles, permisos y niveles de acceso
- **Endpoints**: 
  - `GET/POST/PUT/DELETE /api/usuarios/roles/`
  - `GET/POST/PUT/DELETE /api/usuarios/permisos/`
  - `GET/POST/PUT/DELETE /api/usuarios/rol-permisos/`

#### **CU5: Gestión de residentes e inquilinos (app: usuarios + comunidad)**
- Asociar residentes a unidades habitacionales
- **Endpoints**: 
  - `GET/POST/PUT/DELETE /api/usuarios/personas/`
  - `GET/POST/PUT/DELETE /api/comunidad/residentes-unidad/`

#### **CU6: Gestión de unidades habitacionales (app: comunidad)**
- Alta, baja y edición de unidades
- **Endpoints**: `GET/POST/PUT/DELETE /api/comunidad/unidades/`

#### **CU8: Gestión de gastos del condominio (app: economia)**
- Registrar egresos, pagos a proveedores
- **Endpoints**: `GET/POST/PUT/DELETE /api/economia/gastos/`

#### **CU9: Gestión de multas y sanciones (app: economia)**
- Definir, aplicar y notificar multas por infracciones
- **Endpoints**: `GET/POST/PUT/DELETE /api/economia/multas/`

#### **CU10: Gestión y reserva de áreas comunes (app: mantenimiento)**
- Consultar disponibilidad, reservar áreas comunes
- **Endpoints**: 
  - `GET/POST/PUT/DELETE /api/mantenimiento/areas-comunes/`
  - `GET/POST/PUT/DELETE /api/mantenimiento/reservas/`
  - `GET /api/mantenimiento/reservas/disponibilidad/` - Verificar disponibilidad

#### **CU11: Agenda de eventos (app: comunidad)**
- Publicar o consultar eventos comunitarios
- **Endpoints**: `GET/POST/PUT/DELETE /api/comunidad/eventos/`

#### **CU12: Comunicados y noticias (app: comunidad)**
- Publicar y consultar avisos generales y noticias
- **Endpoints**: 
  - `GET/POST/PUT/DELETE /api/comunidad/notificaciones/`
  - `GET/POST/PUT/DELETE /api/comunidad/notificaciones-residente/`

#### **CU13: Gestión de empleados (app: usuarios)**
- Registrar, actualizar y eliminar empleados
- **Endpoints**: `GET/POST/PUT/DELETE /api/usuarios/empleados/`

#### **CU17: Asambleas vecinales (app: comunidad)**
- Publicar convocatorias, registrar actas
- **Endpoints**: `GET/POST/PUT/DELETE /api/comunidad/actas/`

#### **CU18: Gestión de ingresos (app: finanzas)**
- Reportar ingresos por alquiler de áreas, cuotas
- **Endpoints**: 
  - `GET/POST/PUT/DELETE /api/finanzas/expensas/`
  - `GET/POST/PUT/DELETE /api/finanzas/pagos/`

#### **CU19: Reportes y analítica (app: economia)**
- Generar reportes financieros, estadísticas
- **Endpoints**: 
  - `GET /api/economia/reportes/resumen_financiero/`
  - `GET /api/economia/morosidad/tendencias_pagos/`

#### **CU20: Analítica predictiva de morosidad (app: economia)**
- Predice morosidad utilizando historial de pagos
- **Endpoints**: `GET /api/economia/morosidad/predecir_morosidad/`

## Control de Acceso por Roles

### **Administrador**
- Acceso completo a todas las funcionalidades
- Puede crear, editar, eliminar cualquier registro
- Acceso a reportes y analítica

### **Residente**
- Solo puede ver sus propios datos (pagos, reservas, notificaciones, reclamos)
- Puede crear reservas de áreas comunes
- Puede crear reclamos
- Acceso de solo lectura a eventos y notificaciones generales

### **Empleado**
- Acceso limitado según su cargo específico
- Puede ver información relacionada con sus funciones

## Autenticación

### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
    "username": "usuario",
    "password": "contraseña"
}
```

**Respuesta:**
```json
{
    "token": "token_de_autenticacion",
    "username": "usuario",
    "email": "usuario@email.com",
    "rol": "Administrador",
    "user_id": 1
}
```

### Logout
```bash
POST /api/auth/logout/
Authorization: Token token_de_autenticacion
```

## Uso de la API

### Headers Requeridos
Para todas las peticiones autenticadas:
```
Authorization: Token tu_token_aqui
Content-Type: application/json
```

### Ejemplos de Uso

#### 1. Crear una Reserva (Residente)
```bash
POST /api/mantenimiento/reservas/
Authorization: Token tu_token
Content-Type: application/json

{
    "fecha": "2024-02-15",
    "hora_inicio": "10:00:00",
    "hora_fin": "12:00:00",
    "area": 1,
    "motivo": "Cumpleaños familiar",
    "costo": 50.00
}
```

#### 2. Verificar Disponibilidad
```bash
GET /api/mantenimiento/reservas/disponibilidad/?area_id=1&fecha=2024-02-15&hora_inicio=10:00:00&hora_fin=12:00:00
Authorization: Token tu_token
```

#### 3. Crear un Reclamo (Residente)
```bash
POST /api/usuarios/reclamos/
Authorization: Token tu_token
Content-Type: application/json

{
    "titulo": "Ruido excesivo",
    "descripcion": "Los vecinos del piso superior hacen mucho ruido en las noches",
    "fecha": "2024-01-15T10:00:00Z"
}
```

#### 4. Ver Reporte Financiero (Administrador)
```bash
GET /api/economia/reportes/resumen_financiero/
Authorization: Token tu_token
```

#### 5. Ver Morosidad (Administrador)
```bash
GET /api/economia/morosidad/predecir_morosidad/
Authorization: Token tu_token
```

## Datos de Prueba

Para crear datos de prueba, ejecuta:
```bash
python manage.py crear_datos_prueba
```

Esto creará:
- Usuarios de prueba (admin, residente1, residente2, residente3)
- Unidades habitacionales
- Áreas comunes
- Eventos
- Notificaciones
- Expensas y gastos

**Usuarios de prueba:**
- **admin**: jael (Administrador)
- **residente1**: residente1 (Residente)
- **residente2**: residente2 (Residente)  
- **residente3**: residente3 (Residente)
- **Contraseña para todos**: password123

## Mejoras Implementadas

### 1. **Control de Acceso Mejorado**
- Filtrado automático de datos según el rol del usuario
- Residentes solo ven sus propios datos
- Administradores tienen acceso completo

### 2. **Validaciones de Negocio**
- Verificación de disponibilidad para reservas
- Asignación automática de residentes en reclamos y reservas
- Estados y opciones predefinidas para mejor consistencia

### 3. **Analítica Avanzada**
- Reportes financieros detallados
- Análisis de morosidad por residente
- Tendencias de pagos por mes

### 4. **Relaciones Mejoradas**
- Mejor integración entre modelos
- Historial de residentes en unidades
- Estados de pagos y reservas más detallados

## Endpoints por App

### Autenticación (`/api/auth/`)
- `POST /login/` - Iniciar sesión
- `POST /logout/` - Cerrar sesión

### Usuarios (`/api/usuarios/`)
- `usuarios/` - Gestión de usuarios
- `personas/` - Gestión de personas
- `roles/` - Gestión de roles
- `permisos/` - Gestión de permisos
- `rol-permisos/` - Asignación de permisos a roles
- `empleados/` - Gestión de empleados
- `vehiculos/` - Gestión de vehículos
- `visitas/` - Gestión de visitas
- `reclamos/` - Gestión de reclamos

### Comunidad (`/api/comunidad/`)
- `unidades/` - Gestión de unidades
- `residentes-unidad/` - Asociación residentes-unidades
- `eventos/` - Gestión de eventos
- `notificaciones/` - Gestión de notificaciones
- `notificaciones-residente/` - Notificaciones por residente
- `actas/` - Gestión de actas

### Finanzas (`/api/finanzas/`)
- `expensas/` - Gestión de expensas
- `pagos/` - Gestión de pagos

### Economía (`/api/economia/`)
- `gastos/` - Gestión de gastos
- `multas/` - Gestión de multas
- `reportes/resumen_financiero/` - Reporte financiero
- `morosidad/predecir_morosidad/` - Análisis de morosidad
- `morosidad/tendencias_pagos/` - Tendencias de pagos

### Mantenimiento (`/api/mantenimiento/`)
- `areas-comunes/` - Gestión de áreas comunes
- `reservas/` - Gestión de reservas
- `reservas/disponibilidad/` - Verificar disponibilidad
- `mantenimientos/` - Gestión de mantenimientos
- `bitacoras-mantenimiento/` - Bitácoras de mantenimiento
- `reglamentos/` - Gestión de reglamentos

## Notas Importantes

1. **Base de Datos**: No modificar la estructura de la base de datos, ya está optimizada según el ERD proporcionado.

2. **Permisos**: El sistema implementa control de acceso granular basado en roles.

3. **Validaciones**: Se han agregado validaciones de negocio para mejorar la integridad de los datos.

4. **Escalabilidad**: La arquitectura permite fácil extensión de funcionalidades.

5. **Seguridad**: Todos los endpoints requieren autenticación excepto login.
