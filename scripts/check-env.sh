#!/bin/bash

# setup_env.sh - Script para configurar variáveis de ambiente do Docker

echo "🔧 Configurando variáveis de ambiente para o Scraper..."

# Verifica se .env já existe
if [ -f ".env" ]; then
    echo "⚠️  Arquivo .env já existe. Fazendo backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# ===========================================
# CONFIGURAÇÕES DA API
# ===========================================
API_CONTAINER_NAME="juscash-api"
API_HOST_PORT="8000"
API_PORT="8000"

# ===========================================
# CONFIGURAÇÕES DO FRONTEND - VITE
# ===========================================
VITE_CONTAINER_NAME="juscash-vite"
VITE_PORT="3008"
VITE_HOST_PORT="3001"
VITE_API_URL="http://${API_CONTAINER_NAME}:${API_PORT}"

# ===========================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ===========================================
# POSTGRESQL
POSTGRES_CONTAINER_NAME="juscash-postgres"
POSTGRES_USER="juscash_user"
POSTGRES_DB="juscash_db"
POSTGRES_PASSWORD="6IVxDUQkY9TUf5ij8Af3zIDhiTdgn"
POSTGRES_PORT="5432"
POSTGRES_HOST_PORT="5433"
POSTGRES_URL_ASYNC="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER_NAME}:${POSTGRES_PORT}/${POSTGRES_DB}"

# REDIS
REDIS_CONTAINER_NAME="juscash-redis"
REDIS_PASSWORD="do1HDF1uT5lC49VHuD2xom"
REDIS_PORT="6379"
REDIS_HOST_PORT="6379"
REDIS_URL="redis://${REDIS_CONTAINER_NAME}:${REDIS_PORT}"

# PRISMA
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER_NAME}:${POSTGRES_PORT}/${POSTGRES_DB}?schema=public&connection_limit=20"

# Cria arquivo .env baseado nas variáveis do docker-compose
cat > .env << EOF
WORK_MODE='development'
NODE_VERSION='22.15.0'

# ===========================================
# CONFIGURAÇÕES DA API
# ===========================================
API_CONTAINER_NAME='${API_CONTAINER_NAME}'
API_HOST_PORT=${API_HOST_PORT}
API_PORT=${API_PORT}
API_TIMEOUT=30
API_BASE_URL='http://${API_CONTAINER_NAME}:${API_PORT}'

# Configurações de segurança e limites
CORS_ORIGIN=''
JWT_ACCESS_SECRET='fUXZOvvcAit2HcrAcXsaY3AnZ5PihzyL'
JWT_REFRESH_SECRET='FjOkrtGSfalZaPdfyNJEynzYrGmZFRdW'
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
MAX_REQUEST_SIZE='10mb'

# Configurações adicionais
ENABLE_SECURITY_MIDDLEWARE=true
ENABLE_METRICS=false
METRICS_PATH='/admin/metrics'
ENABLE_FILE_LOGGING=true

# ===========================================
# CONFIGURAÇÕES DO FRONTEND - VITE
# ===========================================
VITE_CONTAINER_NAME='${VITE_CONTAINER_NAME}'
VITE_PORT=${VITE_PORT}
VITE_HOST_PORT=${VITE_HOST_PORT}
VITE_API_URL='${VITE_API_URL}'

# ===========================================
# CONFIGURAÇÕES DOS BANCO DE DADOS
# ===========================================
# POSTGRESQL
POSTGRES_CONTAINER_NAME='${POSTGRES_CONTAINER_NAME}'
POSTGRES_USER='${POSTGRES_USER}'
POSTGRES_DB='${POSTGRES_DB}'
POSTGRES_PASSWORD='${POSTGRES_PASSWORD}'
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_HOST_PORT=${POSTGRES_HOST_PORT}
POSTGRES_URL_ASYNC='${POSTGRES_URL_ASYNC}'

# PRISMA
DATABASE_URL='${DATABASE_URL}'

# REDIS
REDIS_CONTAINER_NAME='${REDIS_CONTAINER_NAME}'
REDIS_PASSWORD='${REDIS_PASSWORD}'
REDIS_PORT=${REDIS_PORT}
REDIS_HOST_PORT=${REDIS_HOST_PORT}
REDIS_URL='${REDIS_URL}'
REDIS_MAXMEMORY='2gb'
REDIS_MAXMEMORY_POLICY='allkeys-lru'
REDIS_SAVE_POLICY='60 1 300 100 600 1'

# ===========================================
# CONFIGURAÇÕES DE E-MAIL
# ===========================================

# GOOGLE
MAIL_PORT='587'
MAIL_SECURE=false
MAIL_BOX_CONTACT='contato@juniormartins.dev'
MAIL_BOX_BILLING='contato@juniormartins.dev'
MAIL_USER='contato@juniormartins.dev'
MAIL_PASS='juniormartins@123'
MAIL_HOST='smtp.gmail.com'

# ===========================================
# CONFIGURAÇÕES DO SCRAPER
# ===========================================
SCRAPER_CONTAINER_NAME='juscash-scraper'
SCRAPER_INTERVAL=86400
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5
SCRAPER_MAX_PAGES=20
SCRAPER_TARGET_URL=https://dje.tjsp.jus.br/cdje/index.do
SCRAPER_SEARCH_TERMS=aposentadoria,benefício,INSS
SCRAPER_API_KEY='scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP'

# Configurações do navegador
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30000
BROWSER_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

# ===========================================
# CONFIGURAÇÕES DE LOG
# ===========================================
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_ROTATION_DAYS=7
LOG_MAX_SIZE_MB=10

EOF

echo "✅ Arquivo .env criado com sucesso!"
echo ""
echo "📋 Configurações aplicadas:"
echo ""
echo "🐳 Para iniciar o ambiente Docker:"
echo "   docker-compose up --build"
echo ""
echo "🔍 Para verificar logs do scraper:"
echo "   docker-compose logs -f scraper"
echo ""
echo "🧪 Para executar testes so scraper:"
echo "   docker-compose exec scraper python -m pytest tests/ -v"
echo ""
echo "🔍 Para verificar logs do vite:"
echo "   docker-compose logs -f vite"
echo ""
echo "🔍 Para verificar logs do api:"
echo "   docker-compose logs -f api"
echo ""
echo "🔍 Para verificar logs do postgres:"
echo "   docker-compose logs -f postgres"
echo ""