#!/bin/bash

# install-scraper.sh - Script de instalação do Scraper DJE
# Configura ambiente Python, dependências e testa a instalação

set -e  # Para execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔧 $1${NC}"; }
log_cmd() { echo -e "${CYAN}💻 $1${NC}"; }

# Banner de início
echo "🐍 JusCash - Instalação do Scraper DJE"
echo "======================================"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml não encontrado. Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

# Verificar se a pasta do scraper existe
if [ ! -d "backend/scraper" ]; then
    log_error "Pasta 'backend/scraper' não encontrada."
    exit 1
fi

log_info "Iniciando instalação do Scraper DJE..."
echo ""

# Função para verificar se um comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para verificar versão do Python
check_python_version() {
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | awk '{print $2}')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
            log_success "Python $version encontrado"
            return 0
        else
            log_error "Python 3.8+ é necessário. Versão encontrada: $version"
            return 1
        fi
    else
        log_error "Python3 não encontrado"
        return 1
    fi
}

# Função para instalar dependências do sistema
install_system_dependencies() {
    log_step "Passo 1/7: Verificando dependências do sistema..."
    
    # Detectar sistema operacional
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            log_info "Sistema Ubuntu/Debian detectado"
            log_cmd "Atualizando lista de pacotes..."
            sudo apt-get update -qq
            
            log_cmd "Instalando dependências do sistema..."
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                wget \
                curl \
                git \
                libnss3-dev \
                libatk-bridge2.0-dev \
                libdrm-dev \
                libxcomposite-dev \
                libxdamage-dev \
                libxrandr-dev \
                libgbm-dev \
                libxss-dev \
                libasound2-dev
                
        elif command_exists yum; then
            log_info "Sistema RedHat/CentOS detectado"
            log_cmd "Instalando dependências do sistema..."
            sudo yum install -y \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                wget \
                curl \
                git
        else
            log_warning "Gerenciador de pacotes não reconhecido. Instale manualmente: python3, python3-pip, python3-venv, build-essential"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        log_info "Sistema macOS detectado"
        if command_exists brew; then
            log_cmd "Instalando dependências via Homebrew..."
            brew install python3 wget curl git
        else
            log_warning "Homebrew não encontrado. Instale manualmente: python3, wget, curl, git"
        fi
    else
        log_warning "Sistema operacional não reconhecido: $OSTYPE"
    fi
    
    log_success "Dependências do sistema verificadas"
}

# Função para verificar e configurar Python
setup_python_environment() {
    log_step "Passo 2/7: Configurando ambiente Python..."
    
    # Verificar versão do Python
    if ! check_python_version; then
        log_error "Python 3.8+ é necessário para o scraper"
        exit 1
    fi
    
    # Navegar para o diretório do scraper
    cd backend/scraper
    
    # Criar ambiente virtual se não existir
    if [ ! -d "venv" ]; then
        log_cmd "Criando ambiente virtual Python..."
        python3 -m venv venv
        log_success "Ambiente virtual criado"
    else
        log_info "Ambiente virtual já existe"
    fi
    
    # Ativar ambiente virtual
    log_cmd "Ativando ambiente virtual..."
    source venv/bin/activate
    
    # Atualizar pip
    log_cmd "Atualizando pip..."
    pip install --upgrade pip
    
    log_success "Ambiente Python configurado"
}

# Função para instalar dependências Python
install_python_dependencies() {
    log_step "Passo 3/7: Instalando dependências Python..."
    
    # Verificar se requirements.txt existe
    if [ ! -f "requirements.txt" ]; then
        log_error "Arquivo requirements.txt não encontrado"
        exit 1
    fi
    
    log_cmd "Instalando dependências do requirements.txt..."
    pip install -r requirements.txt
    
    log_success "Dependências Python instaladas"
}

# Função para configurar Playwright
setup_playwright() {
    log_step "Passo 4/7: Configurando Playwright..."
    
    log_cmd "Instalando browsers do Playwright..."
    python -m playwright install chromium
    
    log_cmd "Instalando dependências do sistema para Playwright..."
    python -m playwright install-deps chromium
    
    log_success "Playwright configurado"
}

