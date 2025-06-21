# 📝 Exemplos de Uso da API - JusCash

> Exemplos práticos e casos de uso da API do sistema JusCash para gerenciamento de publicações DJE

## 🚀 **URL Base da API**

```txt
${API_BASE_URL}
```

**Documentação Interativa:** `${API_BASE_URL}/docs`  
**Health Check:** `${API_BASE_URL}/health`

## 🔐 **Autenticação**

### **Cadastro de Usuário**

```bash
curl -X POST ${API_BASE_URL}/auth/register \
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
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "João Silva Santos",
      "email": "joao.silva@escritorio.com",
      "isActive": true,
      "createdAt": "2024-03-20T10:30:00.000Z",
      "updatedAt": "2024-03-20T10:30:00.000Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
}
```

### **Login**

```bash
curl -X POST ${API_BASE_URL}/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao.silva@escritorio.com",
    "password": "MinhaSenh@123Forte"
  }'
```

**Resposta de Sucesso:**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "João Silva Santos",
      "email": "joao.silva@escritorio.com"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
}
```

### **Renovação de Token**

```bash
curl -X POST ${API_BASE_URL}/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### **Logout**

```bash
curl -X POST ${API_BASE_URL}/auth/logout \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 📄 **Gerenciamento de Publicações**

### **Listar Publicações (com Filtros)**

```bash
# Busca básica com paginação
curl -X GET "${API_BASE_URL}/publications?page=1&limit=30" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtro por status
curl -X GET "${API_BASE_URL}/publications?status=NOVA&page=1&limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtro por data (usando startDate e endDate)
curl -X GET "${API_BASE_URL}/publications?startDate=2024-03-01&endDate=2024-03-31" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por texto no conteúdo
curl -X GET "${API_BASE_URL}/publications?search=aposentadoria" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Filtros combinados
curl -X GET "${API_BASE_URL}/publications?status=LIDA&search=INSS&startDate=2024-03-01" \
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
        "publicationDate": "2024-03-20T00:00:00.000Z",
        "availability_date": "2024-03-22T00:00:00.000Z",
        "authors": ["João Silva Santos", "Maria Oliveira Lima"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [
          {
            "name": "Dr. Carlos Advogado",
            "oab": "SP123456"
          }
        ],
        "gross_value": 5000000,
        "net_value": 4500000,
        "interest_value": 300000,
        "attorney_fees": 200000,
        "content": "Conteúdo da publicação DJE sobre RPV...",
        "status": "NOVA",
        "createdAt": "2024-03-22T08:30:00.000Z",
        "updatedAt": "2024-03-22T08:30:00.000Z"
      }
    ],
    "pagination": {
      "current": 1,
      "total": 5,
      "count": 142,
      "perPage": 30
    }
  }
}
```

### **Buscar Publicação por ID**

```bash
curl -X GET "${API_BASE_URL}/publications/pub-123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### **Criar Nova Publicação**

```bash
curl -X POST ${API_BASE_URL}/publications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "process_number": "7890123-45.2024.8.26.0200",
    "publicationDate": "2024-03-20T00:00:00.000Z",
    "availability_date": "2024-03-22T00:00:00.000Z",
    "authors": ["Ana Costa Silva", "Pedro Santos"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dra. Mariana Advocacia",
        "oab": "SP654321"
      }
    ],
    "gross_value": 7500000,
    "net_value": 6750000,
    "interest_value": 450000,
    "attorney_fees": 300000,
    "content": "Intimação para cumprimento de sentença conforme decisão judicial...",
    "status": "NOVA"
  }'
```

### **Atualizar Status de Publicação (Kanban)**

```bash
# Mover para "Lida"
curl -X PUT "${API_BASE_URL}/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "LIDA"
  }'

# Mover para "Enviada para Advogado"
curl -X PUT "${API_BASE_URL}/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "ENVIADA_PARA_ADV"
  }'

# Finalizar (Concluída)
curl -X PUT "${API_BASE_URL}/publications/pub-123e4567-e89b-12d3-a456-426614174000/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "CONCLUIDA"
  }'
```

### **Busca Avançada**

