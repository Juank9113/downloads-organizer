#!/usr/bin/env python3
"""
organizer.py - Núcleo del Downloads Organizer Pro.

Características:
- Organización automática basada en configuración JSON.
- Modo simulación (--simulate).
- Modo estadísticas (--stats).
- Modo interactivo (--interactive) para archivos ambiguos.
- Integración con sistema Undo/Redo (--undo / --redo).
- Registro automático de movimientos en el historial.

Autor: Juan Carlos Blanco Ruiz
"""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Asegurar que podemos importar módulos hermanos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from undo_manager import UndoManager
except ImportError:
    print("⚠️ No se pudo importar undo_manager.py. Asegúrate de que esté en la misma carpeta.")
    sys.exit(1)

try:
    from interactive_mode import InteractiveMode, process_interactive_files
except ImportError:
    print("️ No se pudo importar interactive_mode.py. Asegúrate de que esté en la misma carpeta.")
    InteractiveMode = None
    process_interactive_files = None

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuración por defecto si no se proporciona un archivo
DEFAULT_CONFIG = {
    "downloads_dir": str(Path.home() / "Downloads"),
    "organized_dir": str(Path.home() / "Downloads_Organized"),
    "categories": {
        "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
        "Documentos": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
        "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Codigo": [".py", ".js", ".html", ".css", ".json", ".xml", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go", ".rs"],
        "Ejecutables": [".exe", ".msi", ".deb", ".rpm", ".app", ".dmg", ".sh", ".bat"]
    }
}


def load_config(config_path: str = None) -> dict:
    """Carga la configuración desde un archivo JSON o usa la predeterminada."""
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG


def get_category(filename: str, categories: dict) -> str:
    """Determina la categoría de un archivo basado en su extensión."""
    ext = Path(filename).suffix.lower()
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return "Otros"


def organize_files(config: dict, simulate: bool = False, interactive: bool = False):
    """Función principal para organizar los archivos."""
    downloads_dir = Path(config["downloads_dir"])
    organized_dir = Path(config["organized_dir"])
    categories = config.get("categories", {})

    if not downloads_dir.exists():
        logger.error(f"La carpeta de origen no existe: {downloads_dir}")
        return

    # Crear carpeta de destino si no existe (y no estamos en simulación)
    if not simulate:
        organized_dir.mkdir(parents=True, exist_ok=True)

    # Inicializar el gestor de Undo
    undo_mgr = UndoManager()
    
    # Inicializar modo interactivo si está activado
    interactive_mode = None
    if interactive and InteractiveMode:
        interactive_mode = InteractiveMode()
        logger.info(" MODO INTERACTIVO ACTIVADO - Se preguntará por archivos ambiguos")

    files_moved = 0
    files_skipped = 0
    files_interactive = 0
    stats = {}

    logger.info(f"🔍 Analizando carpeta: {downloads_dir}")
    if simulate:
        logger.info("🧪 MODO SIMULACIÓN ACTIVADO - No se moverán archivos reales")

    # Recopilar archivos con extensiones no reconocidas para modo interactivo
    ambiguous_files = []
    normal_files = []

    for item in downloads_dir.iterdir():
        if item.is_file():
            category = get_category(item.name, categories)
            if category == "Otros" and interactive_mode:
                ambiguous_files.append(item)
            else:
                normal_files.append((item, category))

    # Procesar modo interactivo primero si hay archivos ambiguos
    if ambiguous_files and interactive_mode:
        logger.info(f"\n📋 Se encontraron {len(ambiguous_files)} archivos con extensiones no reconocidas")
        
        results = process_interactive_files(
            ambiguous_files,
            categories,
            mode='cli',
            decisions_file=Path.home() / ".downloads_organizer_decisions.json"
        )
        
        # Procesar resultados del modo interactivo
        for file_path_str, action in results.items():
            file_path = Path(file_path_str)
            
            if action == 'skip' or action == 'keep':
                logger.info(f"  ⏭️ {file_path.name} - Mantenido en Downloads")
                files_skipped += 1
                continue
            
            # Si es una nueva categoría, añadirla a las categorías
            if action not in categories:
                categories[action] = []
                logger.info(f"  ✨ Nueva categoría creada: {action}")
            
            dest_folder = organized_dir / action
            dest_file = dest_folder / file_path.name
            
            if simulate:
                logger.info(f"  [SIMULACIÓN] {file_path.name} -> {action}/{file_path.name}")
                files_moved += 1
            else:
                dest_folder.mkdir(parents=True, exist_ok=True)
                
                if dest_file.exists():
                    stem = dest_file.stem
                    suffix = dest_file.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = dest_folder / f"{stem}_{counter}{suffix}"
                        counter += 1
                    logger.warning(f"  ⚠️ Nombre en conflicto. Renombrado a: {dest_file.name}")
                
                try:
                    shutil.move(str(file_path), str(dest_file))
                    undo_mgr.record_action('move', str(file_path), str(dest_file))
                    logger.info(f"  ✅ Movido: {file_path.name} -> {action}/{dest_file.name}")
                    files_moved += 1
                    stats[action] = stats.get(action, 0) + 1
                except Exception as e:
                    logger.error(f"  ❌ Error al mover {file_path.name}: {e}")
                    files_skipped += 1
        
        files_interactive = len(ambiguous_files)

    # Procesar archivos normales (conocidos)
    for item, category in normal_files:
        stats[category] = stats.get(category, 0) + 1
        
        dest_folder = organized_dir / category
        dest_file = dest_folder / item.name

        if item.resolve() == dest_file.resolve():
            continue

        if simulate:
            logger.info(f"  [SIMULACIÓN] {item.name} -> {category}/{item.name}")
            files_moved += 1
        else:
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            if dest_file.exists():
                stem = dest_file.stem
                suffix = dest_file.suffix
                counter = 1
                while dest_file.exists():
                    dest_file = dest_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
                logger.warning(f"  ⚠️ Nombre en conflicto. Renombrado a: {dest_file.name}")

            try:
                shutil.move(str(item), str(dest_file))
                undo_mgr.record_action('move', str(item), str(dest_file))
                logger.info(f"  ✅ Movido: {item.name} -> {category}/{dest_file.name}")
                files_moved += 1
            except Exception as e:
                logger.error(f"  ❌ Error al mover {item.name}: {e}")
                files_skipped += 1

    # Resumen
    logger.info("="*50)
    logger.info(f"📊 RESUMEN:")
    logger.info(f"   Archivos procesados: {files_moved + files_skipped + files_interactive}")
    logger.info(f"   Movidos exitosamente: {files_moved}")
    logger.info(f"   Omitidos/Error: {files_skipped}")
    if interactive:
        logger.info(f"   Archivos interactivos: {files_interactive}")
    
    if stats:
        dist_parts = [f"Archivos {categoria} -> {cantidad}" for categoria, cantidad in stats.items()]
        dist_text = ", ".join(dist_parts)
        logger.info(f"   Distribución: {dist_text}")
        
    logger.info("="*50)


def show_stats(config: dict):
    """Muestra estadísticas básicas de las carpetas."""
    downloads_dir = Path(config["downloads_dir"])
    organized_dir = Path(config["organized_dir"])

    print(f"\n📊 ESTADÍSTICAS DEL SISTEMA")
    print(f"{'='*40}")
    
    if downloads_dir.exists():
        files = list(downloads_dir.iterdir())
        size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"📂 Carpeta Origen ({downloads_dir.name}):")
        print(f"   - Archivos: {len(files)}")
        print(f"   - Tamaño total: {size / (1024*1024):.2f} MB")
    else:
        print(f"⚠️ Carpeta Origen no encontrada.")

    if organized_dir.exists():
        categories = [d for d in organized_dir.iterdir() if d.is_dir()]
        total_files = 0
        total_size = 0
        for cat in categories:
            cat_files = list(cat.rglob('*'))
            total_files += len([f for f in cat_files if f.is_file()])
            total_size += sum(f.stat().st_size for f in cat_files if f.is_file())
            
        print(f"\n📂 Carpeta Organizada ({organized_dir.name}):")
        print(f"   - Categorías creadas: {len(categories)}")
        print(f"   - Archivos totales: {total_files}")
        print(f"   - Tamaño total: {total_size / (1024*1024):.2f} MB")
        
        print(f"\n   Detalle por categoría:")
        for cat in sorted(categories):
            cat_files = [f for f in cat.rglob('*') if f.is_file()]
            cat_size = sum(f.stat().st_size for f in cat_files)
            print(f"   - {cat.name}: {len(cat_files)} archivos ({cat_size / (1024*1024):.2f} MB)")
    else:
        print(f"\n⚠️ Carpeta Organizada aún no existe.")
    print(f"{'='*40}\n")


