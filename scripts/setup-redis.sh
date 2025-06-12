#!/bin/bash

# Script de configuração automática do Redis para o projeto JusCash
# Garante que o Redis funcione em qualquer ambiente

set -e  # Para execução em caso de erro

echo "🚀 Configurando Redis para o projeto JusCash..."

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

# Verificar se Docker está rodando
check_docker() {
    log_info "Verificando Docker..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker não está rodando. Por favor, inicie o Docker primeiro."
        exit 1
    fi
    log_success "Docker está rodando"
}

# Verificar se docker-compose existe
check_docker_compose() {
    log_info "Verificando Docker Compose..."
    if ! command -v docker-compose > /dev/null 2>&1; then
        log_error "Docker Compose não encontrado. Por favor, instale o Docker Compose."
        exit 1
    fi
    log_success "Docker Compose encontrado"
}

# Criar diretórios necessários
create_directories() {
    log_info "Criando diretórios necessários..."
    
    directories=(
        "database/redis/redis-data"
        "database/redis/logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "Diretório criado: $dir"
        else
            log_info "Diretório já existe: $dir"
        fi
    done
}

# Configurar permissões
setup_permissions() {
    log_info "Configurando permissões..."
    
    # ID do usuário Redis no container Bitnami
    REDIS_UID=1001
    REDIS_GID=1001
    
    directories=(
        "database/redis/redis-data"
        "database/redis/logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            # Tentar com sudo se necessário
            if ! chown -R $REDIS_UID:$REDIS_GID "$dir" 2>/dev/null; then
                log_warning "Permissões requerem sudo para: $dir"
                if command -v sudo > /dev/null 2>&1; then
                    sudo chown -R $REDIS_UID:$REDIS_GID "$dir"
                    log_success "Permissões configuradas com sudo: $dir"
                else
                    log_warning "Sudo não disponível. Tentando sem chown..."
                    chmod -R 755 "$dir" 2>/dev/null || true
                fi
            else
                log_success "Permissões configuradas: $dir"
            fi
            
            # Garantir permissões de escrita
            chmod -R 755 "$dir" 2>/dev/null || true
        fi
    done
}

# Verificar arquivos necessários do Redis
check_redis_files() {
    log_info "Verificando arquivos do Redis..."
    
    # Verificar Dockerfile
    if [ ! -f "database/redis/.docker/Dockerfile" ] && [ ! -f "database/redis/Dockerfile" ]; then
        log_warning "Dockerfile do Redis não encontrado. Criando..."
        
        mkdir -p database/redis/.docker
        
        cat > database/redis/.docker/Dockerfile << 'EOF'
FROM bitnami/redis:8.0.2

# Criar diretórios necessários e definir permissões
USER root
RUN mkdir -p /var/log/redis /var/lib/redis/data && \
    chown -R 1001:1001 /var/log/redis /var/lib/redis && \
    chmod -R 755 /var/log/redis /var/lib/redis

# Voltar para o usuário redis
USER 1001

EXPOSE ${REDIS_PORT}
EOF
        
        log_success "Dockerfile do Redis criado"
    else
        log_success "Dockerfile do Redis encontrado"
    fi
}

# Limpar containers e volumes antigos
cleanup_redis() {
    log_info "Limpando configurações antigas do Redis..."
    
    # Parar container se estiver rodando
    docker-compose stop redis 2>/dev/null || true
    
    # Remover container
    docker rm -f juscash-redis 2>/dev/null || true
    
    # Limpar dados antigos se tiverem permissões incorretas
    if [ -d "database/redis/redis-data" ]; then
        # Verificar se há arquivos com permissões incorretas
        if find database/redis/redis-data -type f ! -user $USER 2>/dev/null | grep -q .; then
            log_warning "Encontrados arquivos com permissões incorretas. Limpando..."
            if command -v sudo > /dev/null 2>&1; then
                sudo rm -rf database/redis/redis-data/*
            else
                rm -rf database/redis/redis-data/* 2>/dev/null || true
            fi
            log_success "Dados antigos removidos"
        fi
    fi
}

# Testar configuração do Redis
test_redis() {
    log_info "Testando configuração do Redis..."
    
    # Construir imagem
    log_info "Construindo imagem do Redis..."
    if ! docker-compose build redis; then
        log_error "Falha ao construir imagem do Redis"
        return 1
    fi
    
    # Iniciar Redis
    log_info "Iniciando Redis..."
    if ! docker-compose up -d redis; then
        log_error "Falha ao iniciar Redis"
        return 1
    fi
    
    # Aguardar inicialização
    log_info "Aguardando Redis inicializar..."
    sleep 10
    
    # Verificar se está rodando
    if ! docker-compose ps redis | grep -q "Up"; then
        log_error "Redis não está rodando corretamente"
        log_info "Logs do Redis:"
        docker-compose logs redis
        return 1
    fi
    
    # Testar conectividade
    log_info "Testando conectividade..."
    REDIS_PASSWORD=$(grep REDIS_PASSWORD .env | cut -d'=' -f2 | tr -d "'\"")
    REDIS_PORT=$(grep REDIS_PORT .env | cut -d'=' -f2 | tr -d "'\"")
    
    if docker exec juscash-redis redis-cli -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis respondendo ao ping"
        
        # Testar escrita/leitura
        if docker exec juscash-redis redis-cli -p "$REDIS_PORT" -a "$REDIS_PASSWORD" set test_setup "funcionando" >/dev/null 2>&1; then
            if [ "$(docker exec juscash-redis redis-cli -p "$REDIS_PORT" -a "$REDIS_PASSWORD" get test_setup 2>/dev/null)" = "funcionando" ]; then
                log_success "Teste de escrita/leitura OK"
                
                # Testar persistência
                if docker exec juscash-redis redis-cli -p "$REDIS_PORT" -a "$REDIS_PASSWORD" bgsave >/dev/null 2>&1; then
                    log_success "Teste de persistência OK"
                    
                    # Limpeza do teste
                    docker exec juscash-redis redis-cli -p "$REDIS_PORT" -a "$REDIS_PASSWORD" del test_setup >/dev/null 2>&1
                    
                    return 0
                else
                    log_error "Falha no teste de persistência"
                    return 1
                fi
            else
                log_error "Falha no teste de leitura"
                return 1
            fi
        else
            log_error "Falha no teste de escrita"
            return 1
        fi
    else
        log_error "Redis não responde ao ping"
        return 1
    fi
}

# Menu principal
main() {
    echo "🔧 Setup Redis - JusCash Project"
    echo "================================"
    
    check_docker
    check_docker_compose
    create_directories
    setup_permissions
    check_redis_files
    cleanup_redis
    
    if test_redis; then
        echo ""
        log_success "🎉 Redis configurado com sucesso!"
        log_info "Redis está rodando em: localhost:6383"
        log_info "Para parar: docker-compose stop redis"
        log_info "Para ver logs: docker-compose logs redis"
        echo ""
    else
        echo ""
        log_error "❌ Falha na configuração do Redis"
        log_info "Execute 'docker-compose logs redis' para mais detalhes"
        echo ""
        exit 1
    fi
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi