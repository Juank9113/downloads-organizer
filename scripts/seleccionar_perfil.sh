#!/bin/bash
# shellcheck shell=bash
# scripts/seleccionar_perfil.sh
# Script interactivo para seleccionar perfil de configuración
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
set -e

# Colores para mejor experiencia
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Obtener directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Crear carpeta de configuraciones si no existe
mkdir -p configs

# Función para crear configuración por defecto si no existe
crear_config_si_no_existe() {
    local config_file="$1"
    local config_name="$2"
    if [ ! -f "configs/$config_file" ]; then
        echo -e "${YELLOW}️ No existe configs/$config_file, creándolo...${NC}"
        case "$config_name" in
            "estudiante")
                cat > "configs/$config_file" << 'EOF'
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Estudiante",
    "log_level": "INFO",
    "notifications": true,
    "categories": {
        "Apuntes_PDF": [".pdf"],
        "Documentos_Word": [".docx", ".doc"],
        "Presentaciones": [".pptx", ".ppt"],
        "Codigo": [".py", ".java", ".cpp", ".js", ".html", ".css"],
        "Imagenes_Clase": [".jpg", ".jpeg", ".png", ".gif"],
        "Tareas_Entregadas": [".zip", ".rar", ".7z"],
        "Libros": [".epub", ".mobi", ".azw"]
    },
    "exclude_extensions": [".tmp", ".crdownload"]
}
EOF
                ;;
            "desarrollador")
                cat > "configs/$config_file" << 'EOF'
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Desarrollador",
    "log_level": "DEBUG",
    "notifications": true,
    "categories": {
        "Python": [".py", ".pyc", ".ipynb", ".pyw"],
        "JavaScript_TypeScript": [".js", ".jsx", ".ts", ".tsx", ".mjs"],
        "Web_Frontend": [".html", ".css", ".scss", ".sass", ".less"],
        "Web_Backend": [".php", ".go", ".rb", ".java", ".scala"],
        "Bases_Datos": [".sql", ".db", ".sqlite", ".dump"],
        "Configuracion": [".json", ".yaml", ".yml", ".toml", ".ini", ".env"],
        "Docker": ["Dockerfile", ".dockerignore"],
        "Documentacion": [".md", ".rst", ".txt"]
    },
    "exclude_extensions": [".tmp", ".crdownload", ".pyc", ".class"]
}
EOF
                ;;
            "disenador")
                cat > "configs/$config_file" << 'EOF'
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Diseñador",
    "log_level": "INFO",
    "notifications": true,
    "categories": {
        "Fuentes_Tipograficas": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
        "Proyectos_Adobe": [".psd", ".ai", ".indd", ".aep", ".prproj"],
        "Vectoriales": [".svg", ".eps", ".pdf", ".cdr"],
        "Imagenes_Alta": [".png", ".jpg", ".jpeg", ".tiff", ".raw", ".bmp"],
        "Mockups_UI": [".fig", ".sketch", ".xd", ".afdesign"],
        "Videos_Animacion": [".mp4", ".mov", ".avi", ".gif"],
        "Iconos": [".ico", ".svg", ".icns"],
        "Modelos_3D": [".obj", ".fbx", ".blend", ".stl", ".dae"]
    },
    "exclude_extensions": [".tmp", ".crdownload"]
}
EOF
                ;;
            "profesional")
                cat > "configs/$config_file" << 'EOF'
{
    "downloads_dir": "~/Downloads",
    "organized_dir": "~/Downloads_Organized/Profesional",
    "log_level": "INFO",
    "notifications": true,
    "categories": {
        "Clientes_Facturas": [".pdf", ".xlsx", ".xls", ".csv"],
        "Contratos_Legales": [".docx", ".pdf", ".odt", ".rtf"],
        "Propuestas_Presentaciones": [".pptx", ".ppt", ".key", ".pdf"],
        "Recursos_Graficos": [".psd", ".ai", ".eps", ".png", ".jpg"],
        "Minutas_Reuniones": [".txt", ".md", ".docx"],
        "Backups_Empresariales": [".zip", ".rar", ".7z", ".tar.gz"],
        "Correos_Archivados": [".eml", ".msg", ".pst"],
        "Reportes_Datos": [".csv", ".xlsx", ".json", ".xml"]
    },
    "exclude_extensions": [".tmp", ".crdownload", ".~"]
}
EOF
                ;;
        esac
        echo -e "${GREEN}✅ Configuración creada: configs/$config_file${NC}"
    fi
}

