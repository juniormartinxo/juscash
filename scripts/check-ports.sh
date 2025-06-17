#!/bin/bash

# check-ports.sh - Script para verificar se as portas estão ocupadas
# Verifica todas as portas configuradas no arquivo .env

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
echo "🔍 JusCash - Verificação de Portas"
echo "=================================="
echo ""

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    log_error "Arquivo .env não encontrado!"
    log_info "Execute primeiro: ./scripts/check-env.sh"
    exit 1
fi

log_info "Carregando configurações do arquivo .env..."

# Carregar variáveis do arquivo .env de forma mais segura
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

# Lista de portas para verificar com suas descrições
declare -A PORTS_TO_CHECK=(
    ["$API_HOST_PORT"]="API Backend"
    ["$VITE_HOST_PORT"]="Frontend Vite"
    ["$POSTGRES_HOST_PORT"]="PostgreSQL Database"
    ["$REDIS_HOST_PORT"]="Redis Cache"
    ["$SCRAPER_API_PORT"]="Scraper API"
)

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    local service=$2
    
    if [ -z "$port" ]; then
        log_warning "Porta não definida para: $service"
        return 1
    fi
    
    # Verificar se a porta está em uso usando netstat ou ss
    if command -v netstat > /dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            return 0  # Porta em uso
        fi
    elif command -v ss > /dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            return 0  # Porta em uso
        fi
    elif command -v lsof > /dev/null 2>&1; then
        if lsof -i :$port > /dev/null 2>&1; then
            return 0  # Porta em uso
        fi
    else
        log_warning "Nenhum comando de verificação de porta disponível (netstat, ss, lsof)"
        return 2  # Não foi possível verificar
    fi
    
    return 1  # Porta livre
}

# Função para obter informações sobre o processo que está usando a porta
get_port_info() {
    local port=$1
    
    if command -v lsof > /dev/null 2>&1; then
        echo "$(lsof -i :$port 2>/dev/null | tail -n +2 | head -1)"
    elif command -v netstat > /dev/null 2>&1; then
        echo "$(netstat -tulnp 2>/dev/null | grep ":$port " | head -1)"
    elif command -v ss > /dev/null 2>&1; then
        echo "$(ss -tulnp 2>/dev/null | grep ":$port " | head -1)"
    else
        echo "Informações não disponíveis"
    fi
}

# Função para sugerir soluções
suggest_solution() {
    local port=$1
    local service=$2
    local process_info=$3
    
    echo ""
    log_info "💡 Sugestões para resolver o conflito na porta $port ($service):"
    echo ""
    echo "   1️⃣  Parar o serviço que está usando a porta:"
    
    if echo "$process_info" | grep -q "docker"; then
        echo "      docker stop \$(docker ps -q --filter publish=$port)"
        echo "      # ou"
        echo "      docker-compose down"
    elif echo "$process_info" | grep -qE "(node|npm|yarn|pnpm)"; then
        echo "      # Encontrar e parar processo Node.js"
        echo "      pkill -f node"
        echo "      # ou encontrar PID específico"
        echo "      lsof -ti:$port | xargs kill -9"
    else
        echo "      # Parar processo usando a porta"
        echo "      lsof -ti:$port | xargs kill -9"
    fi
    
    echo ""
    echo "   2️⃣  Alterar a porta no arquivo .env:"
    echo "      # Editar .env e alterar a variável da porta"
    echo "      nano .env"
    echo ""
    echo "   3️⃣  Usar porta alternativa temporariamente:"
    echo "      # Exportar nova porta antes de iniciar"
    # Extrair nome da variável do serviço
    service_var=$(echo "$service" | tr '[:lower:]' '[:upper:]' | tr ' ' '_')
    echo "      export ${service_var}_HOST_PORT=$((port + 1000))"
    echo ""
}

# Verificação principal
echo ""
log_info "Verificando portas configuradas..."
echo ""

ports_in_use=0
total_ports=0

for port in "${!PORTS_TO_CHECK[@]}"; do
    service="${PORTS_TO_CHECK[$port]}"
    total_ports=$((total_ports + 1))
    
    if [ -z "$port" ] || [ "$port" = "" ]; then
        log_warning "Porta não definida para: $service"
        continue
    fi
    
    printf "%-25s (porta %s): " "$service" "$port"
    
    check_result=$(check_port "$port" "$service"; echo $?)
    
    case $check_result in
        0)  # Porta em uso
            echo -e "${RED}EM USO ❌${NC}"
            ports_in_use=$((ports_in_use + 1))
            
            # Obter informações do processo
            process_info=$(get_port_info "$port")
            if [ -n "$process_info" ] && [ "$process_info" != "Informações não disponíveis" ]; then
                echo "      💻 Processo: $process_info"
            fi
            
            suggest_solution "$port" "$service" "$process_info"
            ;;
        1)  # Porta livre
            echo -e "${GREEN}LIVRE ✅${NC}"
            ;;
        2)  # Não foi possível verificar
            echo -e "${YELLOW}NÃO VERIFICADA ⚠️${NC}"
            ;;
    esac
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Resumo final
if [ $ports_in_use -eq 0 ]; then
    log_success "🎉 Todas as portas estão livres! Você pode iniciar o projeto."
    echo ""
    log_info "Para iniciar todos os serviços:"
    echo "   docker-compose up --build"
else
    log_error "⚠️  $ports_in_use de $total_ports portas estão em uso!"
    echo ""
    log_info "Resolva os conflitos de porta antes de iniciar o projeto."
    echo ""
    log_info "Após resolver os conflitos, execute novamente:"
    echo "   ./scripts/check-ports.sh"
    echo ""
    log_info "Ou force a parada de todos os containers Docker:"
    echo "   docker-compose down"
    echo "   docker stop \$(docker ps -aq) 2>/dev/null || true"
fi

echo ""

# Código de saída baseado no resultado
exit $ports_in_use 