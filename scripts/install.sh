#!/bin/bash
# shellcheck shell=bash
# Script de instalación para Downloads Organizer
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   DOWNLOADS ORGANIZER - INSTALACIÓN${NC}"
echo -e "${BLUE}   Juan Carlos Blanco Ruiz${NC}"
echo -e "${BLUE}========================================${NC}"

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    INSTALL_DIR="$HOME/.local/bin"
    CONFIG_DIR="$HOME/.config/downloads-organizer"
    BASH_RC="$HOME/.bashrc"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    INSTALL_DIR="/usr/local/bin"
    CONFIG_DIR="$HOME/.config/downloads-organizer"
    BASH_RC="$HOME/.zshrc"
elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="Windows"
    INSTALL_DIR="$HOME/AppData/Local/Programs/downloads-organizer"
    CONFIG_DIR="$HOME/.config/downloads-organizer"
    BASH_RC="$HOME/.bashrc"
else
    echo -e "${RED}❌ Sistema operativo no soportado: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Detectado: $OS${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    echo -e "${YELLOW}📥 Instala Python 3.7 o superior desde python.org${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠️ pip3 no encontrado, intentando instalar...${NC}"
    python3 -m ensurepip --upgrade
fi

# Crear directorios
echo -e "${BLUE}📁 Creando directorios...${NC}"
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR"

# Copiar script principal al proyecto
echo -e "${BLUE}📋 Verificando archivos del proyecto...${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "src/organizer.py" ]; then
    echo -e "${RED}❌ No se encuentra src/organizer.py${NC}"
    echo -e "${YELLOW}⚠️ Asegúrate de ejecutar este script desde la raíz del proyecto${NC}"
    exit 1
fi

# Instalar dependencias
echo -e "${BLUE}📦 Instalando dependencias Python...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${YELLOW}⚠️ No se encuentra requirements.txt${NC}"
fi

# Crear script ejecutable
echo -e "${BLUE} Instalando script...${NC}"
cat > "$INSTALL_DIR/downloads-organizer" << 'EOF'
#!/bin/bash
# Wrapper para Downloads Organizer
python3 "$HOME/.local/bin/downloads-organizer.py" "$@"
EOF

# Copiar el script principal
cp src/organizer.py "$INSTALL_DIR/downloads-organizer.py"
chmod +x "$INSTALL_DIR/downloads-organizer"
chmod +x "$INSTALL_DIR/downloads-organizer.py"

# Copiar configuración por defecto
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    if [ -f "examples/custom_rules.json" ]; then
        cp examples/custom_rules.json "$CONFIG_DIR/config.json"
        echo -e "${GREEN}✅ Configuración por defecto creada en $CONFIG_DIR/config.json${NC}"
    else
        # Crear configuración por defecto
        cat > "$CONFIG_DIR/config.json" << 'EOCONFIG'
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized",
    "log_level": "INFO",
    "notifications": false,
    "exclude_extensions": [".tmp", ".temp", ".crdownload", ".part"],
    "categories": {
        "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
        "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".odt"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
        "Musica": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
        "Archivos_Comprimidos": [".zip", ".rar", ".tar", ".gz", ".7z"],
        "Programas": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"],
        "Codigo": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json"]
    }
}
EOCONFIG
        echo -e "${GREEN}✅ Configuración por defecto creada${NC}"
    fi
fi

# Añadir a PATH si es necesario
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️ Añadiendo $INSTALL_DIR al PATH...${NC}"
    # Añadir a .bashrc o .zshrc
    if [ -f "$BASH_RC" ]; then
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$BASH_RC"
        echo -e "${GREEN}✅ PATH actualizado en $BASH_RC${NC}"
    fi
    # Actualizar PATH para la sesión actual
    export PATH="$PATH:$INSTALL_DIR"
fi

# Configurar alias opcional
echo -e "${BLUE}🔧 Configuración adicional...${NC}"
read -p "¿Deseas crear un alias 'organize' para ejecutar el programa? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if [ -f "$BASH_RC" ]; then
        echo "alias organize='downloads-organizer'" >> "$BASH_RC"
        echo -e "${GREEN}✅ Alias 'organize' creado${NC}"
    fi
fi

# Preguntar por configuración de cron
echo
read -p "¿Deseas configurar ejecución automática cada hora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if [ -f "scripts/setup_cron.sh" ]; then
        chmod +x scripts/setup_cron.sh
        ./scripts/setup_cron.sh
    else
        echo -e "${YELLOW}️ No se encuentra scripts/setup_cron.sh${NC}"
        echo -e "${YELLOW}Configura manualmente con: crontab -e${NC}"
        echo -e "${YELLOW}Añade: 0 * * * * $INSTALL_DIR/downloads-organizer --quiet${NC}"
    fi
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA CON ÉXITO${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🚀 Para comenzar:${NC}"
echo -e "   ${GREEN}downloads-organizer${NC}              # Ejecutar interactivo"
echo -e "   ${GREEN}downloads-organizer --simulate${NC}   # Simular sin mover archivos"
echo -e "   ${GREEN}downloads-organizer --stats${NC}      # Ver estadísticas"
echo -e "   ${GREEN}downloads-organizer --help${NC}       # Ver ayuda"
echo ""
echo -e "${BLUE}📁 Configuración:${NC}"
echo -e "   Archivo de configuración: ${YELLOW}$CONFIG_DIR/config.json${NC}"
echo ""
echo -e "${BLUE}📧 Reportar issues: ${NC}juancarlosblancoruiz@gmail.com"
echo -e "${BLUE}⭐ GitHub: ${NC}https://github.com/Juank9113/downloads-organizer"
echo ""
echo -e "${YELLOW}⚠️ IMPORTANTE:${NC}"
echo -e "   Reinicia tu terminal o ejecuta: ${GREEN}source $BASH_RC${NC}"
echo -e "   Para usar el comando 'downloads-organizer'"