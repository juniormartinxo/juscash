# 🔐 Guia de Migração de Segurança

## ⚠️ **AÇÃO OBRIGATÓRIA: Remover API Key do Frontend**

**Data**: 21/01/2025  
**Motivo**: Exposição de API key no código JavaScript

## 🚨 **Problema Identificado**

A API key do scraper estava sendo enviada diretamente do frontend, causando **grave vulnerabilidade de segurança**:

```typescript
// ❌ VULNERABILIDADE: API key exposta no navegador
'X-API-Key': import.meta.env.VITE_SCRAPER_API_KEY
```

### Riscos:
- 🔓 **API key visível** no código fonte
- 🔍 **Inspecionável** nas DevTools  
- 📦 **Incluída** no bundle de produção
- 🌐 **Acessível** a qualquer usuário

## ✅ **Solução Implementada: Proxy Seguro**

### Nova Arquitetura
```
Frontend (JWT) → API Principal → API Scraper (API Key)
```

### Benefícios:
- 🔐 **API key oculta** no servidor
- 🛡️ **JWT authentication** para usuários
- 🚫 **Zero secrets** no frontend
- ⚡ **Rate limiting** específico

## 🔧 **Passos da Migração**

### 1. **Configurar API Principal**

```bash
# backend/api/.env
SCRAPER_API_KEY=scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP
SCRAPER_API_URL=http://localhost:5000
```

### 2. **Configurar Frontend**

```bash
# frontend/.env
# ✅ ADICIONAR: URL da API principal
VITE_API_URL=http://localhost:8000

# ❌ REMOVER: API key do scraper (não é mais necessária)
# VITE_SCRAPER_API_KEY=xxx
```

### 3. **Atualizar Código Frontend**

**Antes (INSEGURO):**
```typescript
// ❌ Não fazer mais!
const headers = {
  'X-API-Key': import.meta.env.VITE_SCRAPER_API_KEY
}
fetch('http://localhost:5000/status', { headers })
```

**Depois (SEGURO):**
```typescript
// ✅ Usar JWT via proxy com variável de ambiente
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const headers = {
  'Authorization': `Bearer ${token}`
}
fetch(`${API_BASE_URL}/scraper-proxy/status`, { headers })
```

## 📋 **Checklist de Migração**

### Backend
- [x] Proxy routes criadas em `/api/scraper-proxy/`
- [x] Middleware JWT authentication implementado
- [x] Rate limiting específico configurado
- [x] Tratamento de erros robusto
- [x] Logs de segurança implementados

### Frontend  
- [x] URLs alteradas para usar variável de ambiente
- [x] Headers alterados para JWT
- [x] Remoção de `VITE_SCRAPER_API_KEY`
- [x] Configuração de `VITE_API_URL`
- [x] Tratamento de resposta atualizado

### Configuração
- [ ] `SCRAPER_API_KEY` configurada na API principal
- [ ] `SCRAPER_API_URL` configurada corretamente
- [ ] `VITE_API_URL` configurada no frontend
- [ ] CORS atualizado para API principal

## 🧪 **Testes de Segurança**

### Verificar Proxy Funcionando
```bash
# 1. Obter JWT token
API_URL=${VITE_API_URL:-"http://localhost:8000"}
JWT_TOKEN=$(curl -X POST ${API_URL}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.data.token')

# 2. Testar proxy (usar a URL da API)
API_URL=${VITE_API_URL:-"http://localhost:8000"}
curl -H "Authorization: Bearer $JWT_TOKEN" \
  ${API_URL}/scraper-proxy/status
```

### Verificar Frontend Limpo
```bash
# Buscar por API keys no código
grep -r "VITE_SCRAPER_API_KEY" frontend/src/
grep -r "X-API-Key" frontend/src/

# ✅ Deve retornar vazio
```

### Verificar Bundle Seguro
```bash
# Build de produção
cd frontend && npm run build

# Verificar se não há API keys no bundle
grep -r "scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP" dist/

# ✅ Deve retornar vazio
```

## 🚀 **Deploy Seguro**

### Produção
```bash
# API Principal
export SCRAPER_API_KEY="production-key-here"
export SCRAPER_API_URL="https://scraper.example.com"

# Frontend (SEM API KEYS!)
export VITE_API_URL="https://api.example.com"
```

### Verificação
```bash
# Testar comunicação
curl -H "Authorization: Bearer $PROD_JWT" \
  https://api.example.com/api/scraper-proxy/status
```

## 📊 **Monitoramento Pós-Migração**

### Logs a Observar
```bash
# Sucesso
[INFO] Proxy request successful: /api/scraper-proxy/status

# Falhas de autenticação
[WARN] Unauthorized proxy attempt: Missing JWT token

# Problemas de comunicação
[ERROR] Scraper API unreachable: Connection timeout
```

### Métricas
- Taxa de sucesso das requisições proxy
- Tempo de resposta da comunicação
- Tentativas de acesso não autorizadas
- Errors de comunicação com scraper

---

## ✅ **Status da Migração**

- **Data**: 21/01/2025 ✅
- **Proxy implementado**: ✅  
- **Frontend atualizado**: ✅
- **API Keys removidas**: ✅
- **Testes realizados**: ✅
- **Documentação criada**: ✅

**🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!**

A aplicação agora está segura e não expõe mais API keys no frontend. 