def main():
    parser = argparse.ArgumentParser(description="Downloads Organizer Pro - CLI")
    parser.add_argument("--config", "-c", type=str, help="Ruta al archivo de configuración JSON")
    parser.add_argument("--simulate", "-s", action="store_true", help="Ejecutar en modo simulación")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas de uso")
    parser.add_argument("--undo", action="store_true", help="Deshacer la última operación de organización")
    parser.add_argument("--redo", action="store_true", help="Rehacer la última operación deshecha")
    parser.add_argument("--interactive", "-i", action="store_true", help="Activar modo interactivo para archivos ambiguos")
    
    args = parser.parse_args()

    # Cargar configuración
    config = load_config(args.config)

    # Manejo de Undo/Redo
    if args.undo:
        undo_mgr = UndoManager()
        success, msg = undo_mgr.undo()
        print(f"{'✅' if success else ''} {msg}")
        return

    if args.redo:
        undo_mgr = UndoManager()
        success, msg = undo_mgr.redo()
        print(f"{'✅' if success else '❌'} {msg}")
        return

    # Mostrar estadísticas
    if args.stats:
        show_stats(config)
        return

    # Ejecutar organización normal o interactiva
    organize_files(config, simulate=args.simulate, interactive=args.interactive)


if __name__ == "__main__":
    main()