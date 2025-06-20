#!/bin/bash

# Script para corrigir permissões dos diretórios do scraper
set -e

echo "🔧 Corrigindo permissões dos diretórios do scraper..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "Execute o script a partir do diretório raiz do projeto"
    exit 1
fi

# Criar diretórios se não existirem
log_info "Criando diretórios necessários..."
directories=(
    "backend/scraper/reports/json"
    "backend/scraper/reports/log"
    "backend/scraper/reports/pdf"
    "backend/scraper/logs"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_success "Diretório criado: $dir"
    else
        log_info "Diretório já existe: $dir"
    fi
done

# Obter UID/GID do usuário do container scraper
# Normalmente é 1000:1000, mas vamos verificar
log_info "Verificando UID/GID do usuário scraper no container..."

# Parar container se estiver rodando
docker-compose stop scraper 2>/dev/null || true

# Construir imagem se necessário
docker-compose build scraper

# Verificar UID/GID do usuário scraper
SCRAPER_UID=$(docker run --rm ${SCRAPER_CONTAINER_NAME:-juscash-scraper} id -u scraper 2>/dev/null || echo "1000")
SCRAPER_GID=$(docker run --rm ${SCRAPER_CONTAINER_NAME:-juscash-scraper} id -g scraper 2>/dev/null || echo "1000")

log_info "UID do usuário scraper: $SCRAPER_UID"
log_info "GID do usuário scraper: $SCRAPER_GID"

# Corrigir permissões dos diretórios
log_info "Corrigindo permissões dos diretórios..."

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        # Tentar alterar ownership primeiro
        if command -v sudo > /dev/null 2>&1; then
            log_info "Alterando ownership de $dir para $SCRAPER_UID:$SCRAPER_GID"
            sudo chown -R $SCRAPER_UID:$SCRAPER_GID "$dir" 2>/dev/null || {
                log_warning "Não foi possível alterar ownership com sudo. Tentando com chmod..."
                sudo chmod -R 777 "$dir"
            }
        else
            log_warning "Sudo não disponível. Tentando chmod 777..."
            chmod -R 777 "$dir" 2>/dev/null || {
                log_error "Não foi possível corrigir permissões de $dir"
                log_info "Execute: sudo chown -R $SCRAPER_UID:$SCRAPER_GID $dir"
            }
        fi
        
        # Garantir permissões de leitura/escrita/execução
        chmod -R 755 "$dir" 2>/dev/null || true
        
        log_success "Permissões corrigidas: $dir"
    fi
done

# Verificar se as permissões estão corretas
log_info "Verificando permissões..."
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        ls -la "$dir/" | head -3
    fi
done

log_success "🎉 Permissões corrigidas com sucesso!"
echo ""
log_info "Agora você pode iniciar o scraper:"
log_info "  docker-compose up -d scraper"
echo "" 