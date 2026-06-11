#!/bin/bash
# shellcheck shell=bash
# scripts/weekly_report.sh
# Genera reporte semanal de organización
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuración
REPORT_DIR="$HOME/Reports/DownloadsOrganizer"
LOG_FILE="$HOME/.downloads_organizer.log"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Crear directorio de reportes
mkdir -p "$REPORT_DIR"

# Obtener fecha
FECHA=$(date +%Y%m%d)
FECHA_LEGIBLE=$(date '+%d/%m/%Y %H:%M:%S')
DIA_SEMANA=$(date '+%A')
REPORTE_FILE="$REPORT_DIR/reporte_$FECHA.txt"
REPORTE_HTML="$REPORT_DIR/reporte_$FECHA.html"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   GENERANDO REPORTE SEMANAL${NC}"
echo -e "${BLUE}   Downloads Organizer${NC}"
echo -e "${BLUE}========================================${NC}"

# Función para generar reporte en texto
generar_reporte_texto() {
    {
        echo "========================================="
        echo "   REPORTE SEMANAL - DOWNLOADS ORGANIZER"
        echo "   Fecha: $FECHA_LEGIBLE"
        echo "   Día: $DIA_SEMANA"
        echo "   Autor: Juan Carlos Blanco Ruiz"
        echo "========================================="
        echo ""
        echo "📊 ESTADÍSTICAS DE ORGANIZACIÓN:"
        echo "-----------------------------------------"
        cd "$PROJECT_DIR"
        python3 src/organizer.py --stats 2>/dev/null || echo "  No se pudieron obtener estadísticas"
        echo ""
        echo "📁 TOP 10 TIPOS DE ARCHIVO MÁS COMUNES:"
        echo "-----------------------------------------"
        if [ -d ~/Downloads_Organized ]; then
            find ~/Downloads_Organized -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
        else
            echo "  No hay archivos organizados aún"
        fi
        echo ""
        echo "💾 ESPACIO OCUPADO POR CATEGORÍA:"
        echo "-----------------------------------------"
        if [ -d ~/Downloads_Organized ]; then
            du -sh ~/Downloads_Organized/*/ 2>/dev/null | sort -rh | head -10
        else
            echo "  No hay archivos organizados aún"
        fi
        echo ""
        echo "📈 ACTIVIDAD DE LOS ÚLTIMOS 7 DÍAS:"
        echo "-----------------------------------------"
        for i in {0..6}; do
            fecha_log=$(date -d "-${i} days" +%Y-%m-%d)
            if [ -f "$LOG_FILE" ]; then
                count=$(grep -c "${fecha_log}.*✅" "$LOG_FILE" 2>/dev/null || echo "0")
                fecha_mostrar=$(date -d "-${i} days" +%d/%m)
                if [ "$count" -gt 0 ]; then
                    printf "  %s: %4d archivos organizados\n" "$fecha_mostrar" "$count"
                else
                    printf "  %s:    0 archivos organizados\n" "$fecha_mostrar"
                fi
            else
                echo "  $fecha_log: No hay logs disponibles"
            fi
        done
        echo ""
        echo "📊 TOTALES ACUMULADOS:"
        echo "-----------------------------------------"
        if [ -d ~/Downloads_Organized ]; then
            total_files=$(find ~/Downloads_Organized -type f 2>/dev/null | wc -l)
            total_size=$(du -sh ~/Downloads_Organized 2>/dev/null | cut -f1)
            echo "  Total de archivos: $total_files"
            echo "  Tamaño total: $total_size"
        fi
        echo ""
        echo " RECOMENDACIONES:"
        echo "-----------------------------------------"
        if [ -d ~/Downloads_Organized/Otros ]; then
            otros_count=$(find ~/Downloads_Organized/Otros -type f 2>/dev/null | wc -l)
            if [ "$otros_count" -gt 10 ]; then
                echo "  ⚠️ Tienes $otros_count archivos en 'Otros'"
                echo "     Considera añadir nuevas extensiones a tu configuración"
            fi
        fi
        uso_disco=$(df -h ~ | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ "$uso_disco" -gt 80 ]; then
            echo "  ⚠️ Tu disco está al ${uso_disco}% de uso"
            echo "     Considera liberar espacio o mover archivos a almacenamiento externo"
        fi
        echo ""
        echo "========================================="
        echo "   FIN DEL REPORTE"
        echo "   Generado por Downloads Organizer"
        echo "========================================="
    } > "$REPORTE_FILE"
}

# Función para generar reporte en HTML
generar_reporte_html() {
    {
        echo "<!DOCTYPE html>"
        echo "<html>"
        echo "<head>"
        echo "  <meta charset='UTF-8'>"
        echo "  <title>Reporte Downloads Organizer - $FECHA</title>"
        echo "  <style>"
        echo "    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }"
        echo "    .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }"
        echo "    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }"
        echo "    h2 { color: #34495e; margin-top: 30px; }"
        echo "    .stats { background: #ecf0f1; padding: 15px; border-radius: 8px; margin: 20px 0; }"
        echo "    .footer { margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 12px; }"
        echo "  </style>"
        echo "</head>"
        echo "<body>"
        echo "<div class='container'>"
        echo "  <h1> Downloads Organizer - Reporte Semanal</h1>"
        echo "  <p><strong>Fecha:</strong> $FECHA_LEGIBLE</p>"
        echo "  <p><strong>Autor:</strong> Juan Carlos Blanco Ruiz</p>"
        echo ""
        echo "  <div class='stats'>"
        echo "    <h2>📈 Resumen</h2>"
        cd "$PROJECT_DIR"
        python3 src/organizer.py --stats 2>/dev/null | sed 's/$/<br>/'
        echo "  </div>"
        echo ""
        echo "  <div class='footer'>"
        echo "    Reporte generado automáticamente por Downloads Organizer"
        echo "    <br>GitHub: https://github.com/Juank9113/downloads-organizer"
        echo "  </div>"
        echo "</div>"
        echo "</body>"
        echo "</html>"
    } > "$REPORTE_HTML"
}

# Generar reportes
generar_reporte_texto
generar_reporte_html

# Mostrar reporte en consola
echo ""
cat "$REPORTE_FILE"

# Guardar en log principal
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reporte semanal generado" >> "$LOG_FILE"

echo ""
echo -e "${GREEN}✅ Reporte generado exitosamente${NC}"
echo -e "${BLUE}📁 Reporte texto: $REPORTE_FILE${NC}"
echo -e "${BLUE}🌐 Reporte HTML: $REPORTE_HTML${NC}"

echo ""
echo -e "${YELLOW}💡 Para programar este reporte automáticamente cada lunes:${NC}"
echo "   crontab -e"
echo "   Añadir: 0 9 * * 1 $PROJECT_DIR/scripts/weekly_report.sh"