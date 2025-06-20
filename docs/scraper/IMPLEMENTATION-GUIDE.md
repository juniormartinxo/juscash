# 🕷️ DJE Scraper - Guia Completo de Implementação

## 📋 Visão Geral do Projeto

O **DJE Scraper** é um sistema completo de automação para extrair publicações do Diário da Justiça Eletrônico (DJE) de São Paulo, desenvolvido seguindo **Arquitetura Hexagonal** em Python 3.12+. O sistema integra-se perfeitamente com a API JusCash existente para processar publicações relacionadas ao INSS.

### 🎯 Objetivos Principais

- ✅ **Automação Diária**: Extração automática a partir de 17/03/2025
- ✅ **Busca Inteligente**: Filtragem por termos obrigatórios (aposentadoria, benefício, INSS)
- ✅ **Integração API**: Envio via endpoint `/api/scraper/publications`
- ✅ **Arquitetura Robusta**: Hexagonal com separação clara de responsabilidades
- ✅ **Monitoramento Completo**: Logs, alertas, métricas e health checks
- ✅ **Produção Ready**: Docker, systemd, backup automático

---

## 🏗️ Arquitetura do Sistema

```txt
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   DJE Website   │     │   Scraper    │     │   API JusCash   │
│   (Target)      │────▶│   (Python)   │────▶│   (Node.js)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                       │
                        ┌──────────────┐               │
                        │   Database   │◀──────────────┘
                        │ (PostgreSQL) │
                        └──────────────┘
```

### 🧩 Componentes Principais

1. **Domain Layer** - Entidades e regras de negócio
2. **Application Layer** - Use cases e orquestradores
3. **Infrastructure Layer** - Adapters para tecnologias externas
4. **Shared Kernel** - Utilitários e container de dependências

---

## 📁 Estrutura Completa do Projeto

```txt
juscash-dje-system/
├── 📄 README.md
├── 📄 docker-compose.yml
├── 📄 .env
├── 📄 requirements.txt
├── 📄 scraper_cli.py
├── 📄 production-setup.sh
├── 📄 deployment-check.sh
├── 📄 final-integration-test.sh
│
├── 📂 src/
│   ├── 📂 domain/
│   │   ├── 📂 entities/
│   │   │   ├── 📄 publication.py
│   │   │   └── 📄 scraping_execution.py
│   │   ├── 📂 ports/
│   │   │   ├── 📄 scraping_repository.py
│   │   │   └── 📄 web_scraper.py
│   │   └── 📂 services/
│   │       └── 📄 publication_validator.py
│   │
│   ├── 📂 application/
│   │   ├── 📂 usecases/
│   │   │   ├── 📄 extract_publications.py
│   │   │   ├── 📄 save_publications.py
│   │   │   └── 📄 validate_extracted_data.py
│   │   └── 📂 services/
│   │       └── 📄 scraping_orchestrator.py
│   │
│   ├── 📂 infrastructure/
│   │   ├── 📂 web/
│   │   │   ├── 📄 dje_scraper_adapter.py
│   │   │   ├── 📄 content_parser.py
│   │   │   └── 📄 retry_handler.py
│   │   ├── 📂 api/
│   │   │   └── 📄 api_client_adapter.py
│   │   ├── 📂 config/
│   │   │   ├── 📄 settings.py
│   │   │   └── 📄 dynamic_config.py
│   │   ├── 📂 logging/
│   │   │   └── 📄 logger.py
│   │   ├── 📂 scheduler/
│   │   │   └── 📄 scheduler_adapter.py
│   │   ├── 📂 monitoring/
│   │   │   └── 📄 performance_monitor.py
│   │   ├── 📂 backup/
│   │   │   └── 📄 backup_manager.py
│   │   ├── 📂 alerts/
│   │   │   └── 📄 alert_system.py
│   │   ├── 📂 health/
│   │   │   └── 📄 health_checker.py
│   │   └── 📂 utils/
│   │       └── 📄 debugging_tools.py
│   │
│   ├── 📂 cli/
│   │   └── 📄 commands.py
│   │
│   ├── 📂 shared/
│   │   └── 📄 container.py
│   │
│   └── 📄 main.py
│
├── 📂 tests/
│   ├── 📄 conftest.py
│   ├── 📂 unit/
│   └── 📂 integration/
│
├── 📂 config/
│   └── 📄 scraping_config.json
│
├── 📂 logs/
├── 📂 backups/
├── 📂 debug/
├── 📂 scripts/
└── 📂 docs/
```

