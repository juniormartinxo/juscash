# 🤖 Integração API com Scrapers

## 🎯 **Resumo Executivo**

A API JusCash possui **funcionalidade específica para integração com scrapers** através de API Key, permitindo automação e coleta de dados.

### ✅ **Funcionalidades Implementadas:**

- 🔑 **API Key específica** para scrapers (não requer autenticação JWT)
- 🚀 **Rate limiting diferenciado** (1000 req/15min vs 100 para usuários)
- 📝 **Logs de auditoria** específicos para identificar origem dos dados
- 🔒 **Mesma validação rigorosa** de dados de entrada

## 🔧 **Configuração**

### **Variável de Ambiente:**

```bash
# Adicione no .env
SCRAPER_API_KEY="sua-chave-secreta-longa-e-segura-aqui"
```

### **Endpoint Específico:**

```
POST /api/scraper/publications
```

## 🚀 **Exemplo de Uso**

### **cURL:**

```bash
curl -X POST http://localhost:8000/api/scraper/publications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key-aqui" \
  -d '{
    "process_number": "1234567-89.2024.8.26.0100",
    "availability_date": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Conteúdo da publicação...",
    "status": "NOVA"
  }'
```

### **Python:**

```python
import requests
import os

headers = {
    'X-API-Key': os.getenv('SCRAPER_API_KEY'),
    'Content-Type': 'application/json'
}

data = {
    "process_number": "1234567-89.2024.8.26.0100",
    "availability_date": "2024-03-17T00:00:00.000Z",
    # ... outros campos
}

response = requests.post('http://localhost:8000/api/scraper/publications', 
                        headers=headers, json=data)
```

## 📊 **Comparativo de Endpoints**

| Aspecto | Endpoint Normal | Endpoint Scraper |
|---------|----------------|------------------|
| **Rota** | `POST /api/publications` | `POST /api/scraper/publications` |
| **Auth** | JWT Token (Bearer) | API Key (X-API-Key) |
| **Rate Limit** | 100 req/15min | 1000 req/15min |
| **Logs** | Usuário identificado | Origem "SCRAPER" |
| **Validação** | ✅ Mesma | ✅ Mesma |

## 🔒 **Segurança**

- **API Key obrigatória** via header `X-API-Key`
- **Logs de auditoria** com identificação da origem
- **Mesma validação** rigorosa de dados
- **Rate limiting** apropriado para automação

## 🧪 **Teste da Integração**

Execute o script de teste para validar a configuração:

```bash
node backend/api/test-scraper-api.js
```

## 📚 **Documentação Completa**

Para informações técnicas detalhadas:

👉 **[Documentação Técnica Completa](SCRAPER-INTEGRATION.md)**
👉 **[Exemplos Práticos](EXAMPLES.md)**
👉 **[README Técnico da API](../../backend/api/README.md)**

---

**Status:** 🟢 **Pronto para uso** - Integração com scrapers disponível e funcional
