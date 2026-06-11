"""
Módulo de configuración para Downloads Organizer
Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Configuración por defecto
DEFAULT_CATEGORIES = {
    "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".odt", ".rtf", ".md"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Musica": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Archivos_Comprimidos": [".zip", ".rar", ".tar", ".gz", ".7z", ".bz2"],
    "Programas": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage"],
    "Codigo": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json", ".xml", ".yaml"],
}

DEFAULT_CONFIG = {
    "downloads_dir": str(Path.home() / "Downloads"),
    "organized_dir": str(Path.home() / "Downloads_Organized"),
    "categories": DEFAULT_CATEGORIES,
    "exclude_extensions": [".tmp", ".temp", ".crdownload", ".part"],
    "log_level": "INFO",
    "notifications": False,
    "auto_clean": False,
    "clean_days": 30
}

class ConfigManager:
    """Gestor de configuración para el organizador"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo o usa valores por defecto"""
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Fusionar con configuración por defecto
                    config = DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except Exception as e:
                print(f"⚠️ Error cargando configuración: {e}")
        
        return DEFAULT_CONFIG.copy()

    def save(self, config: Dict[str, Any]) -> bool:
        """Guarda la configuración en un archivo"""
        if not self.config_path:
            return False
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False

    def get_category_for_extension(self, extension: str) -> str:
        """Obtiene la categoría para una extensión específica"""
        extension = extension.lower()
        
        for category, extensions in self.config["categories"].items():
            if extension in extensions:
                return category
        
        return "Otros"

    def add_extension_to_category(self, extension: str, category: str) -> bool:
        """Añade una extensión a una categoría existente"""
        if category not in self.config["categories"]:
            return False
        
        extension = extension.lower()
        if extension not in self.config["categories"][category]:
            self.config["categories"][category].append(extension)
            return self.save(self.config)
        
        return False