---

## 🚀 Guia de Instalação

### 1. Pré-requisitos

```bash
# Verificar requisitos
python3 --version  # >= 3.12
docker --version
docker-compose --version
node --version     # Para API JusCash
```

### 2. Configuração Inicial

```bash
# Clonar estrutura (ou criar manualmente)
mkdir juscash-dje-system
cd juscash-dje-system

# Criar estrutura de pastas
mkdir -p {src,tests,config,logs,backups,scripts,docs}
mkdir -p src/{domain,application,infrastructure,cli,shared}
mkdir -p src/domain/{entities,ports,services}
mkdir -p src/application/{usecases,services}
mkdir -p src/infrastructure/{web,api,config,logging,scheduler,monitoring,backup,alerts,health,utils}
```

### 3. Dependências Python

```bash
# Criar requirements.txt
cat > requirements.txt << 'EOF'
# Core dependencies
asyncio
httpx>=0.25.0
loguru>=0.7.0
pydantic[email]>=2.0.0
python-dotenv>=1.0.0

# Web scraping
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Scheduling
APScheduler>=3.10.0

# Data processing
python-dateutil>=2.8.0
tenacity>=8.2.0

# CLI
click>=8.0.0

# System monitoring
psutil>=5.9.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
EOF

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers
python -m playwright install chromium --with-deps
```

### 4. Configuração de Ambiente

```bash
# Criar .env
cat > .env << 'EOF'
# Ambiente
ENVIRONMENT=development

# API Configuration
API_BASE_URL=http://localhost:8000
SCRAPER_API_KEY=scraper_2024_sua_chave_muito_longa_e_segura_aqui
API_TIMEOUT=30

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
BROWSER_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

# Scraper Configuration
SCRAPER_TARGET_URL=https://dje.tjsp.jus.br/cdje/index.do
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5
SCRAPER_MAX_PAGES=20
SCRAPER_SEARCH_TERMS=aposentadoria,benefício,INSS

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_ROTATION_DAYS=7
LOG_MAX_SIZE_MB=10
EOF
```

---

## 🔧 Implementação dos Componentes

1. Implementar Entidades de Domínio

    **src/domain/entities/publication.py**

    ```python
    # [Código da entidade Publication implementado anteriormente]
    ```

2. Implementar Ports (Interfaces)

    **src/domain/ports/web_scraper.py**

    ```python
    # [Código das interfaces implementado anteriormente]
    ```

3. Implementar Use Cases

    **src/application/usecases/extract_publications.py**

    ```python
    # [Código dos use cases implementado anteriormente]
    ```

4. Implementar Adapters

    **src/infrastructure/web/dje_scraper_adapter.py**

    ```python
    # [Código do scraper implementado anteriormente]
    ```

5. Implementar CLI

    **src/cli/commands.py**

    ```python
    # [Código da CLI implementado anteriormente]
    ```

6. Implementar Entry Point

    **src/main.py**

    ```python
    # [Código do main implementado anteriormente]
    ```

---

## 🐳 Docker e Deploy

### 1. Dockerfile

```dockerfile
# [Dockerfile implementado anteriormente]
```

### 2. Docker Compose

```yaml
# [docker-compose.yml implementado anteriormente]
```

### 3. Deploy em Produção

```bash
# Executar script de setup
chmod +x production-setup.sh
./production-setup.sh

# Verificar instalação
./deployment-check.sh

# Teste de integração completa
./final-integration-test.sh
```

---

