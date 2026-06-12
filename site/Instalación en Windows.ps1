#Requires -Version 5.1
# Script de Instalación Automatizada para Downloads Organizer en Windows
# Autor: Juan Carlos Blanco Ruiz
# Email: juancarlosblancoruiz@gmail.com
# Descripción: Verifica dependencias, clona el repo (si es necesario), crea venv e instala requisitos.

# Configuración inicial
$ErrorActionPreference = "Stop"
$RepoName = "downloads-organizer"
$RepoUrl = "https://github.com/Juank9113/downloads-organizer.git"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DOWNLOADS ORGANIZER - INSTALACIÓN" -ForegroundColor Cyan
Write-Host "   Windows Automated Installer v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "   ✅ $pythonVersion detectado." -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python no está instalado o no está en el PATH." -ForegroundColor Red
    Write-Host "   💡 Descárgalo desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "   ⚠️ IMPORTANTE: Marca 'Add Python to PATH' durante la instalación." -ForegroundColor Yellow
    exit 1
}

# 2. Verificar Git
Write-Host "[2/6] Verificando Git..." -ForegroundColor Yellow
try {
    $gitVersion = & git --version 2>&1
    Write-Host "   ✅ $gitVersion detectado." -ForegroundColor Green
} catch {
    Write-Host "   ❌ Git no está instalado." -ForegroundColor Red
    Write-Host "   💡 Descárgalo desde: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 3. Clonar o entrar al repositorio
Write-Host "[3/6] Preparando repositorio..." -ForegroundColor Yellow
if (-not (Test-Path -Path $RepoName)) {
    Write-Host "   📥 Clonando repositorio desde GitHub..." -ForegroundColor Blue
    & git clone $RepoUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Error al clonar el repositorio. Verifica tu conexión a internet." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ El repositorio '$RepoName' ya existe en esta carpeta." -ForegroundColor Green
}
Set-Location -Path $RepoName

# 4. Crear entorno virtual
Write-Host "[4/6] Creando entorno virtual..." -ForegroundColor Yellow
& python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Error al crear el entorno virtual." -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Entorno virtual creado exitosamente." -ForegroundColor Green

# 5. Activar entorno virtual e instalar dependencias
Write-Host "[5/6] Activando entorno e instalando dependencias..." -ForegroundColor Yellow

# Ajustar política de ejecución temporalmente para este proceso si es necesario
$currentPolicy = Get-ExecutionPolicy -Scope Process
if ($currentPolicy -eq "Restricted") {
    Write-Host "   ⚠️ Ajustando política de ejecución para este proceso..." -ForegroundColor Yellow
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
}

& .\venv\Scripts\Activate.ps1
& pip install --upgrade pip -q
& pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Error al instalar las dependencias de requirements.txt." -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Dependencias instaladas correctamente." -ForegroundColor Green

# 6. Mensaje final
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ INSTALACIÓN COMPLETADA CON ÉXITO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Activa el entorno virtual (si cierras esta ventana):" -ForegroundColor White
Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   2. Ejecuta el programa en modo simulación:" -ForegroundColor White
Write-Host "      python src\organizer.py --simulate" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Soporte: juancarlosblancoruiz@gmail.com" -ForegroundColor DarkGray
Write-Host "⭐ GitHub: https://github.com/Juank9113/downloads-organizer" -ForegroundColor DarkGray