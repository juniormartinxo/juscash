# Fila Redis para Publicações

## Visão Geral

Este módulo implementa uma fila Redis para processar o cadastramento de publicações de forma assíncrona, desacoplando o processo de scraping do envio para a API.

## Arquitetura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SCRAPER   │───▶│    REDIS    │───▶│   WORKER    │───▶│     API     │
│             │    │    QUEUE    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Componentes

### 1. RedisQueueAdapter

- **Localização**: `infrastructure/queue/redis_queue_adapter.py`
- **Função**: Gerencia operações da fila Redis
- **Funcionalidades**:
  - Enfileiramento de publicações
  - Desenfileiramento com timeout
  - Reenfileiramento com delay (retry)
  - Processamento de fila com delay
  - Estatísticas da fila
  - Dead Letter Queue (DLQ)

### 2. PublicationWorker

- **Localização**: `infrastructure/queue/publication_worker.py`
- **Função**: Processa publicações da fila e envia para API
- **Funcionalidades**:
  - Processamento em lote
  - Retry com backoff exponencial
  - Dead Letter Queue para falhas permanentes
  - Shutdown graceful
  - Monitoramento e estatísticas

### 3. SavePublicationsUseCase (Atualizado)

- **Localização**: `application/usecases/save_publications.py`
- **Função**: Enfileira publicações ao invés de enviar diretamente
- **Mudança**: Usa Redis Queue ao invés de API diretamente

## Configurações

### Variáveis de Ambiente

```env
# Redis
REDIS_HOST=juscash-redis
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0

# Fila
REDIS_QUEUE_NAME=publications_queue
REDIS_MAX_RETRIES=3
REDIS_RETRY_DELAY=60
REDIS_BATCH_SIZE=10
REDIS_WORKER_TIMEOUT=300
```

## Fluxo de Processamento

### 1. Scraping (Produtor)

```python
# O scraper extrai publicações e as enfileira
publications = [...]  # Lista de publicações extraídas
save_usecase = SavePublicationsUseCase()
result = await save_usecase.execute(publications)
# Publicações são enfileiradas no Redis
```

### 2. Worker (Consumidor)

```python
# Worker processa publicações da fila
worker = PublicationWorker()
await worker.start()  # Processa continuamente
```

### 3. Retry e DLQ

- **Retry**: Publicações com falha são reenfileiradas com delay
- **Backoff**: Delay aumenta exponencialmente (60s, 120s, 240s...)
- **DLQ**: Após 3 tentativas, move para Dead Letter Queue

## Estrutura das Filas Redis

### Fila Principal

- **Chave**: `publications_queue`
- **Tipo**: Lista (FIFO)
- **Conteúdo**: JSON das publicações

### Fila com Delay

- **Chave**: `publications_queue:delayed`
- **Tipo**: Sorted Set
- **Score**: Timestamp quando deve ser processada

### Dead Letter Queue

- **Chave**: `publications_queue:dlq`
- **Tipo**: Lista
- **Conteúdo**: Publicações que falharam permanentemente

## Como Usar

### 1. Executar com Worker Integrado

```bash
# O scraper já inicia o worker automaticamente
python src/main.py
```

### 2. Worker Standalone

```bash
# Executar apenas o worker
python src/cli/redis_cli.py worker
```

### 3. Monitorar Fila

```bash
# Ver estatísticas
python src/cli/redis_cli.py stats
```

## Vantagens da Implementação

### 1. **Desacoplamento**

- Scraper não depende da disponibilidade da API
- Processamento independente e paralelo

### 2. **Resilência**

- Retry automático com backoff exponencial
- Dead Letter Queue para investigação de falhas
- Persistência das publicações no Redis

### 3. **Performance**

- Processamento em lote
- Scraping mais rápido (não aguarda API)
- Rate limiting controlado no worker

### 4. **Monitoramento**

- Estatísticas em tempo real
- Visibilidade das filas
- CLI para operações manuais

### 5. **Escalabilidade**

- Múltiplos workers podem processar a mesma fila
- Configuração flexível de batch size

## Troubleshooting

### 1. Fila Crescendo Muito

```bash
# Verificar estatísticas
python src/cli/redis_cli.py stats

# Possíveis causas:
# - API fora do ar
# - Rate limiting muito agressivo
# - Muitas publicações duplicadas
```

### 2. Publicações na DLQ

```bash
# Investigar DLQ
python src/cli/redis_cli.py stats

# Ver logs do worker para detalhes dos erros
```

### 3. Worker Não Processando

```bash
# Verificar se worker está rodando
python src/cli/redis_cli.py stats

# Restart do worker
docker restart juscash-scraper
```

## Logs Importantes

### Enfileiramento

```
📤 Enfileirando 15 publicações
📊 Enfileiramento concluído: {'total': 15, 'enqueued': 15, 'failed': 0}
📈 Estado da fila: 23 publicações pendentes
```

### Worker Processing

```
🚀 Iniciando Publication Worker
📊 Lote processado: 10 publicações enviadas para API
✅ Publicação processada: 0017752-90.2019.8.26.0053
```

### Retry e DLQ

```
🔄 Reenfileirando 0031736-13.2018.8.26.0053 (tentativa 2/3, delay: 120s)
💀 Publicação 0031738-83.2018.8.26.0053 falhou após 3 tentativas - movendo para DLQ
```

## Desenvolvimento

### Limpar Fila (apenas desenvolvimento)

```python
from infrastructure.queue.redis_queue_adapter import RedisQueueAdapter

queue = RedisQueueAdapter()
queue.clear_queue()  # Apenas em WORK_MODE=development
```

### Testar Localmente

```bash
# Executar scraper uma vez
WORK_MODE=development python src/main.py
```
