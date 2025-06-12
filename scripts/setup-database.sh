#!/bin/bash

# setup-database.sh - Script para configurar o banco de dados via Prisma
# Verifica se containers estão rodando e executa comandos do Prisma no container da API

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
echo "🗄️ JusCash - Configuração do Banco de Dados"
echo "============================================"
echo ""

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    log_error "Arquivo .env não encontrado!"
    log_info "Execute primeiro: ./scripts/check-env.sh"
    exit 1
fi

# Carregar variáveis do arquivo .env
log_info "Carregando configurações do arquivo .env..."
set -a  # Export automaticamente todas as variáveis
while IFS='=' read -r key value; do
    # Ignorar linhas vazias e comentários
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    
    # Remover aspas simples e duplas do valor
    value=$(echo "$value" | sed "s/^['\"]//g; s/['\"]$//g")
    
    # Exportar a variável
    export "$key"="$value"
done < <(grep -v '^#' .env | grep -v '^$')
set +a  # Desabilitar export automático

# Verificar se Docker está rodando
check_docker() {
    log_info "Verificando se Docker está rodando..."
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

# Função para verificar se um container está rodando
check_container_running() {
    local container_name=$1
    local service_name=$2
    
    log_info "Verificando container: $container_name ($service_name)..."
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        log_success "Container $container_name está rodando"
        return 0
    else
        log_warning "Container $container_name não está rodando"
        return 1
    fi
}

# Função para verificar se o container está saudável
check_container_health() {
    local container_name=$1
    local service_name=$2
    
    # Verificar se o container tem healthcheck configurado
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
    
    if [ "$health_status" = "healthy" ]; then
        log_success "Container $container_name está saudável"
        return 0
    elif [ "$health_status" = "unhealthy" ]; then
        # Para PostgreSQL, vamos tentar uma conexão direta mesmo se unhealthy
        if [[ "$service_name" == "PostgreSQL" ]]; then
            log_warning "Container $container_name está marcado como não saudável, mas tentando conexão direta..."
            # Tentar conectar ao PostgreSQL para verificar se está realmente funcionando
            if docker exec "$container_name" pg_isready -U "juscash_user" -d "juscash_db" > /dev/null 2>&1; then
                log_success "PostgreSQL está respondendo apesar do status unhealthy"
                return 0
            else
                log_warning "PostgreSQL não está respondendo"
                return 1
            fi
        else
            log_warning "Container $container_name não está saudável"
            return 1
        fi
    elif [ "$health_status" = "starting" ]; then
        log_info "Container $container_name ainda está inicializando..."
        return 2
    else
        # Para containers sem healthcheck, verificar se estão funcionalmente prontos
        if [[ "$service_name" == "API" ]]; then
            # Verificar se o processo da API está rodando
            if docker exec "$container_name" pgrep -f "tsx" > /dev/null 2>&1; then
                log_success "Processo da API está rodando"
                return 0
            else
                log_warning "Processo da API ainda não está rodando"
                return 1
            fi
        else
            log_info "Container $container_name não tem healthcheck configurado"
            return 0
        fi
    fi
}

# Função específica para verificar se PostgreSQL está pronto
check_postgres_ready() {
    local container_name=$1
    local max_attempts=10
    local attempt=1
    
    log_info "Verificando se PostgreSQL está pronto para conexões..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec "$container_name" pg_isready -U "juscash_user" -d "juscash_db" > /dev/null 2>&1; then
            log_success "PostgreSQL está pronto para conexões!"
            return 0
        fi
        
        log_info "PostgreSQL ainda não está pronto (tentativa $attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL não ficou pronto a tempo"
    return 1
}

# Função específica para verificar se API está pronta
check_api_ready() {
    local container_name=$1
    local max_attempts=10
    local attempt=1
    
    log_info "Verificando se API está pronta para comandos..."
    
    while [ $attempt -le $max_attempts ]; do
        # Verificar se o processo Node.js está rodando e escutando na porta
        if docker exec "$container_name" netstat -tlnp 2>/dev/null | grep -q ":${API_PORT:-8000} " 2>/dev/null; then
            log_success "API está escutando na porta e pronta!"
            return 0
        fi
        
        # Alternativa: verificar se o processo tsx está rodando
        if docker exec "$container_name" pgrep -f "tsx" > /dev/null 2>&1; then
            log_success "Processo da API está rodando!"
            return 0
        fi
        
        log_info "API ainda não está pronta (tentativa $attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log_error "API não ficou pronta a tempo"
    return 1
}

# Função para aguardar container estar pronto
wait_for_container() {
    local container_name=$1
    local service_name=$2
    local max_attempts=20  # Tempo razoável para containers iniciarem
    local attempt=1
    
    log_info "Aguardando container $container_name estar pronto..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_container_running "$container_name" "$service_name" > /dev/null 2>&1; then
            # Verificar saúde se aplicável
            health_result=$(check_container_health "$container_name" "$service_name"; echo $?)
            
            case $health_result in
                0)  # Saudável ou funcionalmente pronto
                    log_success "Container $container_name está pronto!"
                    return 0
                    ;;
                1)  # Não saudável
                    log_warning "Container $container_name não está saudável (tentativa $attempt/$max_attempts)"
                    ;;
                2)  # Ainda inicializando
                    log_info "Container $container_name ainda inicializando (tentativa $attempt/$max_attempts)"
                    ;;
            esac
        else
            log_warning "Container $container_name não está rodando (tentativa $attempt/$max_attempts)"
        fi
        
        sleep 3  # Reduzido para verificações mais frequentes
        attempt=$((attempt + 1))
    done
    
    log_error "Timeout aguardando container $container_name ficar pronto"
    return 1
}

