# API Key para Scraper - Documentação Completa

## Visão Geral

Esta implementação adiciona um endpoint específico para scrapers/bots inserirem publicações sem precisar de autenticação de usuário via JWT. O sistema usa autenticação via API Key através do header `X-API-Key`.

## Arquivos Implementados

### 1. Middleware de API Key

**Arquivo:** `src/infrastructure/web/middleware/api-key.middleware.ts`

```typescript
export class ApiKeyMiddleware {
  static validateScraperApiKey = (req, res, next) => {
    // Valida X-API-Key header contra SCRAPER_API_KEY
    // Logs de auditoria para segurança
    // Adiciona req.apiKeySource = 'SCRAPER' para identificação
  }
}
```

### 2. Configuração de Ambiente

**Arquivo:** `src/shared/config/environment.ts`

Adicionado:

```typescript
// No envSchema
SCRAPER_API_KEY: z.string(),

// No config export
scraper: {
  apiKey: env.SCRAPER_API_KEY,
}
```

### 3. Rotas do Scraper

**Arquivo:** `src/infrastructure/web/routes/scraper.route.ts`

```typescript
export function createScraperRoutes(publicationController: PublicationController): Router {
  // Rate limiting específico para scraper (1000 req/15min)
  // Validação de API Key
  // POST /publications endpoint
}
```

### 4. Controller Atualizado

**Arquivo:** `src/infrastructure/web/controllers/publication.controller.ts`

Adicionado método:

```typescript
createPublicationFromScraper = asyncHandler(async (req, res) => {
  // Logs específicos para auditoria do scraper
  // Mesma lógica de validação e criação
  // Identificação clara da origem "SCRAPER"
})
```

### 5. Integração na Aplicação

**Arquivo:** `src/app.ts`

```typescript
// Nova rota adicionada
this.app.use('/api/scraper', createScraperRoutes(
  this.container.publicationController
))
```

## Configuração Necessária

### Variável de Ambiente

Adicione no seu arquivo `.env`:

```bash
SCRAPER_API_KEY="sua-chave-secreta-aqui-faça-ela-longa-e-segura"
```

**Recomendações para a API Key:**

- Mínimo 32 caracteres
- Mistura de letras, números e símbolos
- Exemplo: `scraper_2024_a8f3k9m2x7q1w5e8r4t6y9u3i0p2s5d7f1g4h6j8k0l3z9x2c4v6b8n1m5q7w9e3r5t7y1u4i6o8p0`

## Endpoints Disponíveis

### POST /api/scraper/publications

**Autenticação:** API Key via header `X-API-Key`

**Headers obrigatórios:**

```txt
Content-Type: application/json
X-API-Key: sua-api-key-aqui
```

**Body:** Mesmo formato do endpoint normal de publicações

**Rate Limiting:** 1000 requests por 15 minutos (mais permissivo que usuários normais)

## Exemplos de Uso

### 1. cURL

```bash
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key-aqui" \
  -d '{
    "process_number": "1234567-89.2024.8.26.0100",
    "publicationDate": "2024-03-15T00:00:00.000Z",
    "availability_date": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva Santos", "Maria Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dr. Carlos Advogado",
        "oab": "123456"
      }
    ],
    "gross_value": 150000,
    "net_value": 135000,
    "interest_value": 10000,
    "attorney_fees": 5000,
    "content": "Conteúdo completo da publicação...",
    "status": "NOVA",
    "scraping_source": "DJE-SP",
    "caderno": "3",
    "instancia": "1",
    "local": "Capital",
    "parte": "1",
    "extraction_metadata": {
      "extraction_date": "2024-03-17T10:30:00.000Z",
      "source_url": "https://dje.tjsp.jus.br/...",
      "confidence_score": 0.95
    }
  }'
```

### 2. JavaScript/Node.js

```javascript
const axios = require('axios');

async function createPublicationFromScraper() {
  try {
    const publicationData = {
      process_number: '1234567-89.2024.8.26.0100',
      publicationDate: '2024-03-15T00:00:00.000Z',
      availability_date: '2024-03-17T00:00:00.000Z',
      authors: ['João Silva Santos', 'Maria Oliveira'],
      defendant: 'Instituto Nacional do Seguro Social - INSS',
      lawyers: [
        { name: 'Dr. Carlos Advogado', oab: '123456' }
      ],
      gross_value: 150000,
      net_value: 135000,
      interest_value: 10000,
      attorney_fees: 5000,
      content: 'Conteúdo completo da publicação...',
      status: 'NOVA',
      scraping_source: 'DJE-SP',
      extraction_metadata: {
        extraction_date: '2024-03-17T10:30:00.000Z',
        source_url: 'https://dje.tjsp.jus.br/...',
        confidence_score: 0.95
      }
    };

    const response = await axios.post('http://localhost:3000/api/scraper/publications', publicationData, {
      headers: {
        'X-API-Key': process.env.SCRAPER_API_KEY,
        'Content-Type': 'application/json'
      }
    });

    console.log('Publicação criada via scraper:', response.data);
    return response.data;

  } catch (error) {
    console.error('Erro ao criar publicação via scraper:', error.response?.data || error.message);
    throw error;
  }
}

// Executar
createPublicationFromScraper();
```

### 3. Python

