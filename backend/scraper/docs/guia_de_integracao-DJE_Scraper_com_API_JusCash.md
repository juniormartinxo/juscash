# 🔗 Guia de Integração - DJE Scraper com API JusCash

## 📋 Visão Geral da Integração

O scraper DJE-SP foi desenvolvido para trabalhar em conjunto com a API JusCash existente, enviando publicações extraídas via endpoint `/api/scraper/publications` usando autenticação por API Key.

## 🏗️ Arquitetura de Integração

```txt
┌─────────────────┐     HTTP POST      ┌──────────────────┐     ┌─────────────────┐
│   DJE Scraper   │ ────────────────▶ │   API JusCash    │ ──▶ │   PostgreSQL    │
│   (Python)      │   X-API-Key       │   (Node.js)      │     │   Database      │
└─────────────────┘                   └──────────────────┘     └─────────────────┘
        │                                       │
        ▼                                       ▼
┌─────────────────┐                   ┌──────────────────┐
│   DJE Website   │                   │   React Frontend │
│   (Playwright)  │                   │   (Kanban)       │
└─────────────────┘                   └──────────────────┘
```

## 🔧 Configuração da Integração

### 1. Configurar API Key na API JusCash

**Arquivo**: `backend/api/.env`

```bash
# Adicionar a mesma chave nos dois projetos
SCRAPER_API_KEY=scraper_2024_a8f3k9m2x7q1w5e8r4t6y9u3i0p2s5d7f1g4h6j8k0l3z9x2c4v6b8n1m5q7w9e3r5t7y1u4i6o8p0
```

**Verificar endpoints ativos**:

```bash
# API deve estar rodando em:
http://localhost:8000/api/scraper/publications
```

### 2. Configurar Scraper

**Arquivo**: `backend/scraper/.env`

```bash
# Configuração para comunicar com a API
API_BASE_URL=http://localhost:8000
SCRAPER_API_KEY=scraper_2024_a8f3k9m2x7q1w5e8r4t6y9u3i0p2s5d7f1g4h6j8k0l3z9x2c4v6b8n1m5q7w9e3r5t7y1u4i6o8p0

# Em Docker, usar o nome do serviço
# API_BASE_URL=http://juscash-api:8000
```

### 3. Estrutura de Pastas Recomendada

```txt
juscash-dje-system/
├── docker-compose.yml           # Compose principal
├── backend/
│   ├── api/                    # API Node.js existente
│   │   ├── .env
│   │   ├── src/
│   │   └── package.json
│   └── scraper/                # Novo scraper Python
│       ├── .env
│       ├── src/
│       ├── requirements.txt
│       ├── Dockerfile
│       └── test_api_connection.py
├── frontend/                   # React app existente
└── database/                   # PostgreSQL
```

## 🚀 Deploy Integrado

### Docker Compose Atualizado

**Arquivo**: `docker-compose.yml`

```yaml
services:
  # API existente
  api:
    build:
      context: ./backend/api
    container_name: juscash-api
    ports:
      - "8000:8000"
    environment:
      - SCRAPER_API_KEY=${SCRAPER_API_KEY}
    depends_on:
      - postgres
    networks:
      - juscash-net

  # Novo serviço do scraper
  scraper:
    build:
      context: ./backend/scraper
    container_name: juscash-scraper
    environment:
      - API_BASE_URL=http://juscash-api:8000
      - SCRAPER_API_KEY=${SCRAPER_API_KEY}
      - BROWSER_HEADLESS=true
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/scraper/logs:/app/logs
    depends_on:
      - api
    networks:
      - juscash-net
    restart: unless-stopped

  # Serviços existentes
  postgres:
    # ... configuração existente
  
  frontend:
    # ... configuração existente

networks:
  juscash-net:
    driver: bridge
```

### Scripts de Deploy

**Arquivo**: `deploy.sh`

```bash
#!/bin/bash
# Script de deploy completo

echo "🚀 Deploy JusCash DJE System"
echo "============================="

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

# Carregar variáveis de ambiente
source .env

# Verificar SCRAPER_API_KEY
if [ -z "$SCRAPER_API_KEY" ]; then
    echo "❌ SCRAPER_API_KEY não definida"
    echo "💡 Configure no arquivo .env"
    exit 1
fi

echo "✅ Configuração validada"

# Build e deploy
echo "🏗️  Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Aguardar API ficar pronta
echo "⏳ Aguardando API ficar pronta..."
timeout 60 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ API está rodando"
else
    echo "❌ Timeout - API não respondeu"
    exit 1
fi

# Testar integração
echo "🧪 Testando integração scraper -> API..."
docker-compose exec scraper python test_api_connection.py

if [ $? -eq 0 ]; then
    echo "✅ Integração funcionando"
else
    echo "❌ Falha na integração"
    echo "📋 Logs do scraper:"
    docker-compose logs scraper
    exit 1
fi

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔗 API: http://localhost:8000"
echo "📋 API Docs: http://localhost:8000/api-docs"
echo "📈 Health: http://localhost:8000/health"
```

