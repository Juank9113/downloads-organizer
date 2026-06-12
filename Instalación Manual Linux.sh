#!/bin/bash
# shellcheck shell=bash
# Script de Instalación Manual para Downloads Organizer (Linux)
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
# Descripción: Instalación paso a paso sin usar el script automático

set -e

echo "========================================"
echo "   DOWNLOADS ORGANIZER - INSTALACIÓN MANUAL (LINUX)"
echo "   Juan Carlos Blanco Ruiz"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "src/organizer.py" ]; then
    echo "❌ Error: No se encuentra src/organizer.py"
    echo "⚠️ Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Paso 1: Crear entorno virtual
echo "🐍 Paso 1: Creando entorno virtual..."
python3 -m venv venv
echo "✅ Entorno virtual creado"
echo ""

# Paso 2: Activar entorno virtual
echo "🔧 Paso 2: Activando entorno virtual..."
# shellcheck disable=SC1091
source venv/bin/activate
echo "✅ Entorno virtual activado"
echo ""

# Paso 3: Instalar dependencias
echo "📦 Paso 3: Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencias instaladas"
else
    echo "⚠️ No se encuentra requirements.txt, usando librerías estándar"
fi
echo ""

# Paso 4: Verificar instalación
echo "🔍 Paso 4: Verificando instalación..."
if [ -f "src/organizer.py" ]; then
    echo "✅ Script principal encontrado"
else
    echo "❌ Error: No se encuentra src/organizer.py"
    exit 1
fi
echo ""

# Paso 5: Probar en modo simulación
echo "🧪 Paso 5: Probando en modo simulación..."
python3 src/organizer.py --simulate
echo ""

echo "========================================"
echo "✅ INSTALACIÓN MANUAL COMPLETADA"
echo "========================================"
echo ""
echo "🚀 Para ejecutar en el futuro:"
echo "   1. Activa el entorno virtual: source venv/bin/activate"
echo "   2. Ejecuta: python3 src/organizer.py"
echo ""
echo "💡 Para salir del entorno virtual:"
echo "   deactivate"
echo ""
echo "📧 Soporte: juancarlosblancoruiz@gmail.com"
echo "⭐ GitHub: https://github.com/Juank9113/downloads-organizer"