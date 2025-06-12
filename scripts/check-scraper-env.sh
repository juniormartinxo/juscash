#!/bin/bash

# check-scraper-env.sh - Verifica se o ambiente do scraper está configurado corretamente
# Executa verificações de pré-requisitos, dependências e configurações

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_check() { echo -e "${PURPLE}🔍 $1${NC}"; }

# Contadores
checks_passed=0
checks_failed=0
checks_warning=0

# Função para incrementar contadores
pass_check() { ((checks_passed++)); log_success "$1"; }
fail_check() { ((checks_failed++)); log_error "$1"; }
warn_check() { ((checks_warning++)); log_warning "$1"; }

# Banner
echo "🔍 JusCash - Verificação do Ambiente Scraper"
echo "============================================="
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Iniciando verificação do ambiente do scraper..."
echo ""

# 1. Verificar estrutura de diretórios
log_check "1. Verificando estrutura de diretórios..."

required_dirs=(
    "backend/scraper"
    "backend/scraper/src"
    "backend/scraper/src/config"
    "backend/scraper/src/core"
    "backend/scraper/src/adapters"
    "backend/scraper/src/shared"
    "scripts"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        pass_check "Diretório encontrado: $dir"
    else
        fail_check "Diretório não encontrado: $dir"
    fi
done

echo ""

# 2. Verificar arquivos essenciais
log_check "2. Verificando arquivos essenciais..."

required_files=(
    "backend/scraper/requirements.txt"
    "backend/scraper/src/main.py"
    "backend/scraper/src/__init__.py"
    "docker-compose.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        pass_check "Arquivo encontrado: $file"
    else
        fail_check "Arquivo não encontrado: $file"
    fi
done

echo ""

# 3. Verificar Python
log_check "3. Verificando Python..."

if command -v python3 >/dev/null 2>&1; then
    version=$(python3 --version 2>&1 | awk '{print $2}')
    major=$(echo $version | cut -d. -f1)
    minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
        pass_check "Python $version (compatível)"
    else
        fail_check "Python $version (necessário 3.8+)"
    fi
else
    fail_check "Python3 não encontrado"
fi

echo ""

# 4. Verificar ambiente virtual
log_check "4. Verificando ambiente virtual..."

if [ -d "backend/scraper/venv" ]; then
    pass_check "Ambiente virtual encontrado"
    
    # Verificar se o ambiente virtual tem as dependências
    if [ -f "backend/scraper/venv/pyvenv.cfg" ]; then
        pass_check "Ambiente virtual configurado corretamente"
    else
        warn_check "Ambiente virtual pode estar corrompido"
    fi
else
    fail_check "Ambiente virtual não encontrado (execute: ./scripts/install-scraper.sh)"
fi

echo ""

# 5. Verificar dependências Python (se ambiente virtual existir)
if [ -d "backend/scraper/venv" ]; then
    log_check "5. Verificando dependências Python..."
    
    cd backend/scraper
    source venv/bin/activate 2>/dev/null || true
    
    dependencies=(
        "playwright"
        "sqlalchemy"
        "redis"
        "loguru"
        "beautifulsoup4"
        "asyncpg"
        "pydantic"
        "apscheduler"
    )
    
    for dep in "${dependencies[@]}"; do
        if python -c "import $dep" 2>/dev/null; then
            pass_check "Dependência instalada: $dep"
        else
            fail_check "Dependência não encontrada: $dep"
        fi
    done
    
    cd ../..
else
    log_check "5. Pulando verificação de dependências (ambiente virtual não encontrado)"
fi

echo ""

# 6. Verificar Playwright browsers
log_check "6. Verificando browsers do Playwright..."

if [ -d "backend/scraper/venv" ]; then
    cd backend/scraper
    source venv/bin/activate 2>/dev/null || true
    
    if python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>/dev/null; then
        pass_check "Chromium do Playwright instalado e funcional"
    else
        fail_check "Chromium do Playwright não encontrado ou não funcional"
    fi
    
    cd ../..
else
    warn_check "Não foi possível verificar browsers (ambiente virtual não encontrado)"
fi

echo ""

# 7. Verificar variáveis de ambiente
log_check "7. Verificando variáveis de ambiente..."

if [ -f ".env" ]; then
    pass_check "Arquivo .env encontrado"
    
    required_vars=(
        "POSTGRES_URL_ASYNC"
    )
    
    optional_vars=(
        "REDIS_URL"
        "DJE_CADERNO"
        "DJE_INSTANCIA"
        "SCRAPING_HEADLESS"
        "SCRAPING_TIMEOUT"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            pass_check "Variável obrigatória configurada: $var"
        else
            fail_check "Variável obrigatória não encontrada: $var"
        fi
    done
    
    for var in "${optional_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            pass_check "Variável opcional configurada: $var"
        else
            warn_check "Variável opcional não configurada: $var"
        fi
    done
    
else
    fail_check "Arquivo .env não encontrado"
fi

echo ""

# 8. Verificar Docker (se disponível)
log_check "8. Verificando Docker..."

if command -v docker >/dev/null 2>&1; then
    if docker --version >/dev/null 2>&1; then
        pass_check "Docker instalado e funcional"
        
        if command -v docker-compose >/dev/null 2>&1; then
            pass_check "Docker Compose disponível"
        else
            warn_check "Docker Compose não encontrado"
        fi
    else
        warn_check "Docker instalado mas não funcional"
    fi
else
    warn_check "Docker não encontrado (opcional para execução local)"
fi

echo ""

# 9. Verificar scripts de execução
log_check "9. Verificando scripts de execução..."

execution_scripts=(
    "scripts/install-scraper.sh"
    "scripts/run-scraper-local.sh"
    "scripts/run-scraper-docker.sh"
    "scripts/test-scraper.sh"
)

for script in "${execution_scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            pass_check "Script executável: $script"
        else
            warn_check "Script não executável: $script (execute: chmod +x $script)"
        fi
    else
        fail_check "Script não encontrado: $script"
    fi
done

echo ""

# 10. Verificar conectividade (se possível)
log_check "10. Verificando conectividade..."

if [ -f ".env" ] && [ -d "backend/scraper/venv" ]; then
    cd backend/scraper
    source venv/bin/activate 2>/dev/null || true
    
    # Carregar variáveis de ambiente
    export $(grep -v '^#' ../../.env | xargs) 2>/dev/null || true
    
    # Testar conexão com banco (se POSTGRES_URL_ASYNC estiver configurada)
    if [ ! -z "$POSTGRES_URL_ASYNC" ]; then
        if python -c "
import asyncio
import sys
sys.path.append('.')
from src.main import test_database
result = asyncio.run(test_database())
sys.exit(0 if result else 1)
" 2>/dev/null; then
            pass_check "Conexão com banco de dados OK"
        else
            warn_check "Não foi possível conectar ao banco de dados"
        fi
    else
        warn_check "POSTGRES_URL_ASYNC não configurada - não foi possível testar conexão"
    fi
    
    cd ../..
else
    warn_check "Não foi possível testar conectividade (ambiente não configurado)"
fi

echo ""

# Resumo final
echo "📊 RESUMO DA VERIFICAÇÃO"
echo "========================"
echo ""
echo "✅ Verificações aprovadas: $checks_passed"
echo "⚠️  Avisos: $checks_warning"
echo "❌ Verificações falharam: $checks_failed"
echo ""

if [ $checks_failed -eq 0 ]; then
    if [ $checks_warning -eq 0 ]; then
        log_success "🎉 Ambiente do scraper está completamente configurado!"
        echo ""
        echo "🚀 Próximos passos:"
        echo "   ./scripts/run-scraper-local.sh          # Executar scraper"
        echo "   ./scripts/test-scraper.sh               # Executar testes"
        echo "   ./scripts/run-scraper-docker.sh         # Executar via Docker"
    else
        log_success "✅ Ambiente do scraper está funcional (com alguns avisos)"
        echo ""
        echo "⚠️  Considere resolver os avisos para melhor experiência"
        echo ""
        echo "🚀 Próximos passos:"
        echo "   ./scripts/run-scraper-local.sh          # Executar scraper"
        echo "   ./scripts/test-scraper.sh               # Executar testes"
    fi
    exit 0
else
    log_error "❌ Ambiente do scraper precisa de correções"
    echo ""
    echo "🔧 Para corrigir os problemas:"
    echo "   ./scripts/install-scraper.sh             # Instalar/reinstalar scraper"
    echo "   ./install.sh --scraper-only              # Instalação via script principal"
    echo ""
    exit 1
fi 