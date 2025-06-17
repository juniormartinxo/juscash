# README.md

## 🕷️ DJE Scraper - São Paulo

Sistema de web scraping automatizado para extrair publicações do Diário da Justiça Eletrônico (DJE) de São Paulo, desenvolvido em Python com Arquitetura Hexagonal.

## 🎯 Objetivo

Automatizar a extração diária de publicações do DJE-SP, especificamente do **Caderno 3 - Judicial - 1ª Instância - Capital Parte 1**, buscando por publicações que contenham termos obrigatórios relacionados ao INSS.

## 🏗️ Arquitetura

O projeto segue **Arquitetura Hexagonal** (Ports and Adapters):

```txt
src/
├── domain/                 # 🎯 Core Domain
│   ├── entities/          # Entidades de negócio
│   ├── ports/             # Interfaces/Contratos
│   └── services/          # Serviços de domínio
├── application/           # 🎮 Application Layer
│   ├── usecases/         # Casos de uso
│   └── services/         # Orquestradores
├── infrastructure/       # 🔧 Infrastructure Layer
│   ├── web/              # Web scraping adapters
│   ├── api/              # API client adapters
│   ├── config/           # Configurações
│   ├── logging/          # Sistema de logs
│   └── scheduler/        # Agendamento
└── shared/               # 🛠️ Shared Kernel
    └── container.py      # Injeção de dependência
```

## 🚀 Funcionalidades

- ✅ **Scraping Automatizado**: Extração diária a partir de 17/03/2025
- ✅ **Busca Inteligente**: Filtra publicações com termos obrigatórios
- ✅ **Extração Estruturada**: Número do processo, autores, advogados, valores
- ✅ **Integração com API**: Envia dados via endpoint `/api/scraper/publications`
- ✅ **Logs Detalhados**: Sistema completo de auditoria
- ✅ **Retry Logic**: Recuperação automática de falhas
- ✅ **Validação de Dados**: Validação rigorosa antes do envio

## 📋 Pré-requisitos

- Python 3.12+
- API JusCash rodando (com endpoint `/api/scraper/publications`)
- Chave API configurada (`SCRAPER_API_KEY`)

## 🛠️ Instalação

1. **Clone e configure o ambiente**:

    ```bash
    # Instalar dependências
    pip install -r requirements.txt

    # Instalar browsers do Playwright
    python -m playwright install chromium --with-deps
    ```

2. **Configurar variáveis de ambiente**:

    ```bash
    # Copiar e editar configurações
    cp .env.example .env

    # Configurar SCRAPER_API_KEY obrigatoriamente
    SCRAPER_API_KEY=sua-chave-api-muito-longa-e-segura-aqui
    ```

3. **Executar testes**:

    ```bash
    # Testar conexão com API
    python test_api_connection.py

    # Testar scraping manual
    python test_scraper_manual.py

    # Ou usar o script completo
    ./run_tests.sh
    ```

## 🚀 Execução

### Modo Produção (Agendado)

```bash
# Execução automática diária
python src/main.py
```

### Modo Desenvolvimento (Manual)

```bash
# Execução única para testes
python test_scraper_manual.py
```

### Docker

```bash
# Build e execução
docker-compose -f docker-compose.scraper.yml up --build

# Para desenvolvimento
docker-compose -f docker-compose.scraper.yml run scraper python test_api_connection.py
```

## ⚙️ Configuração

### Variáveis de Ambiente Principais

```bash
# API
API_BASE_URL=http://localhost:8000
SCRAPER_API_KEY=sua-chave-api-aqui
API_TIMEOUT=30

# Browser
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# Scraper
SCRAPER_MAX_PAGES=20
SCRAPER_SEARCH_TERMS=aposentadoria,benefício,INSS

# Logs
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### Termos de Busca

Configure no `.env` os termos que devem estar presentes nas publicações:

```bash
SCRAPER_SEARCH_TERMS=aposentadoria,benefício,INSS,auxílio
```

## 📊 Monitoramento

### Logs

```bash
# Logs em tempo real
tail -f logs/scraper_$(date +%Y-%m-%d).log

# Logs de erro
tail -f logs/errors_$(date +%Y-%m-%d).log
```

### Estatísticas

O scraper registra automaticamente:

- Publicações encontradas
- Publicações novas vs duplicadas
- Taxa de sucesso/falha
- Tempo de execução
- Erros detalhados

## 🧪 Testes

### Testes Automatizados

```bash
# Teste completo
./run_tests.sh

# Testes individuais
python test_api_connection.py      # Conexão com API
python test_scraper_manual.py      # Scraping manual
```

### Dados de Teste

O sistema cria publicações de teste com:

- Números de processo únicos (timestamp)
- Prefixo "TESTE" para identificação
- Metadados de teste

## 🔧 Desenvolvimento

### Estrutura de Dados

**Publicação extraída**:

```python
{
    "process_number": "1234567-89.2024.8.26.0100",
    "authors": ["João Silva Santos"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [{"name": "Dr. Carlos", "oab": "123456"}],
    "gross_value": 150000,  # em centavos
    "content": "Texto completo da publicação...",
    "extraction_metadata": {
        "extraction_date": "2024-03-17T10:30:00Z",
        "source_url": "https://dje.tjsp.jus.br/...",
        "confidence_score": 0.95
    }
}
```

### Adicionando Novos Adapters

Para adicionar novos scrapers ou APIs:

1. **Criar Port** (interface) em `src/domain/ports/`
2. **Implementar Adapter** em `src/infrastructure/`
3. **Registrar no Container** em `src/shared/container.py`
4. **Configurar Use Case** em `src/application/usecases/`

### Debugging

```bash
# Logs detalhados
LOG_LEVEL=DEBUG python src/main.py

# Browser visível (desenvolvimento)
BROWSER_HEADLESS=false python test_scraper_manual.py
```

## 🔒 Segurança

- ✅ **API Key obrigatória** para todas as requisições
- ✅ **Rate limiting** respeitado (1000 req/15min)
- ✅ **Validação rigorosa** de dados extraídos
- ✅ **Logs de auditoria** completos
- ✅ **Retry com backoff** para evitar sobrecarga

## 📈 Performance

- **Páginas processadas**: Configurável (padrão: 20)
- **Timeout por página**: 30 segundos
- **Retry automático**: 3 tentativas com delay progressivo
- **Memória otimizada**: Processamento streaming das publicações

## 🆘 Troubleshooting

### Problemas Comuns

**1. Erro de API Key**

```bash
❌ Invalid API Key
# Solução: Verificar SCRAPER_API_KEY no .env
```

**2. Timeout do Browser**

```bash
❌ Timeout 30000ms exceeded
# Solução: Aumentar BROWSER_TIMEOUT ou verificar conexão
```

**3. Dependências Playwright**

```bash
❌ Browser not found
# Solução: python -m playwright install chromium --with-deps
```

### Logs de Debug

```bash
# Ativar debug completo
LOG_LEVEL=DEBUG
BROWSER_HEADLESS=false
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Siga a arquitetura hexagonal
4. Adicione testes
5. Faça commit das mudanças
6. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo `LICENSE` para detalhes.

**🎯 Status**: ✅ Pronto para produção
**📅 Início**: 17/03/2025 (execução diária)
**🕷️ Target**: DJE-SP Caderno 3 - Judicial - 1ª Instância - Capital Parte 1
