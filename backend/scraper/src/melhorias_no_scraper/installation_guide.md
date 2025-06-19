# 🚀 Guia de Instalação e Configuração - Sistema DJE-SP

## 📋 Pré-requisitos

### Requisitos do Sistema
- **Python 3.11+** (testado em 3.11 e 3.12)
- **Node.js 18+** (para a API)
- **PostgreSQL 13+**
- **Redis 6+** (para cache e filas)
- **Docker e Docker Compose** (recomendado)

### Dependências Python Obrigatórias
```bash
pip install playwright loguru httpx pydantic pydantic-settings
```

### Dependências Python Opcionais (para PDFs)
```bash
# Escolha uma das opções:
pip install PyPDF2         # Opção 1: PyPDF2
pip install pdfplumber     # Opção 2: pdfplumber (recomendado)
```

## 🔧 Instalação Passo a Passo

### 1. Clone e Configure o Repositório

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/juscash-dje-system.git
cd juscash-dje-system

# Copie o arquivo de environment
cp .env.example .env

# Edite as configurações
nano .env
```

### 2. Configure o Arquivo .env

```bash
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
BROWSER_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# ===========================================
# CONFIGURAÇÕES DE LOG
# ===========================================
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_ROTATION_DAYS=7
LOG_MAX_SIZE_MB=10

# ===========================================
# CONFIGURAÇÕES DA API (se usar integração)
# ===========================================
API_BASE_URL=http://localhost:8000
SCRAPER_API_KEY=sua_api_key_aqui
```

### 3. Instalar Dependências do Playwright

```bash
# Instalar browsers do Playwright
python -m playwright install chromium --with-deps

# Para ambiente Docker/produção
python -m playwright install --deps chromium
```

### 4. Criar Estrutura de Diretórios

```bash
mkdir -p logs/debug_images
mkdir -p logs/test_reports  
mkdir -p data/json_reports
mkdir -p data/temp_pdfs
mkdir -p src/scrap_workrs
```

## 🐳 Instalação com Docker (Recomendada)

### 1. Build e Execução

```bash
# Build de todos os serviços
docker-compose build

# Executar apenas o scraper
docker-compose up scraper

# Executar sistema completo (scraper + API + frontend)
docker-compose up
```

### 2. Verificar Status dos Containers

```bash
# Verificar containers ativos
docker-compose ps

# Ver logs do scraper
docker-compose logs -f scraper

# Acessar container do scraper
docker-compose exec scraper bash
```

## ⚙️ Configuração Avançada

### 1. Configuração de Performance

```python
# Em infrastructure/config/settings.py

class BrowserSettings:
    headless: bool = True
    timeout: int = 30000  # 30 segundos
    user_agent: str = "Mozilla/5.0..."
    
    # Configurações de performance
    disable_images: bool = True  # Desabilitar imagens para velocidade
    disable_javascript: bool = False  # Manter JS habilitado
    concurrent_pages: int = 1  # Páginas simultâneas (usar com cuidado)

class ScrapingSettings:
    max_retries: int = 3
    retry_delay: int = 5
    timeout: int = 30
    
    # Rate limiting
    min_request_interval: float = 2.0  # 2 segundos entre requisições
    max_concurrent_downloads: int = 1  # Downloads simultâneos
```

### 2. Configuração de Logging Detalhado

```python
# Em infrastructure/logging/logger.py

def setup_logger_advanced(name: str, level: str = "INFO"):
    """Configuração avançada de logging"""
    
    # Remover handler padrão
    logger.remove()
    
    # Handler para console com cores
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Logs por módulo
    logger.add(
        "logs/scraper_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        filter=lambda record: "scraper" in record["name"]
    )
    
    # Logs de erro separados
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip",
    )
    
    return logger
```

## 🧪 Testes e Verificação

### 1. Teste Básico de Funcionamento

```bash
# Executar teste completo
python test_system.py

# Teste apenas do parser
python -c "
from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser
parser = EnhancedDJEContentParser()
print('✅ Parser carregado com sucesso')
"

# Teste do browser
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.google.com')
        title = await page.title()
        print(f'✅ Browser funcionando: {title}')
        await browser.close()

asyncio.run(test())
"
```

### 2. Teste do Multi-Date Scraper

```bash
# Teste com período específico
python multi_date_scraper.py

