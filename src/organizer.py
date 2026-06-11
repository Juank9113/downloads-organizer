#!/usr/bin/env python3
"""
Organizador Automático de Descargas
Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
Mueve archivos de ~/Downloads a carpetas según su tipo
"""
import os
import shutil
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuración por defecto
DEFAULT_CONFIG = {
    "downloads_dir": str(Path.home() / "Downloads"),
    "organized_dir": str(Path.home() / "Downloads_Organized"),
    "categories": {
        "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
        "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".odt", ".rtf", ".md"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        "Musica": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "Archivos_Comprimidos": [".zip", ".rar", ".tar", ".gz", ".7z", ".bz2", ".xz"],
        "Programas": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage", ".sh"],
        "Codigo": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json", ".xml", ".yaml", ".yml"],
        "Otros": []
    },
    "exclude_extensions": [".tmp", ".temp", ".crdownload", ".part"],
    "log_level": "INFO",
    "notifications": False
}


class DownloadsOrganizer:
    """Clase principal para organizar archivos de descargas"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa el organizador con la configuración especificada"""
        self.config = self._load_config(config_path)
        # USAR expanduser() PARA EXPANDIR EL ~ A LA RUTA DEL HOME
        self.downloads_dir = Path(self.config["downloads_dir"]).expanduser()
        self.organized_dir = Path(self.config["organized_dir"]).expanduser()
        self.categories = self.config["categories"]
        self.exclude_extensions = self.config["exclude_extensions"]
        self.stats = {"moved": 0, "errors": 0, "skipped": 0}

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carga la configuración desde un archivo JSON"""
        config = DEFAULT_CONFIG.copy()
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                print(f"✅ Configuración cargada desde {config_path}")
            except Exception as e:
                print(f"⚠️ Error cargando configuración: {e}. Usando configuración por defecto.")
        return config

    def create_category_folders(self) -> None:
        """Crea las carpetas de categorías si no existen"""
        for category in self.categories.keys():
            folder_path = self.organized_dir / category
            folder_path.mkdir(parents=True, exist_ok=True)

    def get_file_category(self, file_extension: str) -> str:
        """
        Determina la categoría según la extensión del archivo
        Args:
            file_extension: Extensión del archivo (ej: .pdf)
        Returns:
            Nombre de la categoría
        """
        file_extension = file_extension.lower()
        if file_extension in self.exclude_extensions:
            return "EXCLUDED"
        for category, extensions in self.categories.items():
            if file_extension in extensions:
                return category
        return "Otros"

    def get_unique_filename(self, target_path: Path) -> Path:
        """
        Genera un nombre único si el archivo ya existe
        Args:
            target_path: Ruta destino original
        Returns:
            Ruta con nombre único
        """
        if not target_path.exists():
            return target_path
        counter = 1
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def organize_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Organiza un archivo individual
        Args:
            file_path: Ruta del archivo a organizar
        Returns:
            (éxito, mensaje)
        """
        try:
            file_extension = file_path.suffix
            category = self.get_file_category(file_extension)
            
            if category == "EXCLUDED":
                self.stats["skipped"] += 1
                return True, f"️ {file_path.name}: Excluido"
            
            dest_folder = self.organized_dir / category
            # CREAR CARPETA SI NO EXISTE
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            dest_path = dest_folder / file_path.name
            dest_path = self.get_unique_filename(dest_path)
            
            shutil.move(str(file_path), str(dest_path))
            self.stats["moved"] += 1
            return True, f"✅ {file_path.name} → {category}/"
            
        except PermissionError:
            self.stats["errors"] += 1
            return False, f"❌ {file_path.name}: Permiso denegado"
        except Exception as e:
            self.stats["errors"] += 1
            return False, f"❌ {file_path.name}: {str(e)}"

    def organize_all(self, simulate: bool = False) -> None:
        """
        Organiza todos los archivos en la carpeta de descargas
        Args:
            simulate: Si es True, solo simula sin mover archivos
        """
        if not self.downloads_dir.exists():
            print(f"❌ La carpeta {self.downloads_dir} no existe")
            return
            
        if simulate:
            print("🔍 MODO SIMULACIÓN - No se moverán archivos realmente")
        else:
            self.create_category_folders()
            
        print(f"\n📁 Organizando archivos en {self.downloads_dir}...")
        print("=" * 60)
        
        files = [f for f in self.downloads_dir.iterdir() if f.is_file()]
        
        if not files:
            print("📭 No hay archivos para organizar")
            return
            
        for file_path in files:
            if simulate:
                extension = file_path.suffix
                category = self.get_file_category(extension)
                if category == "EXCLUDED":
                    print(f"⏭️ [SIM] {file_path.name} → Excluido")
                else:
                    print(f"🔄 [SIM] {file_path.name} → {category}/")
                self.stats["moved" if category != "EXCLUDED" else "skipped"] += 1
            else:
                success, message = self.organize_file(file_path)
                print(message)
                
        self.show_summary(simulate)

    def show_summary(self, simulate: bool = False) -> None:
        """Muestra un resumen de la operación"""
        print("=" * 60)
        if simulate:
            print("📊 RESUMEN DE SIMULACIÓN:")
        else:
            print("📊 RESUMEN:")
        print(f"   📦 Movidos: {self.stats['moved']}")
        print(f"   ️ Errores: {self.stats['errors']}")
        print(f"   ⏭️ Excluidos: {self.stats['skipped']}")
        print(f"   📁 Total procesados: {sum(self.stats.values())}")
        if not simulate:
            print(f"\n📂 Archivos organizados en: {self.organized_dir}")

    def show_stats(self) -> None:
        """Muestra estadísticas de archivos ya organizados"""
        if not self.organized_dir.exists():
            print("📊 Aún no hay archivos organizados")
            return
            
        print("\n📊 ESTADÍSTICAS DE ARCHIVOS ORGANIZADOS")
        print("=" * 60)
        total_files = 0
        category_stats = {}
        
        for category in self.categories.keys():
            folder = self.organized_dir / category
            if folder.exists():
                files = [f for f in folder.iterdir() if f.is_file()]
                count = len(files)
                category_stats[category] = count
                total_files += count
                
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                bar_length = min(30, count // 5)
                bar = "█" * bar_length
                print(f"📁 {category:<20} {count:>5} archivos {bar}")
                
        print("=" * 60)
        print(f" Total de archivos organizados: {total_files}")
        
        total_size = sum(f.stat().st_size for f in self.organized_dir.rglob("*") if f.is_file())
        if total_size > 0:
            size_gb = total_size / (1024**3)
            size_mb = total_size / (1024**2)
            if size_gb >= 1:
                print(f" Tamaño total: {size_gb:.2f} GB")
            else:
                print(f"💾 Tamaño total: {size_mb:.2f} MB")


def main():
    """Función principal con línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Organizador automático de archivos de descargas",
        epilog="Ejemplo: python organizer.py --simulate --config custom_rules.json"
    )
    parser.add_argument("--config", "-c", type=str, help="Ruta al archivo de configuración JSON")
    parser.add_argument("--simulate", "-s", action="store_true", help="Simular organización sin mover archivos")
    parser.add_argument("--stats", "-t", action="store_true", help="Mostrar estadísticas de archivos organizados")
    parser.add_argument("--quiet", "-q", action="store_true", help="Modo silencioso (menos output)")
    
    args = parser.parse_args()
    organizer = DownloadsOrganizer(config_path=args.config)
    
    if args.stats:
        organizer.show_stats()
    else:
        organizer.organize_all(simulate=args.simulate)


if __name__ == "__main__":
    main()