# Verificar/crear configuraciones de perfiles
crear_config_si_no_existe "estudiante.json" "estudiante"
crear_config_si_no_existe "desarrollador.json" "desarrollador"
crear_config_si_no_existe "disenador.json" "disenador"
crear_config_si_no_existe "profesional.json" "profesional"

# Función para mostrar header
mostrar_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     DOWNLOADS ORGANIZER - SELECTOR DE PERFILES          ║${NC}"
    echo -e "${BLUE}║     Autor: Juan Carlos Blanco Ruiz                      ${NC}"
    echo -e "${BLUE}║     Email: juancarlosblancoruiz@gmail.com               ${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Función para mostrar estadísticas rápidas
mostrar_stats() {
    if [ -d ~/Downloads_Organized ]; then
        local total
        total=$(find ~/Downloads_Organized -type f 2>/dev/null | wc -l)
        local size
        size=$(du -sh ~/Downloads_Organized 2>/dev/null | cut -f1)
        echo -e "${CYAN}📊 Archivos organizados: $total | Tamaño total: $size${NC}"
    else
        echo -e "${YELLOW}📊 Aún no hay archivos organizados${NC}"
    fi
}

# Mostrar header
mostrar_header

# Mostrar estadísticas
mostrar_stats
echo ""

# Mostrar menú principal
echo -e "${GREEN}┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│              SELECCIONA UN PERFIL                       │${NC}"
echo -e "${GREEN}────────────────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│${NC}                                                         ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}1)${NC} 📚 ${YELLOW}Perfil Estudiante${NC}       - Organización para estudios            ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}2)${NC} 💻 ${YELLOW}Perfil Desarrollador${NC}   - Código, configuraciones y proyectos  ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}3)${NC} 🎨 ${YELLOW}Perfil Diseñador${NC}       - Fuentes, imágenes y vectores         ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}4)${NC} 💼 ${YELLOW}Perfil Profesional${NC}     - Documentos laborales y facturas      ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}5)${NC} 🔧 ${YELLOW}Perfil Personalizado${NC}   - Usar mi propia configuración         ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}6)${NC} 📁 ${YELLOW}Perfil Por Defecto${NC}     - Configuración estándar               ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}7)${NC}  ${YELLOW}Ver Estadísticas${NC}       - Mostrar estadísticas actuales        ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}8)${NC} 🗑️  ${YELLOW}Limpiar Archivos${NC}      - Limpieza automática (cuidado)        ${NC}"
echo -e "${GREEN}│${NC}  ${CYAN}9)${NC} ❌ ${YELLOW}Salir${NC}                 - Salir del programa                   ${NC}"
echo -e "${GREEN}│${NC}                                                         ${NC}"
echo -e "${GREEN}└────────────────────────────────────────────────────────┘${NC}"
echo ""

read -r -p "$(echo -e "${CYAN}➤ Opción (1-9): ${NC}")" opcion

