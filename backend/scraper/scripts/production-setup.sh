#!/bin/bash

# Script de configuração para ambiente de produção
# DJE Scraper - Sistema de Web Scraping

set -e  # Sair em caso de erro

echo "🚀 Configurando DJE Scraper para Produção"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se é root
if [[ $EUID -eq 0 ]]; then
   log_error "Este script não deve ser executado como root"
   exit 1
fi

# Verificar Python 3.12+
log_info "Verificando Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.12"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
    log_success "Python $python_version OK"
else
    log_error "Python 3.12+ é obrigatório. Versão atual: $python_version"
    exit 1
fi

# Verificar Node.js (para API)
log_info "Verificando Node.js..."
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version)
    log_success "Node.js $node_version OK"
else
    log_warning "Node.js não encontrado - necessário para API"
fi

# Verificar Docker
log_info "Verificando Docker..."
if command -v docker >/dev/null 2>&1; then
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    log_success "Docker $docker_version OK"
else
    log_error "Docker é obrigatório para produção"
    exit 1
fi

# Verificar Docker Compose
log_info "Verificando Docker Compose..."
if command -v docker-compose >/dev/null 2>&1; then
    compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    log_success "Docker Compose $compose_version OK"
else
    log_error "Docker Compose é obrigatório"
    exit 1
fi

# Criar estrutura de diretórios
log_info "Criando estrutura de diretórios..."
mkdir -p {config,logs,backups,data,scripts,docs}
mkdir -p backups/{publications,executions,logs}
mkdir -p data/{temp,cache}
log_success "Estrutura de diretórios criada"

# Configurar arquivo .env para produção
log_info "Configurando ambiente de produção..."

if [ ! -f ".env" ]; then
    log_info "Criando arquivo .env..."
    
    # Gerar API Key segura
    api_key="scraper_$(date +%Y)_$(openssl rand -hex 32)"
    
    cat > .env << EOF
# ==========================================
# DJE Scraper - Configuração de Produção
# ==========================================
ENVIRONMENT=production

# API Configuration
API_BASE_URL=http://localhost:8000
SCRAPER_API_KEY=$api_key
API_TIMEOUT=60

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=45000
BROWSER_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36

# Scraper Configuration
SCRAPER_TARGET_URL=https://dje.tjsp.jus.br/cdje/index.do
SCRAPER_MAX_RETRIES=5
SCRAPER_RETRY_DELAY=10
SCRAPER_MAX_PAGES=50
SCRAPER_SEARCH_TERMS=aposentadoria,benefício,INSS,previdenciário

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_ROTATION_DAYS=30
LOG_MAX_SIZE_MB=50

# Performance
SCRAPER_DELAY_BETWEEN_PAGES=3
SCRAPER_DELAY_BETWEEN_REQUESTS=2
SCRAPER_MAX_CONCURRENT_PAGES=2

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=90
BACKUP_COMPRESS=true

# Monitoring
ENABLE_METRICS=true
ENABLE_ALERTS=true
HEALTH_CHECK_INTERVAL=300

# Email Alerts (configurar se necessário)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASS=
# ALERT_EMAILS=admin@empresa.com
EOF
    
    log_success "Arquivo .env criado com API Key: ${api_key:0:20}..."
else
    log_warning "Arquivo .env já existe - não sobrescrevendo"
fi

# Instalar dependências Python
log_info "Instalando dependências Python..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user -r requirements.txt
    log_success "Dependências Python instaladas"
else
    log_warning "requirements.txt não encontrado"
fi

# Instalar browsers do Playwright
log_info "Instalando browsers do Playwright..."
python3 -m playwright install chromium --with-deps
log_success "Browsers do Playwright instalados"

# Configurar systemd service
log_info "Configurando serviço systemd..."

sudo tee /etc/systemd/system/dje-scraper.service > /dev/null << EOF
[Unit]
Description=DJE Scraper Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(which python3):$PATH
ExecStart=$(which python3) src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dje-scraper

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$(pwd)/logs $(pwd)/backups $(pwd)/data

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
log_success "Serviço systemd configurado"

# Configurar logrotate
log_info "Configurando rotação de logs..."
sudo tee /etc/logrotate.d/dje-scraper > /dev/null << EOF
$(pwd)/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload dje-scraper || true
    endscript
}
EOF

log_success "Rotação de logs configurada"

# Configurar cron para backup
log_info "Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && python3 scraper_cli.py backup logs --days-back 1") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * 0 cd $(pwd) && python3 scraper_cli.py backup cleanup --retention-days 90") | crontab -
log_success "Backup automático configurado"

# Configurar monitoramento
log_info "Configurando monitoramento..."
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check script para monitoramento externo

cd "$(dirname "$0")/.."
python3 scraper_cli.py test api --api-url http://localhost:8000

if [ $? -eq 0 ]; then
    echo "OK: Scraper funcionando"
    exit 0
else
    echo "CRITICAL: Scraper com problemas"
    exit 2
fi
EOF

chmod +x scripts/health_check.sh
log_success "Script de health check criado"

# Configurar firewall (UFW)
log_info "Configurando firewall..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow ssh
    sudo ufw allow 8000/tcp  # API
    sudo ufw --force enable
    log_success "Firewall configurado"
else
    log_warning "UFW não encontrado - configure firewall manualmente"
fi

# Otimizações de sistema
log_info "Aplicando otimizações de sistema..."

# Aumentar limites de arquivo
echo "$USER soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "$USER hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Otimizações de rede
sudo tee -a /etc/sysctl.conf > /dev/null << EOF

# DJE Scraper optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_window_scaling = 1
EOF

sudo sysctl -p
log_success "Otimizações aplicadas"

# Teste de configuração
log_info "Testando configuração..."
python3 scraper_cli.py config show > /dev/null
if [ $? -eq 0 ]; then
    log_success "Configuração válida"
else
    log_error "Problema na configuração"
    exit 1
fi

# Instruções finais
echo ""
echo "🎉 Configuração de produção concluída!"
echo "======================================"
echo ""
echo "📋 Próximos passos:"
echo "1. Configurar a API JusCash (se ainda não estiver rodando)"
echo "2. Ajustar SCRAPER_API_KEY na API para: $api_key"
echo "3. Iniciar o serviço: sudo systemctl start dje-scraper"
echo "4. Habilitar auto-start: sudo systemctl enable dje-scraper"
echo "5. Verificar logs: journalctl -fu dje-scraper"
echo ""
echo "🔧 Comandos úteis:"
echo "   Status:    sudo systemctl status dje-scraper"
echo "   Parar:     sudo systemctl stop dje-scraper"
echo "   Reiniciar: sudo systemctl restart dje-scraper"
echo "   Logs:      journalctl -fu dje-scraper"
echo "   Health:    ./scripts/health_check.sh"
echo ""
echo "📊 Monitoramento:"
echo "   Health Check: http://localhost:8000/health"
echo "   CLI Status:   python3 scraper_cli.py status"
echo "   Alertas:      python3 scraper_cli.py alerts list"