# Ou modificar as datas no arquivo:
START_DATE = "17/03/2025"
END_DATE = "20/03/2025"  # Teste com poucos dias
NUM_WORKERS = 1
```

### 3. Verificar Arquivos Gerados

```bash
# Verificar JSONs gerados
ls -la data/json_reports/

# Verificar logs
tail -f logs/scraper_$(date +%Y-%m-%d).log

# Verificar progresso do multi-date
cat src/scrap_workrs.json | jq '.metadata'
```

## 🔍 Troubleshooting

### Problema: Browser não inicializa

```bash
# Reinstalar browsers
python -m playwright uninstall
python -m playwright install chromium --with-deps

# Verificar dependências do sistema (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1
```

### Problema: Timeout nos downloads

```python
# Aumentar timeouts em settings.py
class BrowserSettings:
    timeout: int = 60000  # 60 segundos
    navigation_timeout: int = 60000
    
class ScrapingSettings:
    pdf_download_timeout: int = 120  # 2 minutos
```

### Problema: Muitos PDFs falhando

```python
# Reduzir concorrência e aumentar delays
class ScrapingSettings:
    max_concurrent_downloads: int = 1
    min_request_interval: float = 3.0  # 3 segundos
    max_retries: int = 5
```

### Problema: Parser não encontra publicações

```python
# Verificar se os padrões estão corretos
# Em enhanced_content_parser.py, adicionar logs debug:

def _find_all_rpv_occurrences(self, content: str) -> List[Dict[str, Any]]:
    logger.debug(f"🔍 Buscando RPV em conteúdo de {len(content)} chars")
    
    # Mostrar trecho do conteúdo para debug
    logger.debug(f"📄 Primeiros 200 chars: {content[:200]}")
    
    occurrences = []
    for pattern in self.RPV_PATTERNS:
        matches = list(pattern.finditer(content))
        logger.debug(f"🎯 Padrão '{pattern.pattern}': {len(matches)} matches")
        # ... resto do código
```

## 📊 Monitoramento e Métricas

### 1. Dashboard de Status

```python
# Em monitoring/dashboard.py

class ScrapingDashboard:
    def get_daily_stats(self):
        """Retorna estatísticas do dia"""
        return {
            "publications_found": self._count_todays_publications(),
            "successful_downloads": self._count_successful_downloads(),
            "failed_downloads": len(self.scraper.failed_pdfs),
            "processing_time": self._calculate_avg_processing_time(),
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }
```

### 2. Alertas Automáticos

```python
# Em monitoring/alerts.py

class AlertManager:
    def check_scraping_health(self):
        """Verifica saúde do scraping"""
        issues = []
        
        # Verificar se há publicações sendo encontradas
        if self._no_publications_found_today():
            issues.append("⚠️ Nenhuma publicação encontrada hoje")
        
        # Verificar rate de falhas
        failure_rate = self._calculate_failure_rate()
        if failure_rate > 0.5:  # 50% de falhas
            issues.append(f"❌ Alta taxa de falhas: {failure_rate:.1%}")
        
        return issues
```

## 🚀 Deploy em Produção

### 1. Configurações de Produção

```bash
# .env.production
WORK_MODE=production
BROWSER_HEADLESS=true
LOG_LEVEL=WARNING
ENABLE_METRICS=true

# Configurações de segurança
SCRAPER_API_KEY=sua_chave_segura_aqui
DATABASE_URL=postgresql://user:pass@prod-db:5432/juscash_db
```

### 2. Docker Compose para Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  scraper:
    build:
      context: ./backend/scraper
      dockerfile: .docker/Dockerfile
      target: production
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=WARNING
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### 3. Cron Jobs

```bash
# Adicionar ao crontab para execução diária
0 8 * * * cd /path/to/project && docker-compose -f docker-compose.prod.yml run scraper python multi_date_scraper.py

# Limpeza de logs antigos
0 2 * * 0 find /path/to/logs -name "*.log" -mtime +30 -delete
```

## 📝 Próximos Passos

1. **Execute o teste completo** para verificar se tudo está funcionando
2. **Configure o cron job** para execução automática
3. **Monitore os logs** nas primeiras execuções
4. **Ajuste os timeouts** conforme necessário
5. **Implemente alertas** para monitoramento em produção

## 📞 Suporte

- **Logs detalhados**: `logs/scraper_YYYY-MM-DD.log`
- **Relatórios de teste**: `logs/test_reports/`
- **Debug images**: `logs/debug_images/` (capturas de tela em caso de erro)
- **Arquivos JSON**: `data/json_reports/` (publicações extraídas)
