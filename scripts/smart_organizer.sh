#!/bin/bash
# shellcheck shell=bash
# scripts/smart_organizer.sh
# Organizador inteligente que selecciona configuración según el día de la semana
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Crear carpeta de configuraciones si no existe
mkdir -p configs

# Obtener día de la semana (1 = Lunes, 2 = Martes, ..., 7 = Domingo)
DAY=$(date +%u)
DAY_NAME=$(date +%A)

# Función para crear configuración por defecto si no existe
crear_config() {
    local config_file=$1
    local config_content=$2
    if [ ! -f "configs/$config_file" ]; then
        echo "$config_content" > "configs/$config_file"
        echo -e "${GREEN}✅ Creada configuración: configs/$config_file${NC}"
    fi
}

# Crear todas las configuraciones necesarias si no existen
# Configuración para Lunes (Documentos de trabajo)
crear_config "config_lunes.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Trabajo",
    "categories": {
        "Documentos_Trabajo": [".pdf", ".docx", ".xlsx", ".pptx"],
        "Facturas": [".pdf", ".xml", ".xls"],
        "Contratos": [".docx", ".pdf"],
        "Reportes": [".xlsx", ".csv", ".txt"]
    },
    "exclude_extensions": [".tmp", ".crdownload"],
    "log_level": "INFO"
}'

# Configuración para Martes (Videos y música)
crear_config "config_multimedia.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Multimedia",
    "categories": {
        "Videos_4K": [".mp4", ".mkv", ".mov", ".m4v"],
        "Videos_HD": [".avi", ".wmv", ".flv", ".webm"],
        "Musica_FLAC": [".flac", ".wav", ".aiff"],
        "Musica_MP3": [".mp3", ".m4a", ".ogg"],
        "Podcasts": [".mp3", ".m4a"],
        "Listas_Reproduccion": [".m3u", ".pls"]
    },
    "exclude_extensions": [".tmp", ".crdownload"],
    "log_level": "INFO"
}'

# Configuración para Miércoles (Código y desarrollo)
crear_config "config_dev.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Desarrollo",
    "categories": {
        "Python": [".py", ".pyc", ".ipynb", ".pyw"],
        "JavaScript": [".js", ".jsx", ".ts", ".tsx", ".mjs"],
        "Web_Frontend": [".html", ".css", ".scss", ".sass", ".less"],
        "Web_Backend": [".php", ".go", ".rb", ".java"],
        "Config_Files": [".json", ".yaml", ".yml", ".toml", ".ini", ".env"],
        "Bases_Datos": [".sql", ".db", ".sqlite", ".dump"],
        "Docker": ["Dockerfile", ".dockerignore", ".yml"],
        "Documentacion": [".md", ".rst", ".txt"]
    },
    "exclude_extensions": [".tmp", ".crdownload", ".pyc"],
    "log_level": "DEBUG"
}'

# Configuración para Jueves (Respaldos y archivos comprimidos)
crear_config "config_backup.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Backups",
    "categories": {
        "Backups_DB": [".sql", ".dump", ".backup"],
        "Backups_Sistema": [".tar", ".gz", ".bz2", ".xz"],
        "Archivos_ZIP": [".zip", ".7z", ".rar"],
        "Backups_Config": [".conf", ".config", ".ini", ".bak"],
        "Imagenes_Disk": [".iso", ".img", ".dmg"],
        "Backups_Cloud": [".tar.gz", ".tgz"]
    },
    "exclude_extensions": [".tmp", ".crdownload"],
    "log_level": "INFO",
    "auto_clean": false
}'

# Configuración para Viernes (Limpieza general)
crear_config "config_limpieza.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Limpieza",
    "categories": {
        "Temporales": [".tmp", ".temp", ".cache", ".swp"],
        "Logs": [".log", ".out", ".error"],
        "Archivos_Viejos": [".old", ".bak", ".backup"],
        "Duplicados": ["_copy", "_backup"],
        "Instaladores": [".exe", ".msi", ".dmg", ".deb", ".rpm"]
    },
    "exclude_extensions": [".crdownload"],
    "log_level": "INFO",
    "auto_clean": true,
    "clean_days": 7
}'

