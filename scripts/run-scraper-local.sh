#!/bin/bash

# run-scraper-local.sh - Executa o scraper localmente

# Configurar tratamento de sinais
trap 'handle_exit' EXIT
trap 'handle_sigpipe' SIGPIPE

# Função para lidar com saída do script
handle_exit() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script finalizado com erro (código: $exit_code)"
    fi
    exit $exit_code
}

# Função para lidar com SIGPIPE
handle_sigpipe() {
    log_warning "Pipe quebrado detectado, continuando execução..."
    return 0
}

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Funções de log com buffer
log_info() { 
    echo -e "${BLUE}ℹ️  $1${NC}" >&2
    echo -e "${BLUE}ℹ️  $1${NC}" >> /tmp/scraper.log
}
log_success() { 
    echo -e "${GREEN}✅ $1${NC}" >&2
    echo -e "${GREEN}✅ $1${NC}" >> /tmp/scraper.log
}
log_warning() { 
    echo -e "${YELLOW}⚠️  $1${NC}" >&2
    echo -e "${YELLOW}⚠️  $1${NC}" >> /tmp/scraper.log
}
log_error() { 
    echo -e "${RED}❌ $1${NC}" >&2
    echo -e "${RED}❌ $1${NC}" >> /tmp/scraper.log
}

# Limpar arquivo de log anterior
> /tmp/scraper.log

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Executando scraper localmente..."

# Navegar para o diretório do scraper
cd backend/scraper

# Verificar e criar ambiente virtual se necessário
if [ ! -d "venv" ]; then
    log_info "Ambiente virtual não encontrado. Criando novo ambiente..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        log_error "Falha ao criar ambiente virtual. Certifique-se de que o python3-venv está instalado."
        log_warning "Execute: sudo apt-get install python3-venv"
        exit 1
    fi
    log_success "Ambiente virtual criado"
    
    # Ativar ambiente virtual
    source venv/bin/activate
    log_info "Ambiente virtual ativado"
    
    # Instalar dependências após criar o ambiente
    log_info "Instalando dependências do projeto..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        log_error "Falha ao instalar dependências"
        exit 1
    fi
    log_success "Dependências instaladas"
else
    # Ativar ambiente virtual existente
    source venv/bin/activate
    log_info "Ambiente virtual ativado"
    
    # Verificar se as dependências estão instaladas
    if ! pip list | grep -q "playwright"; then
        log_info "Dependências não encontradas. Instalando..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            log_error "Falha ao instalar dependências"
            exit 1
        fi
        log_success "Dependências instaladas"
    else
        log_info "Dependências já instaladas"
    fi
fi

# Verificar dependências do Playwright
log_info "Verificando dependências do Playwright..."
if ! playwright install-deps --dry-run &>/dev/null; then
    log_warning "Dependências do sistema para o Playwright não estão instaladas."
    log_warning "Execute o seguinte comando para instalar as dependências:"
    echo -e "${YELLOW}    sudo playwright install-deps${NC}" >&2
    echo -e "${YELLOW}    ou${NC}" >&2
    echo -e "${YELLOW}    sudo apt-get install libwoff1 libevent-2.1-7t64 libgstreamer-plugins-bad1.0-0 libavif16 libharfbuzz-icu0 libenchant-2-2 libhyphen0 libmanette-0.2-0${NC}" >&2
    exit 1
fi

# Verificar se os navegadores do Playwright estão instalados
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    log_warning "Navegadores do Playwright não estão instalados."
    log_info "Instalando navegadores do Playwright..."
    playwright install
fi

# Verificar conexão com Redis
log_info "Verificando conexão com Redis..."
if ! nc -z localhost 6379 &>/dev/null; then
    log_warning "Redis não está acessível em localhost:6379"
    log_info "Tentando iniciar o Redis..."
    
    # Voltar para o diretório raiz para executar docker-compose
    cd ../..
    
    # Verificar se o docker-compose está rodando
    if ! docker-compose ps | grep -q "redis"; then
        log_info "Iniciando Redis com docker-compose..."
        docker-compose up -d redis
        if [ $? -ne 0 ]; then
            log_error "Falha ao iniciar Redis"
            exit 1
        fi
        
        # Aguardar o Redis iniciar
        log_info "Aguardando Redis iniciar..."
        for i in {1..30}; do
            if nc -z localhost 6379 &>/dev/null; then
                log_success "Redis iniciado com sucesso"
                break
            fi
            if [ $i -eq 30 ]; then
                log_error "Timeout aguardando Redis iniciar"
                exit 1
            fi
            sleep 1
        done
    else
        log_error "Redis está listado no docker-compose mas não está acessível"
        log_warning "Tente reiniciar o Redis manualmente com: docker-compose restart redis"
        exit 1
    fi
    
    # Voltar para o diretório do scraper
    cd backend/scraper
fi

# Configurar variáveis de ambiente para ambiente local
export REDIS_HOST=localhost
export REDIS_PORT=6379
export ENVIRONMENT=local

# Carregar variáveis de ambiente do .env
if [ -f "../../.env" ]; then
    log_info "Carregando variáveis de ambiente..."
    # Preservar as variáveis locais
    local_redis_host=$REDIS_HOST
    local_redis_port=$REDIS_PORT
    local_environment=$ENVIRONMENT
    
    set -a
    source ../../.env
    set +a
    
    # Restaurar as variáveis locais
    export REDIS_HOST=$local_redis_host
    export REDIS_PORT=$local_redis_port
    export ENVIRONMENT=$local_environment
    
    log_info "Variáveis de ambiente carregadas"
    log_info "Redis configurado para: $REDIS_HOST:$REDIS_PORT"
else
    log_info "Arquivo .env não encontrado. Continuando com configurações locais..."
    log_info "Redis configurado para: $REDIS_HOST:$REDIS_PORT"
fi

# Executar scraper com tratamento de pipe
log_info "Iniciando scraper..."
python -m src.main "$@" 2>&1 | tee -a /tmp/scraper.log

# Verificar o código de saída do Python
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log_error "Scraper finalizado com erro"
    exit 1
fi

log_success "Scraper finalizado"
