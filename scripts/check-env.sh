#!/bin/bash

# setup_env.sh - Script para configurar variáveis de ambiente do Docker

echo "🔧 Configurando variáveis de ambiente para o Scraper..."

# Verifica se .env já existe
if [ -f ".env" ]; then
    echo "⚠️  Arquivo .env já existe. Fazendo backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Cria arquivo .env baseado nas variáveis do docker-compose
cat > .env << 'EOF'
WORK_MODE='development'
NODE_VERSION='22.15.0'

# ===========================================
# CONFIGURAÇÕES DA API
# ===========================================
API_CONTAINER_NAME='juscash-api'
API_HOST_PORT=8000
API_PORT=8000

# ===========================================
# CONFIGURAÇÕES DO FRONTEND - VITE
# ===========================================
VITE_CONTAINER_NAME='juscash-vite'
VITE_PORT=3008
VITE_HOST_PORT=3001
VITE_API_URL='http://$[API_CONTAINER_NAME]:${API_PORT}'

# ===========================================
# CONFIGURAÇÕES DOS BANCO DE DADOS
# ===========================================

# POSTGRESQL
POSTGRES_CONTAINER_NAME='justcash-postgres'
POSTGRES_USER='justcash_user'
POSTGRES_DB='justcash_db'
POSTGRES_PASSWORD='6IVxDUQkY9TUf5ij8Af3zIDhiTdgn'
POSTGRES_PORT=5432
POSTGRES_HOST_PORT=5433

# REDIS
REDIS_CONTAINER_NAME='juscash-redis'
REDIS_PASSWORD='do1HDF1uT5lC49VHuD2xom'
REDIS_PORT=6381
REDIS_HOST_PORT=6388
REDIS_URL='redis://${REDIS_CONTAINER_NAME}:${REDIS_PORT}'
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru
REDIS_SAVE_POLICY=60 1 300 100 600 1

# PRISMA
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER_NAME}:${POSTGRES_PORT}/${POSTGRES_DB}?schema=public&connection_limit=20"

# ===========================================
# CONFIGURAÇÕES DE E-MAIL
# ===========================================

# GOOGLE
MAIL_HOST='smtp.gmail.com'
MAIL_PORT='587'
MAIL_SECURE=false
MAIL_BOX_CONTACT=''
MAIL_BOX_BILLING=''
MAIL_USER=''
MAIL_PASS=''

# ===========================================
# CONFIGURAÇÕES DO SCRAPER
# ===========================================
SCRAPER_INTERVAL=86400
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5

# ===========================================
# CONFIGURAÇÕES DO BROWSER
# ===========================================
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
BROWSER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

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