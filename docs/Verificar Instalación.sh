#!/bin/bash
# shellcheck shell=bash
# Script de Verificación de Instalación para Downloads Organizer
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
# Descripción: Verifica que todos los componentes estén instalados correctamente

set -e

echo "========================================"
echo "   DOWNLOADS ORGANIZER - VERIFICACIÓN"
echo "   Juan Carlos Blanco Ruiz"
echo "========================================"
echo ""

# 1. Verificar Python
echo "🔍 [1/5] Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python 3 no está instalado"
    echo "   💡 Instala Python 3.7+ desde python.org"
    exit 1
fi

# 2. Verificar pip
echo " [2/5] Verificando pip..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo "   ✅ $PIP_VERSION"
else
    echo "   ⚠️ pip3 no está instalado"
    echo "   💡 Instala pip con: python3 -m ensurepip --upgrade"
fi

# 3. Verificar script principal
echo "🔍 [3/5] Verificando script principal..."
if [ -f "src/organizer.py" ]; then
    echo "   ✅ src/organizer.py encontrado"
else
    echo "   ❌ No se encuentra src/organizer.py"
    echo "   ⚠️ Asegúrate de estar en la raíz del proyecto"
    exit 1
fi

# 4. Verificar dependencias
echo "🔍 [4/5] Verificando dependencias..."
if [ -f "requirements.txt" ]; then
    echo "   ✅ requirements.txt encontrado"
else
    echo "   ⚠️ No se encuentra requirements.txt"
fi

# 5. Probar ejecución en modo simulación
echo "🔍 [5/5] Probando ejecución en modo simulación..."
if python3 src/organizer.py --simulate; then
    echo "   ✅ El programa funciona correctamente"
else
    echo "   ❌ Error al ejecutar el programa"
    echo "   💡 Verifica que las dependencias estén instaladas: pip3 install -r requirements.txt"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ VERIFICACIÓN COMPLETADA CON ÉXITO"
echo "========================================"
echo ""
echo "🚀 El proyecto está listo para usar:"
echo "   python3 src/organizer.py              # Ejecutar"
echo "   python3 src/organizer.py --simulate   # Simular"
echo "   python3 src/organizer.py --stats      # Estadísticas"
echo ""
echo "📧 Soporte: juancarlosblancoruiz@gmail.com"
echo "⭐ GitHub: https://github.com/Juank9113/downloads-organizer"