# Função para configurar variáveis de ambiente
setup_environment_variables() {
    log_step "Passo 5/7: Configurando variáveis de ambiente..."
    
    # Voltar para o diretório raiz
    cd ../..
    
    # Verificar se .env existe
    if [ ! -f ".env" ]; then
        log_warning "Arquivo .env não encontrado"
        
        # Verificar se existe .env.example
        if [ -f ".env.example" ]; then
            log_cmd "Copiando .env.example para .env..."
            cp .env.example .env
            log_warning "Configure as variáveis de ambiente no arquivo .env antes de executar o scraper"
        else
            log_error "Arquivo .env.example não encontrado. Crie um arquivo .env com as configurações necessárias."
            exit 1
        fi
    else
        log_success "Arquivo .env encontrado"
    fi
    
    # Verificar variáveis específicas do scraper
    log_info "Verificando variáveis de ambiente do scraper..."
    
    required_vars=(
        "POSTGRES_URL_ASYNC"
        "REDIS_URL"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warning "Variáveis de ambiente faltando no .env:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_warning "Configure essas variáveis antes de executar o scraper"
    else
        log_success "Variáveis de ambiente do scraper configuradas"
    fi
}

# Função para testar a instalação
test_installation() {
    log_step "Passo 6/7: Testando instalação..."
    
    # Navegar para o diretório do scraper
    cd backend/scraper
    
    # Ativar ambiente virtual
    source venv/bin/activate
    
    # Testar importações básicas
    log_cmd "Testando importações Python..."
    python -c "
import sys
print(f'Python: {sys.version}')

try:
    import asyncio
    print('✅ asyncio: OK')
except ImportError as e:
    print(f'❌ asyncio: {e}')

try:
    import playwright
    print('✅ playwright: OK')
except ImportError as e:
    print(f'❌ playwright: {e}')

try:
    import sqlalchemy
    print('✅ sqlalchemy: OK')
except ImportError as e:
    print(f'❌ sqlalchemy: {e}')

try:
    import redis
    print('✅ redis: OK')
except ImportError as e:
    print(f'❌ redis: {e}')

try:
    import loguru
    print('✅ loguru: OK')
except ImportError as e:
    print(f'❌ loguru: {e}')

try:
    import beautifulsoup4
    print('✅ beautifulsoup4: OK')
except ImportError as e:
    print(f'❌ beautifulsoup4: {e}')
"
    
    # Testar estrutura do projeto
    log_cmd "Verificando estrutura do projeto..."
    
    required_files=(
        "src/main.py"
        "src/__init__.py"
        "src/config"
        "src/core"
        "src/adapters"
        "src/shared"
    )
    
    for file in "${required_files[@]}"; do
        if [ -e "$file" ]; then
            log_success "Encontrado: $file"
        else
            log_error "Não encontrado: $file"
        fi
    done
    
    # Voltar para o diretório raiz
    cd ../..
    
    log_success "Testes de instalação concluídos"
}

# Função para criar scripts de execução
create_execution_scripts() {
    log_step "Passo 7/7: Criando scripts de execução..."
    
    # Script para execução local
    cat > scripts/run-scraper-local.sh << 'EOF'
#!/bin/bash

# run-scraper-local.sh - Executa o scraper localmente

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Executando scraper localmente..."

# Navegar para o diretório do scraper
cd backend/scraper

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "Ambiente virtual ativado"
else
    echo "❌ Ambiente virtual não encontrado. Execute: ./scripts/install-scraper.sh"
    exit 1
fi

# Carregar variáveis de ambiente
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
    log_info "Variáveis de ambiente carregadas"
fi

# Executar scraper
log_info "Iniciando scraper..."
python -m src.main "$@"

log_success "Scraper finalizado"
EOF

    chmod +x scripts/run-scraper-local.sh
    
    # Script para execução com Docker
    cat > scripts/run-scraper-docker.sh << 'EOF'
#!/bin/bash

# run-scraper-docker.sh - Executa o scraper via Docker

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Executando scraper via Docker..."

# Construir e executar apenas o scraper
docker-compose up --build scraper

log_success "Scraper finalizado"
EOF

    chmod +x scripts/run-scraper-docker.sh
    
    # Script para testes
    cat > scripts/test-scraper.sh << 'EOF'
#!/bin/bash

# test-scraper.sh - Executa testes do scraper

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute o script a partir do diretório raiz do projeto."
    exit 1
fi

log_info "Executando testes do scraper..."

# Navegar para o diretório do scraper
cd backend/scraper

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "Ambiente virtual ativado"
else
    echo "❌ Ambiente virtual não encontrado. Execute: ./scripts/install-scraper.sh"
    exit 1
fi

# Carregar variáveis de ambiente
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
    log_info "Variáveis de ambiente carregadas"
fi

# Executar testes
log_info "Executando testes unitários..."
if [ -f "pytest.ini" ]; then
    python -m pytest tests/ -v
else
    log_info "Executando teste de conexão com banco..."
    python -m src.main --test-db
    
    log_info "Executando teste de scraping..."
    python -m src.main --test-scraping
fi

log_success "Testes concluídos"
EOF

    chmod +x scripts/test-scraper.sh
    
    log_success "Scripts de execução criados"
}

# Função principal
main() {
    install_system_dependencies
    setup_python_environment
    install_python_dependencies
    setup_playwright
    setup_environment_variables
    test_installation
    create_execution_scripts
    
    echo ""
    log_success "🎉 Instalação do Scraper DJE concluída com sucesso!"
    echo ""
    echo "📋 Próximos passos:"
    echo ""
    echo "🔧 Para configurar variáveis de ambiente:"
    echo "   Edite o arquivo .env com suas configurações"
    echo ""
    echo "🐍 Para executar o scraper localmente:"
    echo "   ./scripts/run-scraper-local.sh"
    echo ""
    echo "🐍 Para executar em modo agendado:"
    echo "   ./scripts/run-scraper-local.sh --schedule"
    echo ""
    echo "🐳 Para executar via Docker:"
    echo "   ./scripts/run-scraper-docker.sh"
    echo ""
    echo "🧪 Para executar testes:"
    echo "   ./scripts/test-scraper.sh"
    echo ""
    echo "🔍 Para testar apenas conexão com banco:"
    echo "   cd backend/scraper && source venv/bin/activate && python -m src.main --test-db"
    echo ""
    echo "🔍 Para testar apenas scraping:"
    echo "   cd backend/scraper && source venv/bin/activate && python -m src.main --test-scraping"
    echo ""
    echo "📚 Logs do scraper ficam em:"
    echo "   backend/scraper/logs/"
    echo ""
}

# Executar função principal
main "$@" 