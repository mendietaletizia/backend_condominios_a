#!/usr/bin/env python3
"""
Script de optimización de base de datos para el proyecto Condominio
Incluye optimizaciones de índices, consultas y configuración
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_condominio_a.settings_optimized')

django.setup()

from django.db import connection
from django.core.management import call_command
from django.db.models import Count, Avg, Max, Min
import logging

logger = logging.getLogger(__name__)

def analyze_database():
    """Analizar el estado actual de la base de datos"""
    print("🔍 ANALIZANDO BASE DE DATOS...")

    with connection.cursor() as cursor:
        # Obtener información de tablas
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)

        tables = cursor.fetchall()
        print("\n📊 TABLAS Y TAMAÑOS:")
        for table in tables:
            print(f"  {table[1]}: {table[2]}")

        # Obtener estadísticas de índices
        cursor.execute("""
            SELECT
                t.relname AS table_name,
                i.relname AS index_name,
                pg_size_pretty(pg_relation_size(i.oid)) AS index_size
            FROM pg_class t
            JOIN pg_index idx ON t.oid = idx.indrelid
            JOIN pg_class i ON i.oid = idx.indexrelid
            WHERE t.relkind = 'r' AND t.relname IN (
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            )
            ORDER BY pg_relation_size(i.oid) DESC;
        """)

        indexes = cursor.fetchall()
        print("\n📈 ÍNDICES:")
        for index in indexes[:10]:  # Mostrar solo los 10 más grandes
            print(f"  {index[0]}.{index[1]}: {index[2]}")

def create_optimized_indexes():
    """Crear índices optimizados para consultas comunes"""
    print("\n🔧 CREANDO ÍNDICES OPTIMIZADOS...")

    with connection.cursor() as cursor:
        # Índices para usuarios
        indexes = [
            # Índices para consultas de usuarios
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios_usuario (username)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios_usuario (email)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios_usuario (rol_id)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_is_active ON usuarios_usuario (is_active)",

            # Índices para personas
            "CREATE INDEX IF NOT EXISTS idx_personas_documento ON usuarios_persona (documento)",
            "CREATE INDEX IF NOT EXISTS idx_personas_telefono ON usuarios_persona (telefono)",
            "CREATE INDEX IF NOT EXISTS idx_personas_email ON usuarios_persona (email)",

            # Índices para residentes
            "CREATE INDEX IF NOT EXISTS idx_residentes_usuario ON usuarios_residentes (usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_residentes_unidad ON usuarios_residentes (unidad_id)",

            # Índices para empleados
            "CREATE INDEX IF NOT EXISTS idx_empleados_usuario ON usuarios_empleado (usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_empleados_cargo ON usuarios_empleado (cargo)",

            # Índices para finanzas
            "CREATE INDEX IF NOT EXISTS idx_pagos_residente ON finanzas_pago (residente_id)",
            "CREATE INDEX IF NOT EXISTS idx_pagos_fecha ON finanzas_pago (fecha_pago)",
            "CREATE INDEX IF NOT EXISTS idx_pagos_estado ON finanzas_pago (estado_pago)",
            "CREATE INDEX IF NOT EXISTS idx_pagos_monto ON finanzas_pago (monto)",

            # Índices para economía
            "CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON economia_gastos (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_gastos_monto ON economia_gastos (monto)",
            "CREATE INDEX IF NOT EXISTS idx_multas_residente ON economia_multa (residente_id)",
            "CREATE INDEX IF NOT EXISTS idx_multas_pagada ON economia_multa (pagada)",

            # Índices para comunidad
            "CREATE INDEX IF NOT EXISTS idx_eventos_fecha ON comunidad_evento (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON comunidad_evento (tipo)",
            "CREATE INDEX IF NOT EXISTS idx_unidades_numero ON comunidad_unidad (numero)",
            "CREATE INDEX IF NOT EXISTS idx_unidades_torre ON comunidad_unidad (torre)",

            # Índices compuestos para consultas comunes
            "CREATE INDEX IF NOT EXISTS idx_usuarios_persona_rol ON usuarios_usuario (persona_id, rol_id)",
            "CREATE INDEX IF NOT EXISTS idx_pagos_residente_fecha ON finanzas_pago (residente_id, fecha_pago)",
            "CREATE INDEX IF NOT EXISTS idx_gastos_fecha_monto ON economia_gastos (fecha, monto)",
        ]

        created_count = 0
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                created_count += 1
                print(f"  ✅ Índice creado")
            except Exception as e:
                print(f"  ⚠️  Error creando índice: {e}")

        print(f"\n✅ {created_count} índices creados o verificados")

def optimize_table_settings():
    """Optimizar configuración de tablas"""
    print("\n⚙️  OPTIMIZANDO CONFIGURACIÓN DE TABLAS...")

    with connection.cursor() as cursor:
        # Configurar fillfactor para tablas con muchas actualizaciones
        tables_to_optimize = [
            'usuarios_usuario',
            'finanzas_pago',
            'economia_gastos',
            'economia_multa',
        ]

        for table in tables_to_optimize:
            try:
                cursor.execute(f"ALTER TABLE {table} SET (fillfactor = 85);")
                print(f"  ✅ Configurado fillfactor para {table}")
            except Exception as e:
                print(f"  ⚠️  Error configurando {table}: {e}")

def run_vacuum_analyze():
    """Ejecutar VACUUM y ANALYZE"""
    print("\n🧹 EJECUTANDO VACUUM Y ANALYZE...")

    with connection.cursor() as cursor:
        try:
            # VACUUM ANALYZE para todas las tablas
            cursor.execute("VACUUM ANALYZE;")
            print("  ✅ VACUUM ANALYZE completado")
        except Exception as e:
            print(f"  ⚠️  Error en VACUUM ANALYZE: {e}")

def generate_query_optimizations():
    """Generar recomendaciones de optimización de consultas"""
    print("\n📋 GENERANDO RECOMENDACIONES DE OPTIMIZACIÓN...")

    recommendations = [
        "1. Usar select_related() para relaciones ForeignKey:",
        "   - Usuario.objects.select_related('persona', 'rol')",
        "   - Pago.objects.select_related('residente__persona')",
        "",
        "2. Usar prefetch_related() para relaciones ManyToMany:",
        "   - Usuario.objects.prefetch_related('groups', 'user_permissions')",
        "   - Rol.objects.prefetch_related('rolpermiso_set__permiso')",
        "",
        "3. Usar annotate() para cálculos agregados:",
        "   - Pago.objects.annotate(total=Sum('monto'))",
        "   - Usuario.objects.annotate(pago_count=Count('pago'))",
        "",
        "4. Evitar N+1 queries usando select_related y prefetch_related",
        "5. Usar pagination para listas grandes",
        "6. Cachear resultados de consultas frecuentes",
        "7. Usar índices compuestos para consultas con múltiples filtros",
    ]

    for rec in recommendations:
        print(f"  {rec}")

def create_performance_monitoring():
    """Crear sistema de monitoreo de performance"""
    print("\n📊 CREANDO SISTEMA DE MONITOREO...")

    monitoring_sql = """
    -- Vista para monitoreo de consultas lentas
    CREATE OR REPLACE VIEW performance_slow_queries AS
    SELECT
        schemaname,
        tablename,
        seq_scan,
        seq_tup_read,
        idx_scan,
        idx_tup_fetch,
        n_tup_ins,
        n_tup_upd,
        n_tup_del,
        n_live_tup,
        n_dead_tup
    FROM pg_stat_user_tables
    WHERE seq_scan > 100 OR idx_scan < seq_scan;

    -- Vista para monitoreo de índices no utilizados
    CREATE OR REPLACE VIEW performance_unused_indexes AS
    SELECT
        schemaname,
        tablename,
        indexname,
        idx_scan,
        pg_size_pretty(pg_relation_size(indexrelid)) as size
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
    ORDER BY pg_relation_size(indexrelid) DESC;
    """

    with connection.cursor() as cursor:
        try:
            cursor.execute(monitoring_sql)
            print("  ✅ Vistas de monitoreo creadas")
        except Exception as e:
            print(f"  ⚠️  Error creando vistas: {e}")

def main():
    """Función principal del script de optimización"""
    print("🚀 INICIANDO OPTIMIZACIÓN DE BASE DE DATOS")
    print("=" * 50)

    try:
        # Analizar estado actual
        analyze_database()

        # Crear índices optimizados
        create_optimized_indexes()

        # Optimizar configuración de tablas
        optimize_table_settings()

        # Ejecutar mantenimiento
        run_vacuum_analyze()

        # Generar recomendaciones
        generate_query_optimizations()

        # Crear sistema de monitoreo
        create_performance_monitoring()

        print("\n" + "=" * 50)
        print("✅ OPTIMIZACIÓN COMPLETADA")
        print("\n📈 PRÓXIMOS PASOS RECOMENDADOS:")
        print("  1. Revisar las consultas en el código para usar select_related/prefetch_related")
        print("  2. Implementar caché para consultas frecuentes")
        print("  3. Configurar monitoreo de performance en producción")
        print("  4. Revisar las vistas de monitoreo creadas regularmente")

    except Exception as e:
        logger.error(f"Error durante la optimización: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
