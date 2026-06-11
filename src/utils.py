"""
Utilidades para Downloads Organizer
Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
"""
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configura el sistema de logging
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo de log opcional

    Returns:
        Logger configurado
    """
    logger = logging.getLogger("DownloadsOrganizer")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_file_size_str(size_bytes: int) -> str:
    """
    Convierte bytes a representación legible
    Args:
        size_bytes: Tamaño en bytes

    Returns:
        String con formato legible (KB, MB, GB)
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_info(file_path: Path) -> dict:
    """
    Obtiene información detallada de un archivo
    Args:
        file_path: Ruta del archivo

    Returns:
        Diccionario con información del archivo
    """
    if not file_path.exists():
        return {}

    stat = file_path.stat()

    return {
        "name": file_path.name,
        "path": str(file_path),
        "size": stat.st_size,
        "size_str": get_file_size_str(stat.st_size),
        "extension": file_path.suffix,
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "is_hidden": file_path.name.startswith('.')
    }


def safe_move(src: Path, dst: Path, overwrite: bool = False) -> Tuple[bool, str]:
    """
    Mueve un archivo de forma segura manejando conflictos
    Args:
        src: Ruta origen
        dst: Ruta destino
        overwrite: Si debe sobrescribir archivos existentes

    Returns:
        (éxito, mensaje)
    """
    try:
        if not src.exists():
            return False, f"Origen no existe: {src}"
        
        # Crear directorio destino si no existe
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Manejar archivos existentes
        if dst.exists():
            if overwrite:
                dst.unlink()
            else:
                # Generar nombre único
                counter = 1
                stem = dst.stem
                suffix = dst.suffix
                while dst.exists():
                    dst = dst.parent / f"{stem}_{counter}{suffix}"
                    counter += 1
        
        # Mover archivo
        src.rename(dst)
        return True, f"Movido: {src.name} -> {dst.parent.name}"

    except Exception as e:
        return False, f"Error: {str(e)}"


def clean_old_files(directory: Path, days_old: int, dry_run: bool = False) -> List[Path]:
    """
    Limpia archivos antiguos en un directorio
    Args:
        directory: Directorio a limpiar
        days_old: Días de antigüedad
        dry_run: Si es True, solo lista sin eliminar

    Returns:
        Lista de archivos eliminados
    """
    if not directory.exists():
        return []

    cutoff = datetime.now().timestamp() - (days_old * 24 * 3600)
    deleted_files = []

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff:
                if not dry_run:
                    file_path.unlink()
                deleted_files.append(file_path)

    return deleted_files


def create_backup(file_path: Path, backup_dir: Path) -> Optional[Path]:
    """
    Crea una copia de seguridad de un archivo
    Args:
        file_path: Archivo a respaldar
        backup_dir: Directorio de respaldo

    Returns:
        Ruta del backup o None si falló
    """
    if not file_path.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


def validate_directory(path: str, create: bool = False) -> Tuple[bool, str]:
    """
    Valida si un directorio existe y es accesible
    Args:
        path: Ruta del directorio
        create: Si debe crear el directorio si no existe

    Returns:
        (es_válido, mensaje)
    """
    dir_path = Path(path)

    if not dir_path.exists():
        if create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                return True, f"Directorio creado: {path}"
            except Exception as e:
                return False, f"No se pudo crear: {e}"
        else:
            return False, f"Directorio no existe: {path}"

    if not dir_path.is_dir():
        return False, f"No es un directorio: {path}"

    if not os.access(path, os.R_OK):
        return False, f"No hay permisos de lectura: {path}"

    return True, "OK"