## 🎮 Usando o Sistema

### 1. CLI Commands

```bash
# Executar scraping manual
python scraper_cli.py run --max-pages 5

# Verificar status
python scraper_cli.py status

# Configuração
python scraper_cli.py config show
python scraper_cli.py config set --key max_pages --value 10

# Backup
python scraper_cli.py backup logs --days-back 1

# Alertas
python scraper_cli.py alerts list

# Testes
python scraper_cli.py test api
python scraper_cli.py test dje

# Monitoramento
python scraper_cli.py monitor --duration 60
```

### 2. Modo Agendado (Produção)

```bash
# Iniciar serviço systemd
sudo systemctl start dje-scraper
sudo systemctl enable dje-scraper

# Monitorar
journalctl -fu dje-scraper
```

---

## 📊 Monitoramento e Observabilidade

### 1. Logs Estruturados

```bash
# Logs principais
tail -f logs/scraper_$(date +%Y-%m-%d).log

# Logs de erro
tail -f logs/errors_$(date +%Y-%m-%d).log
```

### 2. Métricas de Performance

```bash
# Monitor em tempo real
python monitor_performance.py

# Health check
curl http://localhost:8000/health

# Estatísticas via CLI
python scraper_cli.py status
```

### 3. Alertas

- **Email**: Configurável para alertas críticos
- **Logs**: Todos os eventos são registrados
- **Sistema**: Integração com monitoramento externo

---

## 🔒 Segurança e Boas Práticas

### 1. Autenticação

- **API Key**: Obrigatória para todas as requisições ao endpoint scraper
- **Rate Limiting**: 1000 requests/15min para scraper vs 100 para usuários
- **Validação**: Rigorosa de todos os inputs

### 2. Configurações Seguras

```bash
# Gerar API Key forte
openssl rand -hex 32

# Configurar firewall
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw enable

# Limites de sistema
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
```

### 3. Backup e Recuperação

- **Backup Automático**: Diário via cron
- **Retenção**: 30 dias para logs, 90 dias para dados
- **Compressão**: Automática para economizar espaço

---

## 🧪 Testes

### 1. Testes Unitários

```bash
# Executar testes
pytest tests/unit/ -v

# Com coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### 2. Testes de Integração

```bash
# Teste de API
python test_api_connection.py

# Teste manual de scraping
python test_scraper_manual.py

# Teste completo
./final-integration-test.sh
```

### 3. Benchmark

```bash
# Performance
python benchmark.py

# Load test
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/scraper/publications \
    -H "X-API-Key: sua-chave" \
    -H "Content-Type: application/json" \
    -d '{"test": true}' &
done
```

---

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de API Key**

   ```bash
   # Verificar configuração
   grep SCRAPER_API_KEY .env
   # Deve ser a mesma na API e no scraper
   ```

2. **Timeout do Browser**

   ```bash
   # Aumentar timeout
   export BROWSER_TIMEOUT=60000
   # Ou rodar sem headless para debug
   export BROWSER_HEADLESS=false
   ```

3. **Falha de Conexão com API**

   ```bash
   # Testar conectividade
   curl http://localhost:8000/health
   # Verificar se serviços estão rodando
   docker-compose ps
   ```

4. **Erro de Permissão Playwright**

   ```bash
   # Reinstalar browsers
   python -m playwright install chromium --with-deps
   ```

### Debug Avançado

```bash
# Logs detalhados
LOG_LEVEL=DEBUG python scraper_cli.py run

# Captura de tela em erros
BROWSER_HEADLESS=false python scraper_cli.py test dje

# Network debugging
python -c "
import asyncio
from src.infrastructure.utils.debugging_tools import DebugTools
# Usar ferramentas de debug
"
```

---

## 📈 Otimizações de Performance

### 1. Sistema

```bash
# Executar otimizações
./performance-tuning.sh