```bash
# Busca por número de processo específico
curl -X GET "${API_BASE_URL}/publications/search?process_number=1234567-89.2024.8.26.0100" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por autor
curl -X GET "${API_BASE_URL}/publications/search?author=João Silva" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca por faixa de valores (em centavos)
curl -X GET "${API_BASE_URL}/publications/search?min_value=1000000&max_value=10000000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# Busca complexa combinada
curl -X GET "${API_BASE_URL}/publications/search?search=aposentadoria&status=NOVA&min_value=5000000" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 🤖 **Integração com Scrapers (API Key)**

### **Criar Publicação via Scraper**

```bash
curl -X POST ${API_BASE_URL}/scraper/publications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key-do-scraper-aqui" \
  -d '{
    "process_number": "1234567-89.2024.8.26.0100",
    "publicationDate": "2024-03-15T00:00:00.000Z",
    "availability_date": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva Santos", "Maria Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dr. Carlos Advogado",
        "oab": "SP123456"
      }
    ],
    "gross_value": 15000000,
    "net_value": 13500000,
    "interest_value": 1000000,
    "attorney_fees": 500000,
    "content": "Conteúdo completo da publicação extraída do DJE-SP...",
    "status": "NOVA",
    "scraping_source": "DJE-SP",
    "extraction_metadata": {
      "extraction_date": "2024-03-17T10:30:00.000Z",
      "source_url": "https://dje.tjsp.jus.br/...",
      "confidence_score": 0.95
    }
  }'
```

**Configuração da API Key:**

```bash
# Adicione no arquivo .env
SCRAPER_API_KEY="sua-chave-secreta-longa-e-segura-aqui"
```

### **Vantagens do Endpoint Scraper:**

- ✅ **Sem login** - Não requer autenticação de usuário
- ✅ **Rate limiting específico** - 1000 req/15min vs 100 para usuários
- ✅ **Logs de auditoria** - Identificação "SCRAPER" nos logs
- ✅ **Mesma validação** - Segurança mantida

## 📊 **Endpoints de Utilidade**

### **Health Check**

```bash
curl -X GET "${API_SERVER_URL}/health"
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
  "uptime": 3600
}
```

### **Informações da API**

```bash
curl -X GET "${API_BASE_URL}"
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
    "scraper": "/api/scraper",
    "health": "/health"
  }
}
```

## 📈 **Casos de Uso Práticos**

### **1. Workflow Completo Kanban**

```bash
# Salvar token para reutilização
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 1. Listar novas publicações
PUBLICATIONS=$(curl -s -X GET "${API_BASE_URL}/publications?status=NOVA&limit=1" \
  -H "Authorization: Bearer $TOKEN")

# 2. Extrair ID da primeira publicação
PUB_ID=$(echo $PUBLICATIONS | jq -r '.data.publications[0].id')

# 3. Marcar como lida
curl -X PUT "${API_BASE_URL}/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "LIDA"}'

# 4. Enviar para advogado
curl -X PUT "${API_BASE_URL}/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "ENVIADA_PARA_ADV"}'

# 5. Finalizar processo
curl -X PUT "${API_BASE_URL}/publications/$PUB_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "CONCLUIDA"}'
```

### **2. Relatório de Publicações por Período**

```bash
# Publicações do mês atual
START_DATE=$(date +%Y-%m-01)
END_DATE=$(date +%Y-%m-%d)

# Obter total de publicações
curl -X GET "${API_BASE_URL}/publications?startDate=$START_DATE&endDate=$END_DATE&limit=100" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.pagination.count'

# Publicações por status
curl -X GET "${API_BASE_URL}/publications?startDate=$START_DATE&endDate=$END_DATE&status=NOVA" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.publications | length'
```

### **3. Busca por Processos de Alto Valor**

```bash
# Processos com valor maior que R$ 100.000 (10.000.000 centavos)
curl -X GET "${API_BASE_URL}/publications/search?min_value=10000000&status=NOVA" \
  -H "Authorization: Bearer $TOKEN"

# Processos de valor muito alto (R$ 500.000+)
curl -X GET "${API_BASE_URL}/publications/search?min_value=50000000" \
  -H "Authorization: Bearer $TOKEN"
```

### **4. Integração Automatizada (Scraper)**

```bash
# Script para inserção automatizada via scraper
API_KEY="sua-api-key-do-scraper"

curl -X POST ${API_BASE_URL}/scraper/publications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "process_number": "0001234-56.2024.8.26.0100",
    "availability_date": "2024-03-22T00:00:00.000Z",
    "authors": ["Automatizado Script"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "gross_value": 2500000,
    "net_value": 2250000,
    "content": "Publicação inserida automaticamente via scraper...",
    "status": "NOVA",
    "scraping_source": "DJE-SP-AUTOMATED"
  }'
```

## ⚠️ **Tratamento de Erros**

### **Erro de Autenticação (401)**

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token inválido ou expirado",
    "details": "Por favor, faça login novamente"
  }
}
```