## 🧪 Testes de Integração

### Script de Teste Completo

**Arquivo**: `test_integration.py`

```python
#!/usr/bin/env python3
"""
Teste completo de integração Scraper -> API -> Database
"""

import asyncio
import httpx
import os
from datetime import datetime

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")


async def test_full_integration():
    """Testa o fluxo completo de integração"""
    print("🧪 Teste de Integração Completa")
    print("=" * 40)
    
    if not SCRAPER_API_KEY:
        print("❌ SCRAPER_API_KEY não configurada")
        return False
    
    # Dados de teste
    test_data = {
        "process_number": f"INTEGRATION-{int(datetime.now().timestamp())}-89.2024.8.26.0100",
        "publicationDate": "2024-03-15T00:00:00.000Z",
        "availabilityDate": "2024-03-17T00:00:00.000Z",
        "authors": ["João Silva Santos - INTEGRAÇÃO"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [{"name": "Dr. Teste Integração", "oab": "999999"}],
        "grossValue": 100000,
        "netValue": 90000,
        "interestValue": 5000,
        "attorneyFees": 5000,
        "content": "Teste de integração completa entre scraper e API. Aposentadoria por invalidez.",
        "status": "NOVA",
        "scrapingSource": "DJE-SP-TEST",
        "extractionMetadata": {
            "test": True,
            "integration_test": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Teste 1: Health check da API
        print("🏥 Teste 1: Health check da API")
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                print("✅ API está saudável")
            else:
                print(f"⚠️  API health check: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro no health check: {e}")
            return False
        
        # Teste 2: Endpoint de scraper disponível
        print("\n🔍 Teste 2: Endpoint do scraper")
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/scraper/publications",
                json=test_data,
                headers={"X-API-Key": SCRAPER_API_KEY}
            )
            
            if response.status_code == 201:
                print("✅ Publicação criada via endpoint scraper")
                result = response.json()
                publication_id = result["data"]["publication"]["id"]
                print(f"📄 ID da publicação: {publication_id}")
            else:
                print(f"❌ Erro ao criar publicação: {response.status_code}")
                print(f"📋 Resposta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na criação: {e}")
            return False
        
        # Teste 3: Verificar se publicação está disponível
        print("\n📋 Teste 3: Consultar publicação criada")
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/publications",
                params={"search": test_data["process_number"], "limit": 1},
                headers={"Authorization": "Bearer dummy"}  # Usar token real se necessário
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["data"]["total"] > 0:
                    print("✅ Publicação encontrada na API")
                else:
                    print("⚠️  Publicação não encontrada na busca")
            else:
                print(f"⚠️  Erro na consulta: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Erro na consulta: {e}")
        
        # Teste 4: Endpoint normal (para comparação)
        print("\n🔄 Teste 4: Endpoint normal (comparação)")
        try:
            test_data_2 = {**test_data}
            test_data_2["process_number"] = f"NORMAL-{int(datetime.now().timestamp())}-89.2024.8.26.0100"
            
            response = await client.post(
                f"{API_BASE_URL}/api/publications",
                json=test_data_2,
                headers={"Authorization": "Bearer dummy"}  # Usar token real
            )
            
            print(f"📊 Endpoint normal status: {response.status_code}")
            
        except Exception as e:
            print(f"📊 Endpoint normal: {e}")
    
    print("\n🎉 Teste de integração concluído!")
    return True


if __name__ == "__main__":
    asyncio.run(test_full_integration())
```

### Executar Testes

```bash
# Teste de integração completa
python test_integration.py

# Teste via Docker
docker-compose exec scraper python test_integration.py

# Logs em tempo real
docker-compose logs -f scraper
```

## 📊 Monitoramento da Integração

### Logs Estruturados

**Scraper** -> API:

```json
{
  "timestamp": "2024-03-17T10:30:00Z",
  "level": "INFO",
  "message": "📤 Enviando publicação: 1234567-89.2024.8.26.0100",
  "source": "scraper",
  "target": "api"
}
```

**API** <- Scraper:

```json
{
  "timestamp": "2024-03-17T10:30:01Z",
  "level": "INFO", 
  "message": "Publication creation from SCRAPER",
  "process_number": "1234567-89.2024.8.26.0100",
  "source": "SCRAPER",
  "ip": "172.18.0.3"
}
```

### Métricas de Integração

```bash
# Via API de métricas (se habilitada)
curl http://localhost:8000/admin/metrics

# Logs de performance
grep "Scraping concluído" logs/scraper_*.log
grep "SCRAPER" logs/api_*.log
```

## 🔧 Troubleshooting

### Problemas Comuns de Integração

**1. Erro de Conexão Refused**

```bash
❌ Connection refused to http://localhost:8000
```

**Solução**:

```bash
# Verificar se API está rodando
curl http://localhost:8000/health

# Em Docker, usar nome do serviço
API_BASE_URL=http://juscash-api:8000
```

**2. API Key Inválida**

```bash
❌ Invalid API Key
```

**Solução**:

```bash
# Verificar se as chaves são idênticas
grep SCRAPER_API_KEY backend/api/.env
grep SCRAPER_API_KEY backend/scraper/.env

# Verificar configuração na API
curl -H "X-API-Key: sua-chave" http://localhost:8000/api/scraper/publications
```

**3. Timeout de Rede**

```bash
❌ Timeout 30s exceeded
```

**Solução**:

```bash
# Aumentar timeout
API_TIMEOUT=60

# Verificar latência
ping localhost
docker-compose exec scraper ping juscash-api
```

**4. Erro de Validação**

```bash
❌ Process number is required
```

**Solução**:

```bash
# Verificar estrutura dos dados
cat logs/scraper_debug.log | grep "Enviando publicação"

# Testar com dados mínimos
python test_api_connection.py
```

### Debug Avançado

**Capturar todas as requisições**:

```python
# Adicionar em infrastructure/api/api_client_adapter.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Logs detalhados da API**:

```bash
# No backend/api/.env
LOG_LEVEL=debug

# Verificar logs
docker-compose logs api | grep SCRAPER
```

**Análise de rede**:

```bash
# Monitor de tráfego HTTP
docker-compose exec scraper tcpdump -i any port 8000

# Status de conexões
docker-compose exec scraper netstat -an | grep 8000
```

## 🚀 Deploy em Produção

### Configurações de Produção

**Arquivo**: `.env.production`

```bash
ENVIRONMENT=production

# API URLs seguras
API_BASE_URL=https://api.juscash.com
SCRAPER_API_KEY=sua-chave-muito-segura-aqui

# Performance
BROWSER_HEADLESS=true
SCRAPER_MAX_PAGES=50
API_TIMEOUT=60

# Logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### Docker Compose Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  scraper:
    image: juscash/dje-scraper:latest
    environment:
      - API_BASE_URL=https://api.juscash.com
      - SCRAPER_API_KEY=${SCRAPER_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - /var/log/juscash:/app/logs
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('${API_BASE_URL}/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Backup e Monitoramento

```bash
# Backup de logs
tar -czf scraper-logs-$(date +%Y%m%d).tar.gz logs/

# Monitoramento com Prometheus (opcional)
curl http://localhost:8000/admin/metrics

# Alertas personalizados
grep "❌" logs/scraper_*.log | wc -l
```

## 📈 Otimizações

### Performance

1. **Cache de Publicações**:

  ```python
  # Implementar cache local para evitar verificações desnecessárias
  cache_ttl = 3600  # 1 hora
  ```

2. **Batch Processing**:

  ```python
  # Enviar múltiplas publicações por requisição
  batch_size = 10
  ```

3. **Rate Limiting Inteligente**:

  ```python
  # Respeitar limites da API
  requests_per_minute = 100
  ```

### Escalabilidade

1. **Múltiplos Workers**:

  ```yaml
  # docker-compose.yml
  scraper:
    deploy:
      replicas: 3
  ```

1. **Load Balancing**:

  ```python
  # Distribuir carga entre múltiplas APIs
  api_endpoints = [
      "https://api1.juscash.com",
      "https://api2.juscash.com"
  ]
  ```

---

**🔗 Status da Integração**: ✅ Pronto para produção  
**📊 Compatibilidade**: API JusCash v1.0+  
**🚀 Deploy**: Docker Compose + Kubernetes ready
