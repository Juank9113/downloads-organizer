#!/bin/bash
# shellcheck shell=bash
# Script de Instalación como Paquete Python
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
# Descripción: Instala Downloads Organizer como paquete Python global

set -e

echo "========================================"
echo "   DOWNLOADS ORGANIZER - INSTALACIÓN COMO PAQUETE"
echo "   Juan Carlos Blanco Ruiz"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "setup.py" ]; then
    echo "❌ Error: No se encuentra setup.py"
    echo "⚠️ Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi
echo "✅ $(python3 --version)"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado"
    exit 1
fi
echo "✅ $(pip3 --version)"

# Paso 1: Instalar en modo editable
echo ""
echo " Paso 1: Instalando paquete en modo editable..."
pip3 install -e .
echo "✅ Paquete instalado"

# Paso 2: Verificar instalación
echo ""
echo "🔍 Paso 2: Verificando instalación..."
if command -v downloads-organizer &> /dev/null; then
    echo "✅ Comando 'downloads-organizer' disponible"
else
    echo "⚠️ El comando no está en el PATH"
    echo " Intenta: export PATH=\"\$PATH:\$HOME/.local/bin\""
fi

# Paso 3: Probar ejecución
echo ""
echo "🧪 Paso 3: Probando ejecución..."
downloads-organizer --help || python3 src/organizer.py --help

echo ""
echo "========================================"
echo "✅ INSTALACIÓN COMO PAQUETE COMPLETADA"
echo "========================================"
echo ""
echo "🚀 Ahora puedes ejecutar desde cualquier lugar:"
echo "   downloads-organizer              # Ejecutar"
echo "   downloads-organizer --simulate   # Simular"
echo "   downloads-organizer --stats      # Estadísticas"
echo ""
echo "📧 Soporte: juancarlosblancoruiz@gmail.com"