#!/bin/bash

# install.sh - Script principal de instalação do JusCash
# Executa todos os scripts de configuração necessários

set -e  # Para execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Banner de início
echo "🚀 JusCash - Script de Instalação"
echo "=================================="
echo ""

# Verificar argumentos da linha de comando
if [ "$1" = "--scraper-only" ]; then
    log_info "Modo: Instalação apenas do Scraper"
    if [ -f "scripts/install-scraper.sh" ]; then
        chmod +x scripts/install-scraper.sh
        exec ./scripts/install-scraper.sh
    else
        log_error "Script install-scraper.sh não encontrado em scripts/"
        exit 1
    fi
elif [ "$1" = "--check-scraper" ]; then
    log_info "Modo: Verificação do ambiente do Scraper"
    if [ -f "scripts/check-scraper-env.sh" ]; then
        chmod +x scripts/check-scraper-env.sh
        exec ./scripts/check-scraper-env.sh
    else
        log_error "Script check-scraper-env.sh não encontrado em scripts/"
        exit 1
    fi
fi

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml não encontrado. Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

# Verificar se a pasta scripts existe
if [ ! -d "scripts" ]; then
    log_error "Pasta 'scripts' não encontrada."
    exit 1
fi

log_info "Iniciando configuração do ambiente JusCash..."
echo ""

# 1. Verificar variáveis de ambiente
log_info "Passo 1/5: Verificando variáveis de ambiente..."
if [ -f "scripts/check-env.sh" ]; then
    chmod +x scripts/check-env.sh
    if ./scripts/check-env.sh; then
        log_success "Verificação de variáveis de ambiente concluída - todas as variáveis estão corretas!"
    else
        log_warning "Algumas variáveis estão incorretas - verifique os valores antes de iniciar"
        log_info "Execute novamente: ./scripts/check-env.sh"
        exit 1
    fi
else
    log_error "Script check-env.sh não encontrado em scripts/"
    exit 1
fi

echo ""

# 2. Verificar portas
log_info "Passo 2/5: Verificando conflitos de portas..."
if [ -f "scripts/check-ports.sh" ]; then
    chmod +x scripts/check-ports.sh
    if ./scripts/check-ports.sh; then
        log_success "Verificação de portas concluída - todas as portas estão livres!"
    else
        log_warning "Algumas portas estão em uso - verifique os conflitos antes de iniciar"
        log_info "Execute novamente: ./scripts/check-ports.sh"
    fi
else
    log_error "Script check-ports.sh não encontrado em scripts/"
    exit 1
fi

echo ""

# 3. Configurar Redis
log_info "Passo 3/5: Configurando Redis..."
if [ -f "scripts/setup-redis.sh" ]; then
    chmod +x scripts/setup-redis.sh
    if ./scripts/setup-redis.sh; then
        log_success "Redis configurado com sucesso!"
    else
        log_error "Falha ao configurar Redis"
        exit 1
    fi
else
    log_error "Script setup-redis.sh não encontrado em scripts/"
    exit 1
fi

echo ""

# 4. Configurar banco de dados
log_info "Passo 4/5: Configurando banco de dados com Prisma..."
if [ -f "scripts/setup-database.sh" ]; then
    chmod +x scripts/setup-database.sh
    if ./scripts/setup-database.sh; then
        log_success "Banco de dados configurado com sucesso!"
    else
        log_error "Falha ao configurar banco de dados"
        exit 1
    fi
else
    log_error "Script setup-database.sh não encontrado em scripts/"
    exit 1
fi

# 5. Configurar scraper
log_info "Passo 5/5: Configurando scraper via Docker..."
if [ -f "scripts/run-scraper-docker.sh" ]; then
    chmod +x scripts/run-scraper-docker.sh
    if ./scripts/run-scraper-docker.sh; then
        log_success "Scraper configurado com sucesso!"
    else
        log_error "Falha ao configurar scraper"
        exit 1
    fi
else
    log_error "Script run-scraper-docker.sh não encontrado em scripts/"
    exit 1
fi
echo ""

# Verificação final
log_info "Verificando arquivos de configuração..."

required_files=(".env" "docker-compose.yml")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        log_success "Arquivo encontrado: $file"
    else
        log_error "Arquivo obrigatório não encontrado: $file"
        exit 1
    fi
done

echo ""
log_success "🎉 Instalação concluída com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "🐳 Para iniciar todos os serviços:"
echo "   docker-compose up --build"
echo ""
echo "🐳 Para iniciar em background:"
echo "   docker-compose up --build -d"
echo ""
echo "🔍 Para verificar status dos serviços:"
echo "   docker-compose ps"
echo ""
echo "🔍 Para ver logs de todos os serviços:"
echo "   docker-compose logs -f"
echo ""
echo "🔍 Para ver logs de um serviço específico:"
echo "   docker-compose logs -f [redis|postgres|api|vite]"
echo ""
echo "🔍 Para verificar portas antes de iniciar:"
echo "   ./scripts/check-ports.sh"
echo ""
echo "🗄️ Para configurar banco de dados:"
echo "   ./scripts/setup-database.sh"
echo ""
echo "🔍 Para visualizar banco de dados:"
echo "   docker-compose exec api npx prisma studio"
echo ""
echo "🛑 Para parar todos os serviços:"
echo "   docker-compose down"
echo ""
echo "🐍 Para instalar apenas o Scraper:"
echo "   ./install.sh --scraper-only"
echo ""
echo "🔍 Para verificar ambiente do Scraper:"
echo "   ./install.sh --check-scraper"
echo ""
echo "🐍 Para executar o scraper localmente:"
echo "   ./scripts/run-scraper-local.sh"
echo ""
echo "🐍 Para executar o scraper via Docker:"
echo "   ./scripts/run-scraper-docker.sh"
echo ""
echo "🧪 Para testar o scraper:"
echo "   ./scripts/test-scraper.sh"
echo ""