#!/bin/bash

# Script para probar los endpoints del servidor de pagos

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Test de Endpoints - Servidor de Pagos                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="http://localhost:8002"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para hacer requests
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 $description"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ "$method" = "GET" ]; then
        echo "GET $BASE_URL$endpoint"
        echo ""
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        echo "$method $BASE_URL$endpoint"
        echo "Data: $data"
        echo ""
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    # Separar respuesta y código HTTP
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    # Mostrar resultado
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ Status: $http_code${NC}"
    elif [ "$http_code" -ge 400 ] && [ "$http_code" -lt 500 ]; then
        echo -e "${YELLOW}⚠️  Status: $http_code${NC}"
    else
        echo -e "${RED}❌ Status: $http_code${NC}"
    fi
    
    echo "Response:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
}

# Test 1: Health Check
test_endpoint "GET" "/health" "" "Test 1: Health Check"

# Test 2: Listar tarjetas (usuario 1)
test_endpoint "GET" "/tarjetas/usuario/1" "" "Test 2: Listar tarjetas del usuario 1"

# Test 3: Listar tarjetas (usuario 999 - no existe)
test_endpoint "GET" "/tarjetas/usuario/999" "" "Test 3: Listar tarjetas de usuario inexistente"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Tests completados"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Notas:"
echo "  - Para guardar una tarjeta, necesitas un token válido de Mercado Pago"
echo "  - El token se genera en la aplicación móvil automáticamente"
echo "  - Usa las tarjetas de prueba proporcionadas en TESTING_GUIDE.md"
echo ""
