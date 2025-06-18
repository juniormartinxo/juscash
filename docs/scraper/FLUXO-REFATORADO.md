# Refatoração do Scraper

## Visão Geral

Esta documentação descreve a refatoração realizada no scraper do DJE para melhorar a arquitetura do sistema, movendo a responsabilidade de persistência de dados para a API.

## Motivação

A refatoração foi motivada pelos seguintes pontos:

1. **Separação de Responsabilidades**: O scraper deve focar apenas na extração de dados, enquanto a API deve ser responsável pela persistência.
2. **Manutenibilidade**: Código mais fácil de manter e evoluir.
3. **Escalabilidade**: Possibilidade de ter múltiplos scrapers enviando dados para a mesma API.
4. **Centralização**: Lógica de persistência centralizada na API.

## Mudanças Realizadas

### 1. Novo Repositório da API

Foi criado um novo adaptador `APIRepository` que implementa a interface `DatabasePort`:

```python
class APIRepository(DatabasePort):
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_execution_id: Optional[str] = None
```

Principais funcionalidades:

- Comunicação assíncrona com a API usando `aiohttp`
- Gerenciamento do ciclo de vida da sessão HTTP
- Métodos para iniciar/finalizar execuções
- Métodos para salvar publicações individualmente ou em lote

### 2. Configurações Atualizadas

Novas configurações adicionadas em `settings.py`:

```python
class Settings(BaseSettings):
    # Configurações da API
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    API_RETRY_ATTEMPTS: int = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
    API_RETRY_DELAY: int = int(os.getenv("API_RETRY_DELAY", "1"))
```

### 3. Fluxo de Execução

O novo fluxo de execução do scraper é:

1. Inicialização:
   - Carrega configurações
   - Inicializa adaptadores (API, Redis, Playwright)
   - Configura logging

2. Execução:
   - Inicia uma nova execução na API
   - Extrai dados do DJE
   - Envia dados para a API
   - Finaliza execução com status e estatísticas

3. Limpeza:
   - Fecha conexões
   - Libera recursos

## Configuração

### Variáveis de Ambiente

Adicione as seguintes variáveis ao arquivo `.env`:

```env
# API
API_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=1

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600
REDIS_MAX_CONNECTIONS=10

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
```

### Dependências

Novas dependências adicionadas ao `requirements.txt`:

```text
aiohttp==3.9.3
aioredis==2.0.1
python-dateutil==2.8.2
```

## Endpoints da API

O scraper espera os seguintes endpoints na API:

1. **Iniciar Execução**:
   - `POST /api/scraping-executions`
   - Payload: `{ execution_type, criteria, max_publications, started_at }`

2. **Salvar Publicação**:
   - `POST /api/publications`
   - Payload: `{ publication, scraping_execution_id }`

3. **Salvar Publicações em Lote**:
   - `POST /api/publications/batch`
   - Payload: `{ publications, scraping_execution_id }`

4. **Finalizar Execução**:
   - `PATCH /api/scraping-executions/{execution_id}`
   - Payload: `{ status, stats, error_details, finished_at }`

## Tratamento de Erros

O scraper implementa tratamento de erros em vários níveis:

1. **Erros de Conexão**:
   - Retry automático com backoff exponencial
   - Logging detalhado de erros

2. **Erros de API**:
   - Validação de status codes
   - Exceções específicas para cada tipo de erro

3. **Erros de Scraping**:
   - Captura e registro de erros durante a extração
   - Finalização adequada da execução mesmo em caso de erro

## Logging

O sistema mantém logs detalhados em:

1. **Console**: Output em tempo real
2. **Arquivo**: `/tmp/scraper.log`
3. **API**: Registro de execuções e erros

## Próximos Passos

1. **Testes**:
   - Implementar testes unitários para o novo repositório
   - Adicionar testes de integração com a API

2. **Monitoramento**:
   - Adicionar métricas de performance
   - Implementar alertas para falhas

3. **Documentação**:
   - Documentar endpoints da API
   - Criar guia de troubleshooting
