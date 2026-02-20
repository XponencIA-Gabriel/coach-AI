@echo off
title Coach AI Bot
echo ========================================
echo         Coach AI - Iniciando
echo ========================================
echo.

:: Verificar si existe el entorno virtual
if not exist "venv" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        echo Asegurate de tener Python instalado
        pause
        exit /b 1
    )
) else (
    echo [1/4] Entorno virtual encontrado
)

:: Activar entorno virtual
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat

:: Instalar dependencias
echo [3/4] Verificando dependencias...
pip install -r requirements.txt -q

:: Verificar archivo .env
if not exist ".env" (
    echo.
    echo ERROR: No se encontro el archivo .env
    echo Copia .env.example a .env y configura tus credenciales
    pause
    exit /b 1
)

:: Ejecutar el bot
echo [4/4] Iniciando bot...
echo.
echo ========================================
echo    Bot iniciado - Ctrl+C para detener
echo ========================================
echo.
python main.py

:: Si el bot termina
echo.
echo Bot detenido.
pause
