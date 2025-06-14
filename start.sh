#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    log_error "Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Verificar se o arquivo docker-compose.yml existe
if [ ! -f "docker-compose.yml" ]; then
    log_error "Arquivo docker-compose.yml não encontrado. Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    log_error "Arquivo .env não encontrado. Execute ./install.sh primeiro."
    exit 1
fi

# Verificar se os containers já existem
log_info "Verificando containers existentes..."
if docker-compose ps --services | grep -q "api\|vite\|postgres\|redis\|scraper"; then
    log_info "Containers encontrados. Iniciando serviços..."
    docker-compose up -d
    log_success "Serviços iniciados com sucesso!"
else
    log_warning "Nenhum container encontrado. Execute ./install.sh primeiro para configurar o ambiente."
    exit 1
fi

# Verificar status dos containers
log_info "Verificando status dos containers..."
docker-compose ps

# Mostrar logs dos containers
log_info "Mostrando logs dos containers (pressione Ctrl+C para sair)..."
docker-compose logs -f 