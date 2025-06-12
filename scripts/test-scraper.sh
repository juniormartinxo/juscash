#!/bin/bash

# test-scraper.sh - Executa testes do scraper

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Executando testes do scraper..."

# Navegar para o diretório do scraper
cd backend/scraper

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "Ambiente virtual ativado"
else
    echo "❌ Ambiente virtual não encontrado. Execute: ./scripts/install-scraper.sh"
    exit 1
fi

# Carregar variáveis de ambiente
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
    log_info "Variáveis de ambiente carregadas"
fi

# Executar testes
log_info "Executando testes unitários..."
if [ -f "pytest.ini" ]; then
    python -m pytest tests/ -v
else
    log_info "Executando teste de conexão com banco..."
    python -m src.main --test-db
    
    log_info "Executando teste de scraping..."
    python -m src.main --test-scraping
fi

log_success "Testes concluídos"