# Função para executar comandos Prisma no container da API
execute_prisma_commands() {
    local api_container=$1
    
    log_info "Executando comandos do Prisma no container da API..."
    echo ""
    
    # Comando 1: npx prisma generate
    log_info "🔧 Executando: npx prisma generate"
    if docker-compose exec -T "$api_container" npx prisma generate; then
        log_success "Prisma generate executado com sucesso!"
    else
        log_error "Falha ao executar prisma generate"
        return 1
    fi
    
    echo ""
    
    # Comando 2: npx prisma migrate dev
    log_info "🔧 Executando: npx prisma migrate dev"
    if docker-compose exec -T "$api_container" npx prisma migrate dev --name init; then
        log_success "Prisma migrate dev executado com sucesso!"
    else
        log_error "Falha ao executar prisma migrate dev"
        return 1
    fi
    
    echo ""
    
    # Comando 3: npx prisma db seed
    log_info "🔧 Executando: npx prisma db seed"
    if docker-compose exec -T "$api_container" npx prisma db seed; then
        log_success "Prisma db seed executado com sucesso!"
    else
        log_warning "Falha ao executar prisma db seed (pode ser normal se não houver script de seed)"
        log_info "Continuando com a configuração..."
    fi
    
    return 0
}

# Função principal
main() {
    check_docker
    check_docker_compose
    
    echo ""
    log_info "Verificando status dos containers necessários..."
    echo ""
    
    # Definir nomes dos containers a partir das variáveis do .env
    API_CONTAINER=${API_CONTAINER_NAME:-"juscash-api"}
    POSTGRES_CONTAINER=${POSTGRES_CONTAINER_NAME:-"juscashh-postgres"}
    
    # Debug: mostrar nomes dos containers que serão verificados
    log_info "Containers a serem verificados:"
    log_info "  - API: $API_CONTAINER"
    log_info "  - PostgreSQL: $POSTGRES_CONTAINER"
    
    # Verificar se os containers estão rodando
    api_running=false
    postgres_running=false
    
    if check_container_running "$API_CONTAINER" "API"; then
        api_running=true
    fi
    
    if check_container_running "$POSTGRES_CONTAINER" "PostgreSQL"; then
        postgres_running=true
    fi
    
    echo ""
    
    # Se ambos os containers não estão rodando, tentar iniciar
    if [ "$api_running" = false ] || [ "$postgres_running" = false ]; then
        log_warning "Nem todos os containers necessários estão rodando"
        log_info "Tentando iniciar os containers..."
        
        if docker-compose up -d api postgres; then
            log_success "Containers iniciados com docker-compose"
            
            # Aguardar um pouco para containers iniciarem
            sleep 5
            
            # Verificar PostgreSQL diretamente
            if ! check_postgres_ready "$POSTGRES_CONTAINER"; then
                log_error "PostgreSQL não está respondendo adequadamente"
                exit 1
            fi
            
            # Verificar API diretamente
            if ! check_api_ready "$API_CONTAINER"; then
                log_error "API não está respondendo adequadamente"
                exit 1
            fi
        else
            log_error "Falha ao iniciar containers com docker-compose"
            exit 1
        fi
    else
        log_success "Todos os containers necessários estão rodando!"
        
        # Verificação direta se PostgreSQL está realmente pronto
        if ! check_postgres_ready "$POSTGRES_CONTAINER"; then
            log_error "PostgreSQL não está respondendo adequadamente"
            exit 1
        fi
        
        # Verificação direta se API está realmente pronta
        if ! check_api_ready "$API_CONTAINER"; then
            log_error "API não está respondendo adequadamente"
            exit 1
        fi
    fi
    
    echo ""
    
    # Aguardar um pouco mais para garantir que o PostgreSQL está totalmente pronto
    log_info "Aguardando conexão com banco de dados estabilizar..."
    sleep 5
    
    # Executar comandos do Prisma
    if execute_prisma_commands "api"; then
        echo ""
        log_success "🎉 Configuração do banco de dados concluída com sucesso!"
        echo ""
        log_info "📋 Próximos passos:"
        echo ""
        echo "🔍 Para verificar as tabelas criadas:"
        echo "   docker-compose exec api npx prisma studio"
        echo ""
        echo "🗄️ Para acessar o banco PostgreSQL diretamente:"
        echo "   docker-compose exec postgres psql -U \$POSTGRES_USER -d \$POSTGRES_DB"
        echo ""
        echo "🔄 Para executar migrações futuras:"
        echo "   docker-compose exec api npx prisma migrate dev"
        echo ""
    else
        log_error "Falha na configuração do banco de dados"
        exit 1
    fi
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 