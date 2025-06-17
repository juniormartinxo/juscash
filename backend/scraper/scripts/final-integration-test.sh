#!/bin/bash

# Teste final de integração completa
# Valida todo o pipeline: Scraper -> API -> Database -> Frontend

set -e

echo "🧪 Teste Final de Integração - Sistema Completo DJE"
echo "=================================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configurações
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TEST_TIMEOUT=300  # 5 minutos

tests_passed=0
tests_failed=0

run_integration_test() {
    local test_name="$1"
    local test_function="$2"
    
    log_info "Executando: $test_name"
    
    if $test_function; then
        log_success "$test_name: PASSOU"
        tests_passed=$((tests_passed + 1))
        return 0
    else
        log_error "$test_name: FALHOU"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
}

# Teste 1: Verificar se todos os serviços estão rodando
test_services_running() {
    # API
    if ! curl -f "$API_URL/health" >/dev/null 2>&1; then
        echo "API não está respondendo em $API_URL"
        return 1
    fi
    
    # Frontend (se estiver rodando)
    if curl -f "$FRONTEND_URL" >/dev/null 2>&1; then
        echo "Frontend acessível em $FRONTEND_URL"
    else
        echo "Frontend não acessível - prosseguindo com teste backend"
    fi
    
    # Database (via API)
    if ! curl -f "$API_URL/api/publications?limit=1" >/dev/null 2>&1; then
        echo "Database não acessível via API"
        return 1
    fi
    
    return 0
}

# Teste 2: Executar scraping de teste
test_scraping_execution() {
    echo "Executando scraping de teste..."
    
    timeout $TEST_TIMEOUT python3 scraper_cli.py run --dry-run --max-pages 1 >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "Scraping de teste executado com sucesso"
        return 0
    else
        echo "Falha no scraping de teste"
        return 1
    fi
}

# Teste 3: Testar API endpoints
test_api_endpoints() {
    local api_key=$(grep SCRAPER_API_KEY .env | cut -d'=' -f2)
    
    # Test health endpoint
    if ! curl -f "$API_URL/health" >/dev/null 2>&1; then
        echo "Health endpoint falhou"
        return 1
    fi
    
    # Test scraper endpoint
    test_publication='{"process_number":"TEST-'$(date +%s)'-89.2024.8.26.0100","availabilityDate":"2024-03-17T00:00:00.000Z","authors":["Test Author"],"content":"Test content aposentadoria benefício","defendant":"Instituto Nacional do Seguro Social - INSS"}'
    
    response=$(curl -s -X POST "$API_URL/api/scraper/publications" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $api_key" \
        -d "$test_publication")
    
    if echo "$response" | grep -q '"success":true'; then
        echo "API endpoint de scraper funcionando"
        return 0
    else
        echo "API endpoint de scraper falhou: $response"
        return 1
    fi
}

# Teste 4: Testar persistência de dados
test_data_persistence() {
    # Criar publicação via API
    local api_key=$(grep SCRAPER_API_KEY .env | cut -d'=' -f2)
    local test_process="PERSIST-$(date +%s)-89.2024.8.26.0100"
    
    test_publication="{\"process_number\":\"$test_process\",\"availabilityDate\":\"2024-03-17T00:00:00.000Z\",\"authors\":[\"Persistence Test\"],\"content\":\"Test persistence aposentadoria benefício\",\"defendant\":\"Instituto Nacional do Seguro Social - INSS\"}"
    
    # Criar
    curl -s -X POST "$API_URL/api/scraper/publications" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $api_key" \
        -d "$test_publication" >/dev/null
    
    # Aguardar um pouco
    sleep 2
    
    # Buscar
    response=$(curl -s "$API_URL/api/publications?search=$test_process")
    
    if echo "$response" | grep -q "$test_process"; then
        echo "Persistência de dados funcionando"
        return 0
    else
        echo "Falha na persistência de dados"
        return 1
    fi
}

# Teste 5: Testar performance básica
test_basic_performance() {
    local start_time=$(date +%s)
    
    # Executar múltiplas requisições
    for i in {1..10}; do
        curl -s "$API_URL/health" >/dev/null &
    done
    
    wait  # Aguardar todas as requisições
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $duration -lt 10 ]; then
        echo "Performance básica OK ($duration segundos)"
        return 0
    else
        echo "Performance básica lenta ($duration segundos)"
        return 1
    fi
}

