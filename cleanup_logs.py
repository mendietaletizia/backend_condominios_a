#!/usr/bin/env python3
"""
Script para limpieza y rotación de logs del proyecto Condominio
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

def setup_logging():
    """Configurar logging para el script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/cleanup.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def clean_old_logs(log_dir, days_to_keep=30):
    """
    Limpiar logs antiguos

    Args:
        log_dir: Directorio de logs
        days_to_keep: Días para mantener logs
    """
    logger = logging.getLogger(__name__)
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    if not log_dir.exists():
        logger.warning(f"Directorio de logs no existe: {log_dir}")
        return 0

    cleaned_count = 0
    total_size_freed = 0

    logger.info(f"Limpiando logs antiguos en {log_dir} (manteniendo {days_to_keep} días)")

    for log_file in log_dir.glob("*.log*"):
        try:
            # Obtener fecha de modificación
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)

            if mod_time < cutoff_date:
                # Obtener tamaño antes de eliminar
                file_size = log_file.stat().st_size
                total_size_freed += file_size

                # Eliminar archivo
                log_file.unlink()
                logger.info(f"Eliminado: {log_file.name} (tamaño: {file_size / 1024:.1f} KB)")
                cleaned_count += 1

        except Exception as e:
            logger.error(f"Error procesando {log_file.name}: {e}")

    logger.info(f"Limpieza completada: {cleaned_count} archivos eliminados, {total_size_freed / 1024 / 1024:.2f} MB liberados")
    return cleaned_count, total_size_freed

def compress_old_logs(log_dir, days_to_compress=7):
    """
    Comprimir logs antiguos

    Args:
        log_dir: Directorio de logs
        days_to_compress: Días después de los cuales comprimir
    """
    logger = logging.getLogger(__name__)
    cutoff_date = datetime.now() - timedelta(days=days_to_compress)

    try:
        import gzip

        compressed_count = 0
        total_size_before = 0
        total_size_after = 0

        logger.info(f"Comprimiendo logs en {log_dir} (logs de más de {days_to_compress} días)")

        for log_file in log_dir.glob("*.log"):
            try:
                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)

                if mod_time < cutoff_date:
                    # Comprimir archivo
                    original_size = log_file.stat().st_size
                    total_size_before += original_size

                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)

                    # Eliminar archivo original
                    log_file.unlink()
                    compressed_size = Path(f"{log_file}.gz").stat().st_size
                    total_size_after += compressed_size

                    logger.info(f"Comprimido: {log_file.name} -> {log_file.name}.gz "
                              f"({original_size / 1024:.1f} KB -> {compressed_size / 1024:.1f} KB)")
                    compressed_count += 1

            except ImportError:
                logger.warning("gzip no disponible, omitiendo compresión")
                break
            except Exception as e:
                logger.error(f"Error comprimiendo {log_file.name}: {e}")

        if compressed_count > 0:
            compression_ratio = (1 - total_size_after / total_size_before) * 100
            logger.info(f"Compresión completada: {compressed_count} archivos, "
                       f"ratio de compresión: {compression_ratio:.1f}%")

        return compressed_count, total_size_before, total_size_after

    except ImportError:
        logger.warning("Módulo gzip no disponible, omitiendo compresión")
        return 0, 0, 0

def rotate_current_logs(log_dir, max_size_mb=100):
    """
    Rotar logs actuales si son demasiado grandes

    Args:
        log_dir: Directorio de logs
        max_size_mb: Tamaño máximo en MB antes de rotar
    """
    logger = logging.getLogger(__name__)
    max_size_bytes = max_size_mb * 1024 * 1024

    rotated_count = 0

    logger.info(f"Verificando rotación de logs (máximo {max_size_mb} MB)")

    for log_file in log_dir.glob("*.log"):
        try:
            if log_file.stat().st_size > max_size_bytes:
                # Crear archivo de rotación
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_file = log_file.with_name(f"{log_file.stem}_{timestamp}{log_file.suffix}")

                # Renombrar archivo actual
                log_file.rename(rotated_file)

                logger.info(f"Rotado: {log_file.name} -> {rotated_file.name}")
                rotated_count += 1

        except Exception as e:
            logger.error(f"Error rotando {log_file.name}: {e}")

    logger.info(f"Rotación completada: {rotated_count} archivos rotados")
    return rotated_count

