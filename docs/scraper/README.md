# 🐍 Scraper DJE - JusCash

Sistema de scraping automatizado para o Diário da Justiça Eletrônico (DJE), desenvolvido em Python com arquitetura hexagonal.

## 📋 Índice

- [Características](#-características)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Testes](#-testes)
- [Arquitetura](#-arquitetura)
- [Logs](#-logs)
- [Troubleshooting](#-troubleshooting)

## 🚀 Características

- **Scraping Automatizado**: Coleta publicações do DJE com base em critérios configuráveis
- **Agendamento**: Execução automática diária via APScheduler
- **Cache Redis**: Sistema de cache para otimização de performance
- **Banco PostgreSQL**: Armazenamento persistente com SQLAlchemy
- **Playwright**: Navegação web robusta e confiável
- **Arquitetura Hexagonal**: Código limpo e testável
- **Logs Estruturados**: Sistema de logging com Loguru
- **Docker Support**: Execução via containers

## 📦 Pré-requisitos

### Sistema

- **Python 3.8+** (recomendado 3.11)
- **PostgreSQL** (para banco de dados)
- **Redis** (para cache - opcional)
- **Git** (para versionamento)

### Linux/Ubuntu

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv python3-dev build-essential
```

### macOS

```bash
brew install python3 wget curl git
```

## 🔧 Instalação

### Opção 1: Instalação Automática (Recomendada)

Execute o script de instalação a partir do diretório raiz do projeto:

```bash
# Instalar apenas o scraper
./install.sh --scraper-only

# OU instalar todo o sistema (incluindo scraper)
./install.sh
```

### Opção 2: Instalação Manual

1. **Navegar para o diretório do scraper:**

    ```bash
    cd backend/scraper
    ```

2. **Criar ambiente virtual:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Instalar dependências:**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4. **Configurar Playwright:**

    ```bash
    python -m playwright install chromium
    python -m playwright install-deps chromium
    ```

## ⚡ Configuração

### Variáveis de Ambiente

Crie ou configure o arquivo `.env` no diretório raiz do projeto:

```env
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/juscash_db

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Configurações do DJE
DJE_CADERNO=1
DJE_INSTANCIA=1
DJE_LOCAL=1
DJE_PARTE=1

# Configurações de Scraping
SCRAPING_HEADLESS=true
SCRAPING_TIMEOUT=30000
SCRAPING_MAX_RETRIES=3
SCRAPING_REQUIRED_TERMS=termo1,termo2,termo3

# Agendamento
SCHEDULER_START_DATE=2024-01-01
SCHEDULER_EXECUTION_HOUR=8
SCHEDULER_EXECUTION_MINUTE=0
```

### Configurações Avançadas

As configurações podem ser ajustadas em `src/config/settings.py`:

- **Timeout de requisições**
- **User-Agent personalizado**
- **Configurações de retry**
- **Configurações de logging**

## 🎯 Uso

### Execução Local

```bash
# Execução única (imediata)
./scripts/run-scraper-local.sh

# Execução com agendamento automático
./scripts/run-scraper-local.sh --schedule

# Teste de conexão com banco
cd backend/scraper && source venv/bin/activate
python -m src.main --test-db

# Teste de scraping
python -m src.main --test-scraping
```

### Execução via Docker

```bash
# Executar scraper via Docker
./scripts/run-scraper-docker.sh

# OU executar todo o sistema
docker-compose up --build
```

### Modos de Execução

1. **Modo Imediato**: Executa uma vez e para
2. **Modo Agendado**: Executa automaticamente todos os dias no horário configurado
3. **Modo Teste**: Executa testes de conectividade e funcionalidade

## 🧪 Testes

### Executar Todos os Testes

```bash
./scripts/test-scraper.sh
```

### Testes Específicos

```bash
cd backend/scraper && source venv/bin/activate

# Teste de conexão com banco
python -m src.main --test-db

# Teste de scraping
python -m src.main --test-scraping

# Testes unitários (se disponíveis)
python -m pytest tests/ -v
```

## 📋 Arquitetura

O scraper segue a **Arquitetura Hexagonal** (Ports & Adapters):

```txt
src/
├── main.py                 # Ponto de entrada da aplicação
├── config/                 # Configurações
│   ├── settings.py
│   └── database.py
├── core/                   # Regras de negócio
│   ├── entities/
│   ├── usecases/
│   └── ports/
├── adapters/               # Adaptadores de infraestrutura
│   ├── primary/           # Adaptadores primários (entrada)
│   └── secondary/         # Adaptadores secundários (saída)
└── shared/                # Utilitários compartilhados
    ├── logger.py
    └── value_objects.py
```

### Componentes Principais

- **Entities**: Modelos de domínio (Publication, ScrapingResult)
- **Use Cases**: Casos de uso (ScrapePublications, ScheduleScraping)
- **Adapters**: Implementações concretas (Playwright, SQLAlchemy, Redis)
- **Ports**: Interfaces/contratos entre camadas

## 📊 Logs

Os logs são salvos em `backend/scraper/logs/`:

```txt
logs/
├── scraper.log           # Log principal
├── scraper_error.log     # Apenas erros
└── scraper_debug.log     # Debug detalhado
```

### Níveis de Log

- **INFO**: Informações gerais de execução
- **WARNING**: Avisos e situações não críticas
- **ERROR**: Erros que impedem a execução
- **DEBUG**: Informações detalhadas para debugging

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Erro de Importação do Playwright

```bash
# Reinstalar browsers
python -m playwright install chromium --with-deps
```

#### 2. Erro de Conexão com Banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
python -m src.main --test-db
```

#### 3. Erro de Conexão com Redis

```bash
# Verificar se Redis está rodando
redis-cli ping

# Redis é opcional - o scraper funciona sem ele
```

#### 4. Permissões no Linux

```bash
# Dar permissões aos scripts
chmod +x scripts/*.sh
```

#### 5. Dependências do Sistema (Ubuntu)

```bash
# Instalar dependências do Playwright
sudo apt-get install libnss3-dev libatk-bridge2.0-dev libdrm-dev \
    libxcomposite-dev libxdamage-dev libxrandr-dev libgbm-dev \
    libxss-dev libasound2-dev
```

### Verificação de Saúde

```bash
# Verificar instalação completa
./scripts/test-scraper.sh

# Verificar apenas importações Python
cd backend/scraper && source venv/bin/activate
python -c "
import playwright, sqlalchemy, redis, loguru, asyncio
print('✅ Todas as dependências OK')
"
```

### Logs de Debug

Para debugging detalhado, configure no `.env`:

```env
LOG_LEVEL=DEBUG
```

## 📚 Documentação Adicional

- [Configuração do Banco](../../database/README.md)
- [Configuração do Redis](../../database/redis/README.md)
- [Scripts de Instalação](../../scripts/README.md)
- [Docker Setup](../../docker-README.md)
