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

echo -e "${YELLOW}"
echo "╭──💡 Deseja continuar com a instalação do DJE JusCash?──╮"
echo "|                                                        |"
echo "|     Este script irá resetar todo o ambiente,           |"
echo "|     incluindo o banco de dados e o scraper.            |"
echo "|     Para continuar, digite 's' e pressione Enter.      |"
echo "|     Para cancelar, digite 'n' e pressione Enter.       |"
echo "|                                                        |"
echo "╰────────────────────────────────────────────────────────╯"
echo -e "${NC}"

read -p "Deseja continuar com a instalação? (s/n): " confirm
if [ "$confirm" != "s" ]; then
    echo ""
    log_error ">>> Instalação cancelada pelo usuário. Execute o script novamente para continuar."
    echo ""
    exit 1
fi

# verifica se algum container está em execução e se estiver esecuta docker compose down
if [ "$(docker ps -q)" ]; then
    echo ""
    log_warning "══════ Parando containers em execução ══════"
    echo ""
    docker compose down --rmi all
fi

# Banner de início
echo ""
log_success "╭───────────────── DJE JusCash - Script de Instalação ─────────────────╮"
echo ""

export COMPOSE_BAKE=true

echo ""
log_info "═════ EXECUTANDO CHMOD +X PARA SCRIPTS ═══════"
echo ""

# Dando permissão de execução aos scripts da pasta scripts
if [ -d "scripts" ]; then
    chmod +x scripts/*.sh
else
    log_error ">>> Pasta 'scripts' não encontrada."
    echo ""
    exit 1
fi

echo ""
log_warning "══════ LIMPANDO WORKSPACE ══════"
echo ""

# Limpar o projeto com o script ./scrpits/clean-workspace.sh
if [ -f "scripts/clean-workspace.sh" ]; then
    chmod +x scripts/clean-workspace.sh
    ./scripts/clean-workspace.sh
else
    log_error ">>> Script clean-workspace.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_info "══════ VERIFICANDO SE ESTAMOS NO DIRETÓRIO CORRETO ══════"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error ">>> docker-compose.yml não encontrado. Execute o script a partir do diretório raiz do projeto."
    echo ""
    exit 1
fi

# Verificar se a pasta scripts existe
if [ ! -d "scripts" ]; then
    log_error ">>> Pasta 'scripts' não encontrada."
    echo ""
    exit 1
fi

echo ""
echo "╭───────────────────────────────────────────────────────────────╮"
echo "│          Iniciando configuração do ambiente JusCash           │"
echo "╰───────────────────────────────────────────────────────────────╯"
echo ""

# 1. Verificar variáveis de ambiente
echo ""
log_info "═════ 1/7 - VERIFICANDO VARIÁVEIS DE AMBIENTE ═════"

if [ -f "scripts/check-env.sh" ]; then
    chmod +x scripts/check-env.sh
    if ./scripts/check-env.sh; then
        log_success "Verificação de variáveis de ambiente concluída - todas as variáveis estão corretas!"
        echo ""
    else
        log_warning "Algumas variáveis estão incorretas - verifique os valores antes de iniciar"
        log_info "Execute novamente: ./scripts/check-env.sh"
        exit 1
    fi
else
    log_error ">>> Script check-env.sh não encontrado em scripts/"
    exit 1
fi

echo ""
log_success "═════ FIM DA VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ═════"
echo ""

# 2. Verificar portas
echo ""
log_info "═════ 2/7 - VERIFICANDO CONFLITOS DE PORTAS ═════"
echo ""

if [ -f "scripts/check-ports.sh" ]; then
    chmod +x scripts/check-ports.sh
    if ./scripts/check-ports.sh; then
        log_success "Verificação de portas concluída - todas as portas estão livres!"
        echo ""
    else
        log_warning "Algumas portas estão em uso - verifique os conflitos antes de iniciar"
        log_info "Execute novamente: ./scripts/check-ports.sh"
        echo ""
    fi
else
    log_error ">>> Script check-ports.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_success "═════ FIM DA VERIFICAÇÃO DE CONFLITOS DE PORTAS ═════"
echo ""

# 3. Configurar Redis
echo ""
log_info "══════ 3/7 - CONFIGURANDO O REDIS ══════"
if [ -f "scripts/setup-redis.sh" ]; then
    chmod +x scripts/setup-redis.sh
    if ./scripts/setup-redis.sh; then
        log_success "Redis configurado com sucesso!"
        echo ""
    else
        log_error ">>> Falha ao configurar Redis"
        echo ""
        exit 1
    fi
else
    log_error ">>> Script setup-redis.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_success "═════ FIM DA CONFIGURAÇÃO DO REDIS ═════"
echo ""

# 4. Configurar API
echo ""
log_info "══════ 4/7 - CONFIGURANDO A API ══════"
if [ -f "scripts/setup-api.sh" ]; then
    chmod +x scripts/setup-api.sh
    if ./scripts/setup-api.sh; then
        log_success "API configurada com sucesso!"
        echo ""
    else
        log_error ">>> Falha ao configurar API"
        echo ""
        exit 1
    fi
else
    log_error ">>> Script setup-api.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_success "════════════ 4/7 ════════════"
echo ""

# 5. Configurar banco de dados
echo ""
log_info "══════ 5/7 - CONFIGURANDO BANCO DE DADOS COM PRISMA ══════"
if [ -f "scripts/setup-database.sh" ]; then
    chmod +x scripts/setup-database.sh
    if ./scripts/setup-database.sh; then
        log_success "Banco de dados configurado com sucesso!"
        echo ""
    else
        log_error ">>> Falha ao configurar banco de dados"
        echo ""
        exit 1
    fi
else
    log_error ">>> Script setup-database.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_success "═════ FIM DA CONFIGURAÇÃO DA API ═════"
echo ""

# 6. Configurar Vite
echo ""
log_info "══════ 6/7 - CONFIGURANDO O VITE ══════"
if [ -f "scripts/setup-vite.sh" ]; then
    chmod +x scripts/setup-vite.sh
    if ./scripts/setup-vite.sh; then
        log_success "Vite configurado com sucesso!"
        echo ""
    else
        log_error ">>> Falha ao configurar Vite"
        echo ""
        exit 1
    fi
else
    log_error ">>> Script setup-vite.sh não encontrado em scripts/"
    echo ""
    exit 1
fi

echo ""
log_success "═════ FIM DA CONFIGURAÇÃO DO VITE ═════"
echo ""

# 7. Configurar scraper
log_info "══════ 7/7 - CONFIGURANDO O SCRAPER ══════"
if [ -f "scripts/setup-scraper.sh" ]; then
    chmod +x scripts/setup-scraper.sh
    if ./scripts/setup-scraper.sh; then
        log_success "Scraper configurado com sucesso!"
        echo ""
    else
        log_error ">>> Falha ao configurar scraper"
        echo ""
        exit 1
    fi
else
    log_error ">>> Script setup-scraper.sh não encontrado em scripts/"
    echo ""
    exit 1
fi
echo ""
log_success "═════ FIM DA CONFIGURAÇÃO DO SCRAPER ═════"
echo ""

echo ""
log_success "╭───────────────────────────────────────────╮"
log_success "|   🎉 Instalação concluída com sucesso!    |"
log_success "╰───────────────────────────────────────────╯"
echo ""