### **Erro de Validação (400)**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR", 
    "message": "Dados inválidos",
    "details": {
      "process_number": "Número do processo é obrigatório",
      "availability_date": "Data de disponibilidade deve estar no formato ISO"
    }
  }
}
```

### **Erro de API Key (401)**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_API_KEY",
    "message": "X-API-Key header é obrigatório",
    "details": "Configure SCRAPER_API_KEY no arquivo .env"
  }
}
```

### **Erro de Rate Limit (429)**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Muitas requisições",
    "details": "Limite: 100 req/15min para usuários, 1000 req/15min para scrapers"
  }
}
```

### **Erro de Processo Duplicado (409)**

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_PROCESS",
    "message": "Processo já cadastrado",
    "details": "process_number deve ser único"
  }
}
```

## 💻 **Bibliotecas e SDKs**

### **JavaScript/TypeScript**

```javascript
import axios from 'axios';

class JusCashAPI {
  constructor(baseURL = '${API_BASE_URL}', token = null) {
    this.api = axios.create({
      baseURL,
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
  }

  // Autenticação
  async login(email, password) {
    const response = await this.api.post('/auth/login', { email, password });
    this.api.defaults.headers['Authorization'] = `Bearer ${response.data.data.tokens.accessToken}`;
    return response.data;
  }

  // Listar publicações
  async getPublications(params = {}) {
    const response = await this.api.get('/publications', { params });
    return response.data;
  }

  // Atualizar status
  async updateStatus(id, status) {
    const response = await this.api.put(`/publications/${id}/status`, { status });
    return response.data;
  }

  // Criar publicação
  async createPublication(data) {
    const response = await this.api.post('/publications', data);
    return response.data;
  }
}

// Uso
const api = new JusCashAPI();
await api.login('user@example.com', 'password');
const publications = await api.getPublications({ status: 'NOVA', limit: 10 });
```

### **Python**

```python
import requests
from typing import Optional, Dict, Any

class JusCashAPI:
    def __init__(self, base_url: str = '${API_BASE_URL}', token: Optional[str] = None):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f'{self.base_url}/auth/login',
            json={'email': email, 'password': password}
        )
        response.raise_for_status()
        data = response.json()
        
        # Atualizar token nos headers
        token = data['data']['tokens']['accessToken']
        self.headers['Authorization'] = f'Bearer {token}'
        
        return data
    
    def get_publications(self, **params) -> Dict[str, Any]:
        response = requests.get(
            f'{self.base_url}/publications',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def update_status(self, pub_id: str, status: str) -> Dict[str, Any]:
        response = requests.put(
            f'{self.base_url}/publications/{pub_id}/status',
            headers=self.headers,
            json={'status': status}
        )
        response.raise_for_status()
        return response.json()
    
    def create_publication_scraper(self, data: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
        response = requests.post(
            f'{self.base_url}/scraper/publications',
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

# Uso
api = JusCashAPI()
api.login('user@example.com', 'password')
publications = api.get_publications(status='NOVA', limit=20)
```

## 📋 **Modelo de Dados Atualizado**

### **Publication**

```typescript
interface Publication {
  id: string;
  process_number: string;           // Único, obrigatório
  publicationDate?: Date;           // Data da publicação
  availability_date: Date;          // Data de disponibilidade (obrigatório)
  authors: string[];                // Array de autores (obrigatório)
  defendant: string;                // Padrão: "INSS"
  lawyers?: Array<{                 // Array de advogados
    name: string;
    oab: string;
  }>;
  gross_value?: number;             // Valor bruto em centavos
  net_value?: number;               // Valor líquido em centavos
  interest_value?: number;          // Valor de juros em centavos
  attorney_fees?: number;           // Honorários em centavos
  content: string;                  // Conteúdo (obrigatório)
  status: 'NOVA' | 'LIDA' | 'ENVIADA_PARA_ADV' | 'CONCLUIDA';
  createdAt: Date;
  updatedAt: Date;
}
```

### **User**

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

## 🔗 **Links Úteis**

- **[README Técnico da API](../../backend/api/README.md)** - Documentação completa para desenvolvedores
- **[Integração com Scrapers](./SCRAPER-INTEGRATION.md)** - Documentação técnica da API Key
- **[Documentação Técnica](./TECHNICAL-DOCS.md)** - Arquitetura e implementação

---

**📚 Documentação de exemplos da API JusCash** | **Sistema de gerenciamento de publicações DJE**
