# Coach AI - Script de inicio (PowerShell)
$Host.UI.RawUI.WindowTitle = "Coach AI Bot"

Write-Host "========================================"
Write-Host "         Coach AI - Iniciando"
Write-Host "========================================"
Write-Host ""

# Verificar si existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "[1/4] Creando entorno virtual..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
        Write-Host "Asegurate de tener Python instalado"
        Read-Host "Presiona Enter para salir"
        exit 1
    }
} else {
    Write-Host "[1/4] Entorno virtual encontrado"
}

# Activar entorno virtual
Write-Host "[2/4] Activando entorno virtual..."
& ".\venv\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host "[3/4] Verificando dependencias..."
pip install -r requirements.txt -q

# Verificar archivo .env
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "ERROR: No se encontro el archivo .env" -ForegroundColor Red
    Write-Host "Copia .env.example a .env y configura tus credenciales"
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Ejecutar el bot
Write-Host "[4/4] Iniciando bot..."
Write-Host ""
Write-Host "========================================"
Write-Host "    Bot iniciado - Ctrl+C para detener"
Write-Host "========================================"
Write-Host ""

python main.py

# Si el bot termina
Write-Host ""
Write-Host "Bot detenido."
Read-Host "Presiona Enter para salir"
