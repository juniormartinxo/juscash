# 📝 Exemplos de Uso da API - JusCash

> Exemplos práticos e casos de uso da API do sistema JusCash

## 🔐 Autenticação

### Registro de Usuário

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva Santos",
    "email": "joao.silva@escritorio.com",
    "password": "MinhaSenh@123Forte"
  }'
```

**Resposta de Sucesso:**
```json
{
  "message": "Usuário criado com sucesso",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "João Silva Santos",
    "email": "joao.silva@escritorio.com",
    "created_at": "2024-03-20T10:30:00.000Z"
  }
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao.silva@escritorio.com",
    "password": "MinhaSenh@123Forte"
  }'
```

**Resposta de Sucesso:**
```json
{
  "message": "Login realizado com sucesso",
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900
  },
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "João Silva Santos",
    "email": "joao.silva@escritorio.com"
  }
}
```

### Renovação de Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## 📄 Gerenciamento de Publicações

### Listar Publicações (com Filtros)

```bash
# Busca básica
curl -X GET "http://localhost:8000/api/publications?page=1&limit=20" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtro por status
curl -X GET "http://localhost:8000/api/publications?status=NOVA&page=1&limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtro por data
curl -X GET "http://localhost:8000/api/publications?start_date=2024-03-01&end_date=2024-03-31" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por texto
curl -X GET "http://localhost:8000/api/publications?search=aposentadoria" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtros combinados
curl -X GET "http://localhost:8000/api/publications?status=LIDA&search=INSS&start_date=2024-03-01" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "data": {
    "publications": [
      {
        "id": "pub-123e4567-e89b-12d3-a456-426614174000",
        "process_number": "1234567-89.2024.8.26.0100",
        "publication_date": "2024-03-20T00:00:00.000Z",
        "availability_date": "2024-03-22T00:00:00.000Z",
        "authors": ["João Silva Santos", "Maria Oliveira Lima"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [
          {
            "name": "Dr. Carlos Advogado",
            "oab": "SP123456"
          }
        ],
        "gross_value": 50000,
        "net_value": 45000,
        "content": "Conteúdo da publicação...",
        "status": "NOVA",
        "created_at": "2024-03-22T08:30:00.000Z",
        "updated_at": "2024-03-22T08:30:00.000Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 95,
      "items_per_page": 20,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### Buscar Publicação por ID

```bash
curl -X GET "http://localhost:8000/api/publications/pub-123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Criar Nova Publicação

```bash
curl -X POST http://localhost:8000/api/publications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "process_number": "7890123-45.2024.8.26.0200",
    "publication_date": "2024-03-20T00:00:00.000Z",
    "availability_date": "2024-03-22T00:00:00.000Z",
    "authors": ["Ana Costa Silva", "Pedro Santos"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dra. Mariana Advocacia",
        "oab": "SP654321"
      }
    ],
    "gross_value": 75000,
    "net_value": 67500,
    "attorney_fees": 7500,
    "content": "Intimação para cumprimento de sentença...",
    "status": "NOVA"
  }'
```

### Atualizar Status de Publicação

```bash
# Mover para "Lida"
curl -X PATCH "http://localhost:8000/api/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "LIDA"
  }'

# Mover para "Enviar para Advogado"
curl -X PATCH "http://localhost:8000/api/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "ENVIAR_PARA_ADVOGADO"
  }'

# Finalizar (Concluído)
curl -X PATCH "http://localhost:8000/api/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "CONCLUIDO"
  }'
