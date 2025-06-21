# Autenticação Segura da API do Scraper

## ⚠️ **ATUALIZAÇÃO DE SEGURANÇA - DEZEMBRO 2024**

**IMPORTANTE**: O acesso direto do frontend à API do scraper foi substituído por um sistema de proxy seguro para evitar exposição de API keys no navegador.

## 🔐 **Nova Arquitetura de Segurança**

### Fluxo Seguro

```
Frontend → API Principal (JWT) → API Scraper (API Key)
```

### Antiga Abordagem (INSEGURA) ❌

```
Frontend → API Scraper (API Key exposta)
```

## 🛡️ **Sistema de Proxy Implementado**

### Endpoints do Proxy (API Principal)

- `GET /api/scraper-proxy/status` - Status do scraper
- `POST /api/scraper-proxy/run` - Iniciar scraping  
- `POST /api/scraper-proxy/force-stop` - Parar scraping
- `POST /api/scraper-proxy/today` - Scraping do dia atual

### Autenticação Necessária

- **Frontend**: JWT Token (Bearer Authentication)
- **API Principal**: API Key para comunicar com scraper

## 📝 **Configuração**

### Variáveis de Ambiente

#### API Principal (backend/api)

```bash
# API Key para comunicar com o scraper
SCRAPER_API_KEY=scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP

# URL da API do scraper
SCRAPER_API_URL=http://localhost:5000
```

#### API do Scraper (backend/scraper)

```bash
# API Key para autenticar requisições
SCRAPER_API_KEY=scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP

# CORS para API principal
CORS_ORIGIN=http://localhost:3000
```

#### Frontend

```bash
# ✅ REMOVIDO: VITE_SCRAPER_API_KEY (não é mais necessário)
# Frontend agora usa JWT para autenticar com API principal
```

## 🔒 **Benefícios de Segurança**

### ✅ **Problemas Resolvidos**

- **API Key oculta**: Nunca exposta no navegador
- **Código seguro**: Não há secrets no JavaScript
- **DevTools seguro**: Nenhuma informação sensível
- **Build seguro**: Sem keys no bundle de produção

### 🛡️ **Camadas de Proteção**

1. **JWT Authentication**: Frontend → API Principal
2. **API Key Protection**: API Principal → API Scraper  
3. **Rate Limiting**: Específico para operações do scraper
4. **CORS Restrictivo**: Apenas origens autorizadas

## 💻 **Implementação Frontend**

### Antes (INSEGURO) ❌

```typescript
// ❌ API key exposta no navegador!
const headers = {
  'X-API-Key': 'scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP'
}

fetch('http://localhost:5000/status', { headers })
```

### Agora (SEGURO) ✅

```typescript
// ✅ Apenas JWT, API key fica no servidor
const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
fetch(`${API_BASE_URL}/scraper-proxy/status`, {
  headers: getAuthHeaders()
})
```

## 🔧 **Implementação Backend (Proxy)**

### Middleware de Segurança

```typescript
// Autenticação JWT obrigatória
router.use(authMiddleware.authenticate)

// Rate limiting específico (5 min, 10 requests)
router.use(scraperRateLimit.middleware)
```

### Exemplo de Endpoint Proxy

```typescript
router.get('/status', asyncHandler(async (req: Request, res: Response) => {
  // API key fica segura no servidor
  const response = await fetch(`${SCRAPER_API_URL}/status`, {
    headers: {
      'X-API-Key': SCRAPER_API_KEY
    }
  })
  
  const data = await response.json()
  res.json(ApiResponseBuilder.success(data))
}))
```

## 📊 **Monitoramento**

### Logs de Segurança

```
[INFO] Proxy request: GET /api/scraper-proxy/status - User: john@example.com
[WARN] Unauthorized proxy attempt: Missing JWT token
[ERROR] Scraper API unreachable: Connection refused
```

### Códigos de Status

- **200**: Requisição proxy bem-sucedida
- **401**: JWT token ausente/inválido  
- **502**: Erro de comunicação com scraper
- **503**: Serviço do scraper indisponível

## 🚀 **Deployment**

### Checklist de Segurança

- [ ] `SCRAPER_API_KEY` configurada nos dois serviços
- [ ] `SCRAPER_API_URL` apontando corretamente
- [ ] CORS configurado apenas para origens necessárias
- [ ] JWT secrets diferentes em cada ambiente
- [ ] Rate limiting ativo em produção

### Testando a Segurança

```bash
# ❌ Tentativa direta (deve falhar)
curl -H "X-API-Key: invalid" http://localhost:5000/status

# ✅ Via proxy com JWT (deve funcionar)  
curl -H "Authorization: Bearer $JWT_TOKEN" http://localhost:8000/api/scraper-proxy/status
```

## 🆘 **Troubleshooting**

### Erro: "Serviço do scraper indisponível"

```bash
# Verificar se scraper está rodando
curl http://localhost:5000/

# Verificar logs da API principal
tail -f backend/api/logs/app.log
```

### Erro: "Erro de autenticação com o scraper"

```bash
# Verificar se API keys coincidem
echo $SCRAPER_API_KEY

# Testar comunicação direta
curl -H "X-API-Key: $SCRAPER_API_KEY" http://localhost:5000/status
```

## 📋 **Exemplos de Uso**

### 1. Frontend (React/TypeScript)

```typescript
// Obter status do scraper
const checkStatus = async () => {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  const response = await fetch(`${API_BASE_URL}/scraper-proxy/status`, {
    headers: getAuthHeaders()
  })
  const result = await response.json()
  return result.data
}

// Iniciar scraping
const startScraping = async (startDate: string, endDate: string) => {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  const response = await fetch(`${API_BASE_URL}/scraper-proxy/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      start_date: startDate,
      end_date: endDate,
      headless: true
    })
  })
  return response.json()
}
```

### 2. cURL (com JWT)

```bash
# Obter JWT token primeiro
API_URL=${VITE_API_URL:-"http://localhost:8000/api"}
JWT_TOKEN=$(curl -X POST ${API_URL}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.data.token')

# Usar o proxy
curl -H "Authorization: Bearer $JWT_TOKEN" \
  ${API_URL}/scraper-proxy/status
```

## 🔄 **Migração de Projetos Existentes**

### Passos da Migração

1. **Configurar variáveis de ambiente**:
   - Adicionar `SCRAPER_API_KEY` na API principal
   - Remover `VITE_SCRAPER_API_KEY` do frontend

2. **Atualizar frontend**:
   - Trocar URLs diretas por rotas de proxy
   - Usar JWT authentication ao invés de API key

3. **Testar comunicação**:
   - Verificar se API principal consegue se comunicar com scraper
   - Validar autenticação JWT no frontend

---

**✅ MIGRAÇÃO CONCLUÍDA**: Sistema de proxy seguro implementado com sucesso. API keys nunca mais serão expostas no frontend.