```python
import requests
import json
import os

def create_publication_from_scraper():
    url = "http://localhost:3000/api/scraper/publications"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": os.getenv("SCRAPER_API_KEY")
    }
    
    data = {
        "process_number": "1234567-89.2024.8.26.0100",
        "publicationDate": "2024-03-15T00:00:00.000Z",
        "availability_date": "2024-03-17T00:00:00.000Z",
        "authors": ["João Silva Santos", "Maria Oliveira"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [
            {"name": "Dr. Carlos Advogado", "oab": "123456"}
        ],
        "gross_value": 150000,
        "net_value": 135000,
        "interest_value": 10000,
        "attorney_fees": 5000,
        "content": "Conteúdo completo da publicação...",
        "status": "NOVA",
        "scraping_source": "DJE-SP",
        "extraction_metadata": {
            "extraction_date": "2024-03-17T10:30:00.000Z",
            "source_url": "https://dje.tjsp.jus.br/...",
            "confidence_score": 0.95
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print("Publicação criada via scraper:", response.json())
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar publicação via scraper: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta do servidor: {e.response.text}")
        raise

# Executar
if __name__ == "__main__":
    create_publication_from_scraper()
```

## Tratamento de Erros

### 1. API Key não fornecida (400)

```json
{
  "success": false,
  "error": "X-API-Key header is required"
}
```

### 2. API Key inválida (401)

```json
{
  "success": false,
  "error": "Invalid API Key"
}
```

### 3. Erro de validação de dados (400)

```json
{
  "success": false,
  "error": "Process number is required"
}
```

### 4. Rate limit excedido (429)

```json
{
  "success": false,
  "error": "Too many requests",
  "retryAfter": 300
}
```

### 5. Processo duplicado (500)

```json
{
  "success": false,
  "error": "Unique constraint failed on the fields: (`process_number`)"
}
```

## Segurança Implementada

### 1. Logs de Auditoria

- Todas as tentativas de autenticação são logadas
- Logs específicos identificam origem "SCRAPER"
- IPs e User-Agents são registrados
- Sucessos e falhas são auditados

### 2. Rate Limiting

- Limite específico para scraper: 1000 requests/15min
- Mais permissivo que usuários normais
- Baseado em IP + identificação de origem

### 3. Validação de Dados

- Mesma validação rigorosa do endpoint normal
- Schema validation com Zod
- Sanitização de inputs

### 4. Configuração Segura

- API Key obrigatória via variável de ambiente
- Não exposição da chave em logs (apenas primeiros 8 caracteres)
- Verificação de configuração no startup

## Diferenças do Endpoint Normal

| Aspecto | Endpoint Normal | Endpoint Scraper |
|---------|----------------|------------------|
| **Autenticação** | JWT Token (Bearer) | API Key (X-API-Key) |
| **Rota** | `POST /api/publications` | `POST /api/scraper/publications` |
| **Rate Limit** | 100 req/15min | 1000 req/15min |
| **Logs** | Logs normais | Logs com identificação "SCRAPER" |
| **Validação** | Mesma | Mesma |
| **Resposta** | Mesma | Mesma |

## Monitoramento e Logs

### Logs de Sucesso

```txt
Publication creation from SCRAPER: {
  process_number: "1234567-89.2024.8.26.0100",
  source: "SCRAPER",
  timestamp: "2024-03-17T10:30:00.000Z",
  ip: "192.168.1.100"
}
```

### Logs de Erro

```txt
Publication creation failed from SCRAPER: {
  error: "Process number is required",
  process_number: undefined,
  source: "SCRAPER",
  ip: "192.168.1.100"
}
```

### Logs de Autenticação

```txt
Scraper API Key validated successfully: {
  ip: "192.168.1.100",
  url: "/api/scraper/publications",
  method: "POST",
  source: "SCRAPER"
}
```

## Testes Recomendados

### 1. Teste de Autenticação

```bash
# Sem API Key
curl -X POST http://localhost:3000/api/scraper/publications

# API Key inválida
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "X-API-Key: invalid-key"

# API Key válida
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "X-API-Key: sua-api-key-aqui"
```

### 2. Teste de Validação

```bash
# Dados inválidos
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "X-API-Key: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{}'

# Dados válidos
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "X-API-Key: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{"process_number": "123", "availability_date": "2024-03-17", "authors": ["Test"], "content": "Test"}'
```

### 3. Teste de Rate Limiting

```bash
# Script para testar rate limiting
for i in {1..1001}; do
  curl -X POST http://localhost:3000/api/scraper/publications \
    -H "X-API-Key: sua-api-key-aqui" \
    -H "Content-Type: application/json" \
    -d '{"process_number": "'$i'", "availability_date": "2024-03-17", "authors": ["Test"], "content": "Test"}'
done
```

## Melhorias Futuras Sugeridas

### 1. Múltiplas API Keys

- Suporte a diferentes scrapers com chaves específicas
- Identificação por fonte (DJE-SP, DJE-RJ, etc.)

### 2. Rotação de API Keys

- Sistema de rotação automática de chaves
- Múltiplas chaves válidas simultaneamente

### 3. Rate Limiting Avançado

- Limites diferentes por tipo de scraper
- Rate limiting baseado em recursos (CPU, memória)

### 4. Métricas Específicas

- Dashboard de monitoramento para scrapers
- Métricas de performance e erro por fonte

### 5. Webhook de Notificação

- Notificações em tempo real de novas publicações
- Integração com sistemas externos

## Conclusão

A implementação fornece uma solução robusta e segura para permitir que scrapers insiram publicações sem comprometer a segurança do sistema. O uso de API Keys, logs de auditoria e rate limiting específico garante controle total sobre o acesso automatizado à API.

A solução mantém a mesma qualidade de validação e processamento do endpoint normal, mas com identificação clara da origem e logs específicos para auditoria e monitoramento.
