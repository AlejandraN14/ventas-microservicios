#!/bin/bash

# Script para iniciar el servidor de pagos

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Servidor de Pagos - Mercado Pago Integration              ║"
echo "║     Puerto: 8002                                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: No se encontró requirements.txt"
    echo "Asegúrate de ejecutar este script desde /app-pagos"
    exit 1
fi

# Instalar dependencias si es necesario
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
    echo ""
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar/actualizar dependencias
echo "📥 Verificando dependencias..."
pip install -q -r requirements.txt
echo "✅ Dependencias instaladas"
echo ""

# Mostrar información de inicio
echo "🚀 Iniciando servidor..."
echo "   URL: http://localhost:8002"
echo "   Health: http://localhost:8002/health"
echo "   Docs: http://localhost:8002/docs"
echo ""
echo "⏳ Presiona Ctrl+C para detener el servidor"
echo ""

# Iniciar el servidor con reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