```

### Busca Avançada

```bash
# Busca por número de processo
curl -X GET "http://localhost:8000/api/publications/search?process_number=1234567-89.2024.8.26.0100" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por autor
curl -X GET "http://localhost:8000/api/publications/search?author=João Silva" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por faixa de valores
curl -X GET "http://localhost:8000/api/publications/search?min_value=10000&max_value=100000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca complexa
curl -X GET "http://localhost:8000/api/publications/search?search=aposentadoria&status=NOVA&min_value=50000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 📊 Endpoints de Utilidade

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2024-03-22T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": "connected",
    "redis": "connected"
  },
  "uptime": 3600,
  "memory": {
    "used": "256MB",
    "total": "512MB"
  }
}
```

### Informações da API

```bash
curl -X GET "http://localhost:8000/api"
```

**Resposta:**
```json
{
  "name": "JusCash API",
  "version": "1.0.0",
  "description": "API para gerenciamento de publicações DJE",
  "documentation": "/api/docs",
  "endpoints": {
    "auth": "/api/auth",
    "publications": "/api/publications",
    "health": "/health"
  }
}
```

## 🤖 Integração com Scraper

### Executar Scraping de Data Específica

```bash
curl -X POST "http://localhost:8000/api/scraper/run" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SCRAPER_API_KEY" \
  -d '{
    "date": "2024-03-20",
    "force": true
  }'
```

### Enviar Publicações do Scraper

```bash
curl -X POST "http://localhost:8000/api/scraper/publications" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SCRAPER_API_KEY" \
  -d '{
    "publications": [
      {
        "process_number": "1234567-89.2024.8.26.0100",
        "publication_date": "2024-03-20T00:00:00.000Z",
        "availability_date": "2024-03-22T00:00:00.000Z",
        "authors": ["João Silva Santos"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "gross_value": 50000,
        "net_value": 45000,
        "content": "Conteúdo completo da publicação..."
      }
    ]
  }'
```

## 📈 Casos de Uso Práticos

### 1. Workflow Completo de uma Publicação

```bash
# 1. Listar novas publicações
PUBLICATIONS=$(curl -s -X GET "http://localhost:8000/api/publications?status=NOVA&limit=1" \
  -H "Authorization: Bearer $TOKEN")

# 2. Extrair ID da primeira publicação
PUB_ID=$(echo $PUBLICATIONS | jq -r '.data.publications[0].id')

# 3. Marcar como lida
curl -X PATCH "http://localhost:8000/api/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "LIDA"}'

# 4. Enviar para advogado
curl -X PATCH "http://localhost:8000/api/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "ENVIAR_PARA_ADVOGADO"}'

# 5. Finalizar
curl -X PATCH "http://localhost:8000/api/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "CONCLUIDO"}'
```

### 2. Relatório de Publicações por Período

```bash
# Publicações do mês atual
START_DATE=$(date +%Y-%m-01)
END_DATE=$(date +%Y-%m-%d)

curl -X GET "http://localhost:8000/api/publications?start_date=$START_DATE&end_date=$END_DATE&limit=100" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.publications | length'
```

### 3. Busca por Processos de Alto Valor

```bash
# Processos com valor maior que R$ 100.000
curl -X GET "http://localhost:8000/api/publications/search?min_value=100000&status=NOVA" \
  -H "Authorization: Bearer $TOKEN"
```

## ⚠️ Tratamento de Erros

### Erro de Autenticação (401)

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token inválido ou expirado",
    "details": "Por favor, faça login novamente"
  }
}
```

### Erro de Validação (400)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos",
    "details": {
      "email": "Email deve ter formato válido",
      "password": "Senha deve ter pelo menos 8 caracteres"
    }
  }
}
```

### Erro de Rate Limit (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Muitas requisições",
    "details": "Tente novamente em 15 minutos"
  }
}
```

## 📚 SDKs e Libraries

### JavaScript/TypeScript

```javascript
// Exemplo de uso com axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Buscar publicações
const publications = await api.get('/publications?status=NOVA');

// Atualizar status
await api.patch(`/publications/${id}/status`, { status: 'LIDA' });
```

### Python

```python
import requests

class JusCashAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get_publications(self, status=None, page=1, limit=20):
        params = {'page': page, 'limit': limit}
        if status:
            params['status'] = status
        
        response = requests.get(
            f'{self.base_url}/publications',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def update_status(self, pub_id, status):
        response = requests.patch(
            f'{self.base_url}/publications/{pub_id}/status',
            headers=self.headers,
            json={'status': status}
        )
        return response.json()
```

---

Para mais exemplos e detalhes técnicos, consulte a [Documentação Técnica](./TECHNICAL-DOCS.md) ou acesse a documentação interativa em `/api/docs` quando o sistema estiver rodando. 