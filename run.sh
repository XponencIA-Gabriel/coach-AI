#!/bin/bash
# Coach AI - Script de inicio (Linux/Mac)

echo "========================================"
echo "         Coach AI - Iniciando"
echo "========================================"
echo ""

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "[1/4] Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        echo "Asegurate de tener Python 3 instalado"
        exit 1
    fi
else
    echo "[1/4] Entorno virtual encontrado"
fi

# Activar entorno virtual
echo "[2/4] Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "[3/4] Verificando dependencias..."
pip install -r requirements.txt -q

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo ""
    echo "ERROR: No se encontro el archivo .env"
    echo "Copia .env.example a .env y configura tus credenciales"
    exit 1
fi

# Ejecutar el bot
echo "[4/4] Iniciando bot..."
echo ""
echo "========================================"
echo "    Bot iniciado - Ctrl+C para detener"
echo "========================================"
echo ""

python main.py

# Si el bot termina
echo ""
echo "Bot detenido."
