#!/bin/bash

# run-scraper-docker.sh - Executa o scraper via Docker

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

# Verifica se o arquivo Dockerfile do scraper existe
if [ ! -f "backend/scraper/.docker/Dockerfile" ]; then
    echo "❌ Arquivo Dockerfile do scraper não encontrado."
    exit 1
fi

# Verifica se o arquivo entrypoint.sh do scraper existe
if [ ! -f "backend/scraper/.docker/entrypoint.sh" ]; then
    echo "❌ Arquivo entrypoint.sh do scraper não encontrado."
    exit 1
else
    chmod +x backend/scraper/.docker/entrypoint.sh
fi

log_info "Executando scraper via Docker..."

# Construir e executar apenas o scraper
docker-compose up --build scraper -d

log_success "Scraper finalizado"
