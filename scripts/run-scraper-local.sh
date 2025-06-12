#!/bin/bash

# run-scraper-local.sh - Executa o scraper localmente

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

log_info "Executando scraper localmente..."

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
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
    log_info "Variáveis de ambiente carregadas"
fi

python -m pip install -r requirements.txt

# Executar scraper
log_info "Iniciando scraper..."
python -m src.main "$@"

log_success "Scraper finalizado"