# Teste 6: Testar sistema de logs
test_logging_system() {
    local log_file="logs/scraper_$(date +%Y-%m-%d).log"
    
    # Gerar algumas entradas de log
    python3 scraper_cli.py version >/dev/null 2>&1
    
    if [ -f "$log_file" ]; then
        local log_size=$(stat -c%s "$log_file" 2>/dev/null || stat -f%z "$log_file" 2>/dev/null || echo "0")
        if [ "$log_size" -gt 0 ]; then
            echo "Sistema de logs funcionando"
            return 0
        fi
    fi
    
    echo "Sistema de logs não está funcionando"
    return 1
}

# Teste 7: Testar backup system
test_backup_system() {
    # Executar backup de teste
    if python3 scraper_cli.py backup logs --days-back 1 >/dev/null 2>&1; then
        echo "Sistema de backup funcionando"
        return 0
    else
        echo "Sistema de backup falhou"
        return 1
    fi
}

# Teste 8: Testar alertas
test_alert_system() {
    # Testar listagem de alertas
    if python3 scraper_cli.py alerts list >/dev/null 2>&1; then
        echo "Sistema de alertas funcionando"
        return 0
    else
        echo "Sistema de alertas falhou"
        return 1
    fi
}

# Teste 9: Testar health check completo
test_health_check() {
    if python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from infrastructure.health.health_checker import HealthChecker

async def check():
    checker = HealthChecker()
    result = await checker.run_all_checks()
    print(f'Health check status: {result[\"overall_status\"]}')
    return result['overall_status'] in ['healthy', 'warning']

exit(0 if asyncio.run(check()) else 1)
" 2>/dev/null; then
        echo "Health check passou"
        return 0
    else
        echo "Health check falhou"
        return 1
    fi
}

# Teste 10: Testar configuração dinâmica
test_dynamic_config() {
    # Testar leitura de configuração
    if python3 scraper_cli.py config show >/dev/null 2>&1; then
        echo "Configuração dinâmica funcionando"
        return 0
    else
        echo "Configuração dinâmica falhou"
        return 1
    fi
}

# Executar todos os testes
echo "🚀 Iniciando testes de integração..."
echo ""

run_integration_test "Serviços Rodando" test_services_running
run_integration_test "Execução de Scraping" test_scraping_execution
run_integration_test "Endpoints da API" test_api_endpoints
run_integration_test "Persistência de Dados" test_data_persistence
run_integration_test "Performance Básica" test_basic_performance
run_integration_test "Sistema de Logs" test_logging_system
run_integration_test "Sistema de Backup" test_backup_system
run_integration_test "Sistema de Alertas" test_alert_system
run_integration_test "Health Check" test_health_check
run_integration_test "Configuração Dinâmica" test_dynamic_config

# Resumo final
echo ""
echo "📊 Resumo dos Testes de Integração"
echo "=================================="
echo "✅ Testes passaram: $tests_passed"
echo "❌ Testes falharam: $tests_failed"
echo "📈 Total: $((tests_passed + tests_failed))"

if [ $tests_failed -eq 0 ]; then
    echo ""
    log_success "🎉 TODOS OS TESTES PASSARAM!"
    echo ""
    echo "🚀 Sistema DJE Scraper está PRONTO PARA PRODUÇÃO!"
    echo ""
    echo "📋 Próximos passos recomendados:"
    echo "1. Configure monitoramento contínuo"
    echo "2. Configure alertas por email"
    echo "3. Configure backup automático"
    echo "4. Inicie o serviço: sudo systemctl start dje-scraper"
    echo "5. Configure auto-start: sudo systemctl enable dje-scraper"
    echo ""
    echo "📊 URLs importantes:"
    echo "   API: $API_URL"
    echo "   API Docs: $API_URL/api-docs"
    echo "   Health: $API_URL/health"
    if curl -f "$FRONTEND_URL" >/dev/null 2>&1; then
        echo "   Frontend: $FRONTEND_URL"
    fi
    
    exit 0
else
    echo ""
    log_error "❌ ALGUNS TESTES FALHARAM!"
    echo ""
    echo "🔧 Antes de usar em produção:"
    echo "1. Corrija os problemas identificados"
    echo "2. Execute os testes novamente"
    echo "3. Verifique logs para mais detalhes"
    echo ""
    echo "📋 Para debug:"
    echo "   Logs da API: docker-compose logs api"
    echo "   Status: python3 scraper_cli.py status"
    echo "   Health: python3 scraper_cli.py test api"
    
    exit 1
fi