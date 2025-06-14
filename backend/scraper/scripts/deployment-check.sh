#!/bin/bash

# Script de verificação pós-deployment
# Valida se o sistema está funcionando corretamente

set -e

echo "🔍 Verificação Pós-Deployment - DJE Scraper"
echo "============================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Contadores
tests_passed=0
tests_failed=0
tests_total=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    tests_total=$((tests_total + 1))
    log_info "Teste: $test_name"
    
    if eval "$test_command"; then
        log_success "$test_name: PASSOU"
        tests_passed=$((tests_passed + 1))
        return 0
    else
        log_error "$test_name: FALHOU"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
}

# Teste 1: Verificar arquivos essenciais
run_test "Arquivos essenciais" "[ -f '.env' ] && [ -f 'requirements.txt' ] && [ -d 'src' ]"

# Teste 2: Verificar dependências Python
run_test "Dependências Python" "python3 -c 'import playwright, httpx, loguru, pydantic' 2>/dev/null"

# Teste 3: Verificar CLI
run_test "CLI funcionando" "python3 scraper_cli.py version >/dev/null 2>&1"

# Teste 4: Verificar configuração
run_test "Configuração válida" "python3 scraper_cli.py config show >/dev/null 2>&1"

# Teste 5: Verificar conectividade API (se configurada)
if [ -n "$API_BASE_URL" ]; then
    run_test "Conectividade API" "python3 scraper_cli.py test api --api-url $API_BASE_URL >/dev/null 2>&1"
else
    log_warning "API_BASE_URL não configurada - pulando teste de API"
fi

# Teste 6: Verificar acesso DJE
run_test "Acesso ao DJE" "python3 scraper_cli.py test dje >/dev/null 2>&1"

# Teste 7: Verificar browsers Playwright
run_test "Browsers Playwright" "python3 -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()' >/dev/null 2>&1"

# Teste 8: Verificar diretórios
run_test "Estrutura de diretórios" "[ -d 'logs' ] && [ -d 'backups' ] && [ -d 'config' ]"

# Teste 9: Verificar permissões
run_test "Permissões de escrita" "touch logs/test.tmp && rm logs/test.tmp"

# Teste 10: Verificar serviço systemd (se configurado)
if systemctl list-unit-files | grep -q "dje-scraper.service"; then
    run_test "Serviço systemd" "systemctl is-enabled dje-scraper >/dev/null 2>&1"
else
    log_warning "Serviço systemd não configurado"
fi

# Teste 11: Health check completo
run_test "Health check geral" "python3 -c '
import asyncio
import sys
sys.path.insert(0, \"src\")
from infrastructure.health.health_checker import HealthChecker

async def check():
    checker = HealthChecker()
    result = await checker.run_all_checks()
    return result[\"overall_status\"] in [\"healthy\", \"warning\"]

result = asyncio.run(check())
exit(0 if result else 1)
' 2>/dev/null"

# Teste 12: Teste de execução rápida (dry-run)
run_test "Execução de teste" "timeout 60 python3 scraper_cli.py run --dry-run --max-pages 1 >/dev/null 2>&1"

# Resumo dos testes
echo ""
echo "📊 Resumo da Verificação"
echo "========================"
echo "Total de testes: $tests_total"
echo "Passou: $tests_passed"
echo "Falhou: $tests_failed"

if [ $tests_failed -eq 0 ]; then
    log_success "Todos os testes passaram! Sistema pronto para produção."
    echo ""
    echo "🚀 Para iniciar o scraper:"
    echo "   sudo systemctl start dje-scraper"
    echo ""
    echo "📊 Para monitorar:"
    echo "   journalctl -fu dje-scraper"
    echo "   python3 scraper_cli.py status"
    exit 0
else
    log_error "$tests_failed testes falharam. Corrija os problemas antes de usar em produção."
    echo ""
    echo "🔧 Para debug:"
    echo "   python3 scraper_cli.py config show"
    echo "   python3 scraper_cli.py test api"
    echo "   python3 scraper_cli.py test dje"
    exit 1
fi