# Función para ejecutar organización
ejecutar_organizacion() {
    local config_file="$1"
    local perfil_nombre="$2"
    
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Perfil seleccionado: $perfil_nombre${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    
    if [ -n "$config_file" ] && [ -f "configs/$config_file" ]; then
        echo -e "${CYAN}📋 Usando configuración: configs/$config_file${NC}"
        echo -e "${YELLOW}📝 Categorías configuradas:${NC}"
        grep -E '"[^"]+": \[\.' "configs/$config_file" | head -5 | sed 's/^/   /'
        local total_categorias
        total_categorias=$(grep -c -E '"[^"]+": \[' "configs/$config_file")
        if [ "$total_categorias" -gt 5 ]; then
            echo "   ..."
        fi
    else
        echo -e "${CYAN}📋 Usando configuración por defecto${NC}"
    fi
    
    echo ""
    read -r -p "$(echo -e "${YELLOW}¿Ejecutar en modo simulación primero? (s/n): ${NC}")" -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}🔍 Modo simulación activado${NC}"
        echo ""
        if [ -n "$config_file" ] && [ -f "configs/$config_file" ]; then
            python3 src/organizer.py --config "configs/$config_file" --simulate
        else
            python3 src/organizer.py --simulate
        fi
        echo ""
        read -r -p "$(echo -e "${YELLOW}¿Ejecutar organización real? (s/n): ${NC}")" -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            echo -e "${RED}❌ Operación cancelada${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}🚀 Ejecutando organización...${NC}"
    echo ""
    
    # CORRECCIÓN: Verificar código de salida directamente con if
    if [ -n "$config_file" ] && [ -f "configs/$config_file" ]; then
        if python3 src/organizer.py --config "configs/$config_file"; then
            echo ""
            echo -e "${GREEN}✅ Organización completada exitosamente${NC}"
            echo ""
            python3 src/organizer.py --stats 2>/dev/null | head -15
        else
            echo -e "${RED}❌ Hubo errores durante la organización${NC}"
        fi
    else
        if python3 src/organizer.py; then
            echo ""
            echo -e "${GREEN}✅ Organización completada exitosamente${NC}"
            echo ""
            python3 src/organizer.py --stats 2>/dev/null | head -15
        else
            echo -e "${RED} Hubo errores durante la organización${NC}"
        fi
    fi
    
    return 0
}

# Procesar opción
case "$opcion" in
    1)
        ejecutar_organizacion "estudiante.json" "📚 Estudiante"
        ;;
    2)
        ejecutar_organizacion "desarrollador.json" "💻 Desarrollador"
        ;;
    3)
        ejecutar_organizacion "disenador.json" " Diseñador"
        ;;
    4)
        ejecutar_organizacion "profesional.json" "💼 Profesional"
        ;;
    5)
        echo ""
        echo -e "${CYAN}📁 Configuraciones personalizadas disponibles:${NC}"
        echo "----------------------------------------"
        find configs/ -maxdepth 1 -name "*.json" -type f 2>/dev/null | sed 's|configs/||' | sed 's/^/   /'
        echo "----------------------------------------"
        echo ""
        read -r -p "$(echo -e "${YELLOW}Nombre del archivo de configuración (ej: mi_config.json): ${NC}")" custom_config
        if [ -f "configs/$custom_config" ]; then
            ejecutar_organizacion "$custom_config" " Personalizado: $custom_config"
        else
            echo -e "${RED}❌ Archivo no encontrado: configs/$custom_config${NC}"
            exit 1
        fi
        ;;
    6)
        ejecutar_organizacion "" "📁 Por defecto"
        ;;
    7)
        echo ""
        python3 src/organizer.py --stats
        echo ""
        read -r -p "$(echo -e "${YELLOW}Presiona Enter para continuar...${NC}")"
        "$0"
        ;;
    8)
        echo ""
        echo -e "${RED}⚠️  LIMPIEZA AUTOMÁTICA - Archivos temporales${NC}"
        echo -e "${YELLOW}Esto eliminará archivos .tmp, .temp, .crdownload en Downloads${NC}"
        read -r -p "$(echo -e "${RED}¿Estás seguro? (s/n): ${NC}")" -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo -e "${YELLOW}🧹 Limpiando archivos temporales...${NC}"
            find ~/Downloads -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.crdownload" -o -name "*.part" \) -delete 2>/dev/null
            echo -e "${GREEN}✅ Limpieza completada${NC}"
        else
            echo -e "${CYAN}❌ Limpieza cancelada${NC}"
        fi
        echo ""
        read -r -p "$(echo -e "${YELLOW}Presiona Enter para continuar...${NC}")"
        "$0"
        ;;
    9)
        echo -e "${GREEN} ¡Hasta luego, que tengas un excelente día!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Opción inválida${NC}"
        sleep 2
        "$0"
        ;;
esac

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Proceso finalizado${NC}"
echo -e "${BLUE}📧 Reportar issues: juancarlosblancoruiz@gmail.com${NC}"
echo -e "${BLUE}⭐ GitHub: https://github.com/Juank9113/downloads-organizer${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"