# Configuración por defecto (Sábado y Domingo)
crear_config "config_default.json" '{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/General",
    "categories": {
        "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
        "Documentos": [".pdf", ".docx", ".txt", ".odt"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov"],
        "Musica": [".mp3", ".wav", ".flac"],
        "Programas": [".exe", ".msi", ".dmg", ".deb"],
        "Archivos_Comprimidos": [".zip", ".rar", ".7z"],
        "Codigo": [".py", ".js", ".html", ".css"]
    },
    "exclude_extensions": [".tmp", ".crdownload", ".part"],
    "log_level": "INFO"
}'

# Mostrar banner
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   SMART ORGANIZER - Downloads Organizer${NC}"
echo -e "${BLUE}   Autor: Juan Carlos Blanco Ruiz${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${CYAN}📅 Hoy es: $DAY_NAME${NC}"
echo ""

# Seleccionar configuración según día de la semana
case $DAY in
    1)
        CONFIG="configs/config_lunes.json"
        PERFIL=" Documentos de trabajo"
        ICONO=""
        DESCRIPCION="Organizando documentos, facturas y reportes laborales"
        ;;
    2)
        CONFIG="configs/config_multimedia.json"
        PERFIL="🎬 Videos y música"
        ICONO="🎵"
        DESCRIPCION="Organizando contenido multimedia, videos y audio"
        ;;
    3)
        CONFIG="configs/config_dev.json"
        PERFIL="💻 Código y desarrollo"
        ICONO="🐍"
        DESCRIPCION="Organizando código fuente, configuraciones y proyectos"
        ;;
    4)
        CONFIG="configs/config_backup.json"
        PERFIL="💾 Respaldos"
        ICONO="📦"
        DESCRIPCION="Organizando archivos comprimidos y respaldos"
        ;;
    5)
        CONFIG="configs/config_limpieza.json"
        PERFIL="🧹 Limpieza general"
        ICONO="🗑️"
        DESCRIPCION="Limpiando archivos temporales y logs"
        ;;
    *)
        CONFIG="configs/config_default.json"
        PERFIL="📁 Organización general"
        ICONO="📂"
        DESCRIPCION="Organización estándar para fin de semana"
        ;;
esac

# Mostrar información
echo -e "${GREEN}${ICONO} Perfil activo: $PERFIL${NC}"
echo -e "${BLUE}📋 Descripción: $DESCRIPCION${NC}"
echo -e "${YELLOW}⚙️ Configuración: $CONFIG${NC}"
echo ""

# Mostrar vista previa de la configuración
echo -e "${CYAN}📋 Vista previa de la configuración:${NC}"
echo "-----------------------------------------"
if [ -f "$CONFIG" ]; then
    cat "$CONFIG" | grep -E '"categories":|"downloads_dir":|"organized_dir":' | head -5
    echo "  ..."
else
    echo "  Configuración no encontrada"
fi
echo "-----------------------------------------"
echo ""

# Preguntar si quiere continuar
read -p "¿Deseas ejecutar la organización automática? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}❌ Operación cancelada por el usuario${NC}"
    exit 0
fi

# Preguntar por modo simulación
echo ""
read -p "¿Deseas simular antes de ejecutar? (s/n): " -n 1 -r
echo ""

# Ejecutar
echo -e "${BLUE}🚀 Ejecutando organización...${NC}"
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}🔍 MODO SIMULACIÓN - Vista previa${NC}"
    python3 src/organizer.py --config "$CONFIG" --simulate
    echo ""
    read -p "¿Ejecutar realmente la organización? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${GREEN}✅ Ejecutando organización real...${NC}"
        python3 src/organizer.py --config "$CONFIG"
    else
        echo -e "${YELLOW}❌ Organización cancelada${NC}"
        exit 0
    fi
else
    python3 src/organizer.py --config "$CONFIG"
fi

# Mostrar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ ORGANIZACIÓN COMPLETADA CON ÉXITO${NC}"
    echo -e "${GREEN}========================================${NC}"
    # Mostrar estadísticas rápidas
    echo ""
    echo -e "${CYAN} Estadísticas rápidas:${NC}"
    python3 src/organizer.py --stats 2>/dev/null | head -15
else
    echo ""
    echo -e "${RED}❌ Hubo errores durante la organización${NC}"
    echo -e "${YELLOW}💡 Revisa los logs para más detalles${NC}"
fi

echo ""
echo -e "${BLUE}📧 Reportar issues: juancarlosblancoruiz@gmail.com${NC}"
echo -e "${BLUE}⭐ GitHub: https://github.com/Juank9113/downloads-organizer${NC}"

# Registrar en log la ejecución
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Smart organizer ejecutado - Perfil: $PERFIL" >> "$HOME/.downloads_organizer.log"