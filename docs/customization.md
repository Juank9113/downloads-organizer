# Personalización Avanzada - Downloads Organizer

## 🎨 Configuración Completa

### Archivo de configuración completo

Crea un archivo `config_personal.json` con la siguiente estructura:

```json
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Personal",
    "categories": {
        "01_Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "02_Documentos": [".pdf", ".docx", ".txt", ".odt"],
        "03_Videos": [".mp4", ".avi", ".mkv"],
        "04_Audio": [".mp3", ".wav", ".flac"],
        "05_Proyectos": [".py", ".js", ".html", ".css"],
        "06_Programas": [".exe", ".msi", ".dmg"],
        "07_Comprimidos": [".zip", ".rar", ".7z"]
    },
    "exclude_extensions": [".tmp", ".crdownload", ".part"],
    "log_level": "INFO",
    "notifications": true,
    "auto_clean": false,
    "clean_days": 30
}