#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para imprimir mensagens
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar se o Redis está rodando
if ! docker ps | grep -q "juscash-redis"; then
    print_error "Container do Redis não está rodando"
    exit 1
fi

# Verificar conexão com Redis
print_message "Verificando conexão com Redis..."
if ! docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; then
    print_error "Não foi possível conectar ao Redis"
    exit 1
fi

# Verificar configurações do Redis
print_message "Verificando configurações do Redis..."
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config get timeout
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config get tcp-keepalive
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config get maxclients

# Verificar uso de memória
print_message "Verificando uso de memória do Redis..."
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" info memory

# Verificar conexões ativas
print_message "Verificando conexões ativas..."
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" info clients

# Verificar filas
print_message "Verificando filas..."
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" keys "*queue*"

# Ajustar configurações se necessário
print_message "Ajustando configurações do Redis..."
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config set timeout 300
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config set tcp-keepalive 60
docker exec juscash-redis redis-cli -a "${REDIS_PASSWORD}" config set maxclients 10000

print_message "Configurações do Redis ajustadas com sucesso!" 