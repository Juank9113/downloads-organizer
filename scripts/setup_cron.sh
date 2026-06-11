#!/bin/bash
# shellcheck shell=bash
# Script para configurar automatización con cron
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   CONFIGURACIÓN DE CRON - AUTOMATIZACIÓN${NC}"
echo -e "${BLUE}   Downloads Organizer${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar si cron está instalado
if ! command -v crontab &> /dev/null; then
    echo -e "${RED}❌ crontab no está instalado${NC}"
    echo -e "${YELLOW}Instálalo con:${NC}"
    echo -e "  Ubuntu/Debian: ${GREEN}sudo apt install cron${NC}"
    echo -e "  CentOS/RHEL: ${GREEN}sudo yum install cronie${NC}"
    echo -e "  macOS: Ya viene incluido${NC}"
    exit 1
fi

# Ruta del script
SCRIPT_PATH="$HOME/.local/bin/downloads-organizer"
if [ ! -f "$SCRIPT_PATH" ]; then
    SCRIPT_PATH="$(pwd)/src/organizer.py"
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo -e "${RED}❌ No se encuentra el script organizer.py${NC}"
        exit 1
    fi
fi

# Mostrar opciones
echo -e "${BLUE}Selecciona la frecuencia de ejecución:${NC}"
echo "1) Cada hora (recomendado)"
echo "2) Cada día a las 10 AM"
echo "3) Cada día a las 6 PM"
echo "4) Cada 30 minutos"
echo "5) Personalizado"
echo "6) Eliminar todas las tareas programadas"
echo "7) Ver tareas actuales"
echo "8) Salir"
read -p "Opción (1-8): " option

case $option in
    1)
        CRON_SCHEDULE="0 * * * *"
        DESCRIPTION="cada hora"
        ;;
    2)
        CRON_SCHEDULE="0 10 * * *"
        DESCRIPTION="cada día a las 10:00 AM"
        ;;
    3)
        CRON_SCHEDULE="0 18 * * *"
        DESCRIPTION="cada día a las 6:00 PM"
        ;;
    4)
        CRON_SCHEDULE="*/30 * * * *"
        DESCRIPTION="cada 30 minutos"
        ;;
    5)
        echo -e "${BLUE}Formato cron: (minuto hora día mes día_semana)${NC}"
        echo -e "${YELLOW}Ejemplos:${NC}"
        echo "  0 9 * * 1   → Lunes a las 9 AM"
        echo "  */15 * * * * → Cada 15 minutos"
        echo "  0 0 * * 0   → Domingos a medianoche"
        read -p "Ingresa tu programación cron: " CRON_SCHEDULE
        DESCRIPTION="personalizado: $CRON_SCHEDULE"
        ;;
    6)
        echo -e "${YELLOW}⚠️ Eliminando todas las tareas de downloads-organizer...${NC}"
        crontab -l 2>/dev/null | grep -v "downloads-organizer" | crontab -
        echo -e "${GREEN}✅ Tareas eliminadas${NC}"
        exit 0
        ;;
    7)
        echo -e "${BLUE}📋 Tareas actuales en crontab:${NC}"
        crontab -l 2>/dev/null | grep "downloads-organizer" || echo "No hay tareas configuradas"
        exit 0
        ;;
    8)
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Opción inválida${NC}"
        exit 1
        ;;
esac

# Preguntar si quiere modo silencioso
read -p "¿Ejecutar en modo silencioso (sin output)? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    QUIET_FLAG="--quiet"
else
    QUIET_FLAG=""
fi

# Crear la línea de cron
CRON_JOB="$CRON_SCHEDULE $SCRIPT_PATH $QUIET_FLAG"

# Añadir al crontab
echo -e "${BLUE}📝 Configurando tarea programada...${NC}"

# Respaldar crontab actual
crontab -l > /tmp/crontab_backup.txt 2>/dev/null || echo "# Crontab backup" > /tmp/crontab_backup.txt

# Eliminar tareas anteriores del mismo programa
crontab -l 2>/dev/null | grep -v "downloads-organizer" | crontab -

# Añadir nueva tarea
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo -e "${GREEN}✅ Tarea configurada exitosamente${NC}"
echo ""
echo -e "${BLUE}📋 Detalles de la tarea:${NC}"
echo "   Ejecución: $DESCRIPTION"
echo "   Comando: $SCRIPT_PATH $QUIET_FLAG"
echo "   Programación cron: $CRON_SCHEDULE"
echo ""

# Mostrar crontab actual
echo -e "${BLUE}📋 Contenido actual de crontab:${NC}"
crontab -l
echo ""

echo -e "${YELLOW}️ Notas importantes:${NC}"
echo "   - Asegúrate de que el script tiene permisos de ejecución"
echo "   - Verifica que Python está en el PATH del usuario"
echo "   - Los logs se guardan en ~/.downloads_organizer.log"
echo ""
echo -e "${GREEN}✅ Configuración completada${NC}"
echo -e "Para verificar que funciona, espera a la próxima ejecución o ejecuta:"
echo -e "  ${GREEN}crontab -l${NC}  # Ver tareas programadas"
echo -e "  ${GREEN}grep CRON /var/log/syslog${NC}  # Ver logs de cron (Linux)"