# Aplicar configurações
source python_env.sh
```

### 2. Browser

```python
# Configurações otimizadas já implementadas
OPTIMIZED_LAUNCH_OPTIONS = {
    'headless': True,
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        # ... outras otimizações
    ]
}
```

### 3. Rede

```bash
# Otimizações TCP aplicadas automaticamente
net.core.somaxconn = 65535
net.ipv4.tcp_congestion_control = bbr
```

---

## 🔄 Atualizações e Manutenção

### 1. Atualizações de Código

```bash
# Backup antes de atualizar
./cleanup_cache.sh
python scraper_cli.py backup logs

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Reinstalar browsers se necessário
python -m playwright install chromium
```

### 2. Manutenção Rotineira

```bash
# Limpeza semanal
0 2 * * 0 /path/to/cleanup_cache.sh

# Backup diário
0 1 * * * /path/to/scraper_cli.py backup logs

# Health check
*/15 * * * * /path/to/scripts/health_check.sh
```

### 3. Monitoramento de Capacidade

```bash
# Verificar recursos
df -h  # Espaço em disco
free -h  # Memória
top  # CPU

# Logs de performance
python monitor_performance.py
```

---

## 📚 Documentação Adicional

### 1. API Integration

- **Endpoint**: `POST /api/scraper/publications`
- **Headers**: `X-API-Key`, `Content-Type: application/json`
- **Rate Limit**: 1000 req/15min
- **Docs**: Consultar `../api/SCRAPER-INTEGRATION.md`

### 2. Configuração Dinâmica

- **Arquivo**: `config/scraping_config.json`
- **Hot Reload**: Alterações aplicadas automaticamente
- **CLI**: `python scraper_cli.py config`

### 3. Extensibilidade

Para adicionar novos scrapers ou funcionalidades:

1. **Criar Port** (interface)
2. **Implementar Adapter**
3. **Registrar no Container**
4. **Adicionar Use Case**
5. **Expor via CLI**

---

## 🎯 Roadmap Futuro

### Próximas Funcionalidades

- [ ] **Multi-tenancy**: Suporte a múltiplos clientes
- [ ] **Dashboard Web**: Interface de monitoramento
- [ ] **API de Métricas**: Exposição via REST
- [ ] **Machine Learning**: Classificação automática
- [ ] **Webhooks**: Notificações em tempo real
- [ ] **Kubernetes**: Deploy escalável

### Melhorias Planejadas

- [ ] **Cache Inteligente**: Redis para publicações
- [ ] **Processamento Paralelo**: Múltiplos workers
- [ ] **Fallback Adapters**: Múltiplas fontes de dados
- [ ] **Advanced Analytics**: Relatórios detalhados

---

## 🤝 Contribuição

### Padrões de Desenvolvimento

1. **Arquitetura Hexagonal**: Sempre seguir separação de camadas
2. **Clean Code**: Código limpo e bem documentado
3. **Type Hints**: Usar anotações de tipo
4. **Testes**: Cobrir novos códigos com testes
5. **Logs**: Adicionar logs estruturados

### Pull Request Process

1. Fork do projeto
2. Criar branch para feature
3. Implementar seguindo padrões
4. Adicionar testes
5. Atualizar documentação
6. Submeter PR

---

## 📄 Licença

Este projeto está sob licença MIT. Consulte arquivo `LICENSE` para detalhes.

---

## 🎉 Conclusão

O **DJE Scraper** é um sistema robusto, escalável e pronto para produção que automatiza completamente a extração de publicações do DJE-SP. Com arquitetura hexagonal, monitoramento completo e integração perfeita com a API JusCash, o sistema garante:

- ✅ **Reliability**: Retry automático e tratamento de erros
- ✅ **Observability**: Logs, métricas e alertas completos
- ✅ **Scalability**: Preparado para crescimento
- ✅ **Maintainability**: Código limpo e bem estruturado
- ✅ **Security**: Autenticação e validação rigorosa

**🚀 Status**: ✅ **PRONTO PARA PRODUÇÃO**

Para suporte ou dúvidas, consulte a documentação detalhada ou execute:

```bash
python scraper_cli.py --help
```