def generate_log_report(log_dir):
    """Generar reporte de logs"""
    logger = logging.getLogger(__name__)

    if not log_dir.exists():
        logger.warning(f"Directorio de logs no existe: {log_dir}")
        return

    logger.info("Generando reporte de logs...")

    total_files = 0
    total_size = 0
    files_by_type = {}

    for log_file in log_dir.glob("*"):
        if log_file.is_file():
            total_files += 1
            file_size = log_file.stat().st_size
            total_size += file_size

            # Categorizar por extensión
            ext = log_file.suffix.lower()
            if ext not in files_by_type:
                files_by_type[ext] = {'count': 0, 'size': 0}
            files_by_type[ext]['count'] += 1
            files_by_type[ext]['size'] += file_size

    # Mostrar reporte
    print("\n" + "="*50)
    print("📊 REPORTE DE LOGS")
    print("="*50)
    print(f"📁 Total de archivos: {total_files}")
    print(f"💾 Tamaño total: {total_size / 1024 / 1024:.2f} MB")

    print("\n📋 Por tipo de archivo:")
    for ext, info in sorted(files_by_type.items()):
        print(f"  {ext or 'sin extensión'}: {info['count']} archivos, {info['size'] / 1024 / 1024:.2f} MB")

    # Archivos más grandes
    print("\n📈 Archivos más grandes:")
    large_files = sorted(log_dir.glob("*"), key=lambda x: x.stat().st_size, reverse=True)[:5]
    for i, file in enumerate(large_files, 1):
        size_mb = file.stat().st_size / 1024 / 1024
        print(f"  {i}. {file.name}: {size_mb:.2f} MB")

def main():
    """Función principal del script de limpieza"""
    logger = setup_logging()

    print("🧹 INICIANDO LIMPIEZA DE LOGS")
    print("=" * 50)

    # Directorio de logs
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(exist_ok=True)
        logger.info(f"Directorio de logs creado: {log_dir}")

    try:
        # 1. Generar reporte inicial
        generate_log_report(log_dir)

        # 2. Limpiar logs antiguos
        cleaned_count, size_freed = clean_old_logs(log_dir, days_to_keep=30)

        # 3. Comprimir logs antiguos
        compressed_count, size_before, size_after = compress_old_logs(log_dir, days_to_compress=7)

        # 4. Rotar logs grandes
        rotated_count = rotate_current_logs(log_dir, max_size_mb=100)

        # 5. Generar reporte final
        print("\n" + "=" * 50)
        print("✅ LIMPIEZA COMPLETADA")
        print("=" * 50)

        print("📋 RESUMEN:")
        print(f"  🗑️  Archivos eliminados: {cleaned_count}")
        print(f"  📦 Archivos comprimidos: {compressed_count}")
        print(f"  🔄 Archivos rotados: {rotated_count}")

        if size_freed > 0:
            print(f"  💾 Espacio liberado: {size_freed / 1024 / 1024:.2f} MB")

        if compressed_count > 0:
            compression_ratio = (1 - size_after / size_before) * 100 if size_before > 0 else 0
            print(f"  🗜️  Ratio de compresión: {compression_ratio:.1f}%")

        generate_log_report(log_dir)

        print("\n📅 Próxima limpieza recomendada: En 7 días")
        print("💡 Tip: Configura este script en un cron job para ejecución automática")

        return 0

    except Exception as e:
        logger.error(f"Error durante la limpieza: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
