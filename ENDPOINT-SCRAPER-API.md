# 🚀 API do Scraper - Execução via HTTP

## ✅ **Novos Endpoints Adicionados!**

Agora você pode executar o comando `scraping.py run` via HTTP através da API do scraper.

---

## 🌐 **URL Base da API**

```
http://localhost:5000
```

**Porta:** 5000 (configurada no docker-compose)

**Documentação Interativa:** http://localhost:5000/docs

---

## 📋 **Endpoints Disponíveis**

### **1. Execução Manual com Datas Específicas**

**POST** `/run/scraping`

Executa o mesmo comando que você faria manualmente no terminal.

#### **Payload:**
```json
{
  "start_date": "2025-01-21",
  "end_date": "2025-01-21", 
  "headless": true
}
```

#### **Exemplo cURL:**
```bash
curl -X POST "http://localhost:5000/run/scraping" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-21",
    "end_date": "2025-01-21",
    "headless": true
  }'
```

#### **Resposta:**
```json
{
  "status": "success",
  "message": "Scraping iniciado para período 2025-01-21 até 2025-01-21",
  "command": "python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless",
  "parameters": {
    "start_date": "2025-01-21",
    "end_date": "2025-01-21", 
    "headless": true
  },
  "note": "Mesmo comando que você executaria manualmente via terminal"
}
```

---

### **2. Execução da Data Atual (Conveniência)**

**POST** `/run/scraping/today?headless=true`

Executa o scraping da data atual automaticamente.

#### **Exemplo cURL:**
```bash
# Modo headless (padrão)
curl -X POST "http://localhost:5000/run/scraping/today"

# Com interface gráfica
curl -X POST "http://localhost:5000/run/scraping/today?headless=false"
```

#### **Resposta:**
```json
{
  "status": "success",
  "message": "Scraping da data atual (2025-01-21) iniciado",
  "command": "python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless",
  "parameters": {
    "start_date": "2025-01-21",
    "end_date": "2025-01-21",
    "headless": true
  },
  "note": "Execução automática da data atual"
}
```

---

### **3. Status da API**

**GET** `/status`

Verifica o status dos serviços do scraper.

#### **Exemplo cURL:**
```bash
curl "http://localhost:5000/status"
```

#### **Resposta:**
```json
{
  "status": {
    "monitor": false,
    "scraper": false,
    "multi_date_scraper": false
  },
  "pids": {},
  "script_directory": "/app",
  "python_executable": "/opt/venv/bin/python"
}
```

---

### **4. Informações da API**

**GET** `/`

Retorna informações sobre endpoints disponíveis.

#### **Exemplo cURL:**
```bash
curl "http://localhost:5000/"
```

---

## 🧪 **Exemplos de Uso**

### **Exemplo 1: Scraping de Hoje**
```bash
curl -X POST "http://localhost:5000/run/scraping/today"
```

### **Exemplo 2: Scraping de Data Específica**
```bash
curl -X POST "http://localhost:5000/run/scraping" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-20",
    "end_date": "2025-01-20",
    "headless": true
  }'
```

### **Exemplo 3: Scraping de Período (Múltiplos Dias)**
```bash
curl -X POST "http://localhost:5000/run/scraping" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-15",
    "end_date": "2025-01-20",
    "headless": true
  }'
```

### **Exemplo 4: Scraping com Interface Gráfica (Debug)**
```bash
curl -X POST "http://localhost:5000/run/scraping" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-21",
    "end_date": "2025-01-21",
    "headless": false
  }'
```

---

## 🐍 **Exemplo em Python**

```python
import requests
import json

# URL da API
api_url = "http://localhost:5000"

# Exemplo 1: Scraping de hoje
response = requests.post(f"{api_url}/run/scraping/today")
print("Resposta:", response.json())

# Exemplo 2: Scraping com datas específicas
payload = {
    "start_date": "2025-01-21",
    "end_date": "2025-01-21",
    "headless": True
}

response = requests.post(
    f"{api_url}/run/scraping",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

print("Resposta:", response.json())

# Exemplo 3: Verificar status
status = requests.get(f"{api_url}/status")
print("Status:", status.json())
```

---

## 📱 **Exemplo em JavaScript (Frontend)**

```javascript
// Função para executar scraping
async function executarScraping(startDate, endDate, headless = true) {
    try {
        const response = await fetch('http://localhost:5000/run/scraping', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate,
                headless: headless
            })
        });

        const result = await response.json();
        console.log('Scraping iniciado:', result);
        return result;
    } catch (error) {
        console.error('Erro ao executar scraping:', error);
    }
}

// Uso
executarScraping('2025-01-21', '2025-01-21', true);

// Scraping de hoje
async function scrapingHoje() {
    try {
        const response = await fetch('http://localhost:5000/run/scraping/today', {
            method: 'POST'
        });
        const result = await response.json();
        console.log('Scraping de hoje:', result);
    } catch (error) {
        console.error('Erro:', error);
    }
}
```

---

## 🔍 **Validações**

### **Formato de Data:**
- **Formato obrigatório:** `YYYY-MM-DD`
- **Exemplos válidos:** `2025-01-21`, `2024-12-31`
- **Exemplos inválidos:** `21/01/2025`, `2025-1-21`, `21-01-2025`

### **Lógica de Datas:**
- **Data final não pode ser anterior à data inicial**
- **Exemplo inválido:** `start_date: "2025-03-17"`, `end_date: "2025-01-21"`
- **Exemplo válido:** `start_date: "2025-01-21"`, `end_date: "2025-03-17"`
- **Mesma data é válida:** `start_date: "2025-01-21"`, `end_date: "2025-01-21"`

### **Parâmetros:**
- `start_date`: **Obrigatório**, string no formato YYYY-MM-DD
- `end_date`: **Obrigatório**, string no formato YYYY-MM-DD  
- `headless`: **Opcional**, boolean (default: true)

---

## 🚨 **Tratamento de Erros**

### **Erro 400 - Formato de Data Inválido:**
```json
{
  "detail": "Formato de start_date inválido. Use YYYY-MM-DD, recebido: 21/01/2025"
}
```

### **Erro 400 - Data Final Anterior à Data Inicial:**
```json
{
  "detail": "Data final (2025-01-21) não pode ser anterior à data inicial (2025-03-17)"
}
```

### **Erro 500 - Erro Interno:**
```json
{
  "detail": "scraping.py não encontrado em: /app/scraping.py"
}
```

---

## 📊 **Monitoramento**

### **Verificar se API está Rodando:**
```bash
curl "http://localhost:5000/"
```

### **Verificar Logs do Container:**
```bash
docker-compose logs -f scraper
```

### **Verificar Processos Ativos:**
```bash
curl "http://localhost:5000/status"
```

---

## 🔄 **Relação com Comando Manual**

| Comando Manual | Endpoint API |
|----------------|--------------|
| `docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless` | `POST /run/scraping` com `{"start_date": "2025-01-21", "end_date": "2025-01-21", "headless": true}` |
| `docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --no-headless` | `POST /run/scraping` com `{"start_date": "2025-01-21", "end_date": "2025-01-21", "headless": false}` |

### **Vantagens da API:**
- ✅ **Não precisa de acesso ao terminal**
- ✅ **Pode ser chamada de qualquer aplicação**
- ✅ **Ideal para integração com frontend**
- ✅ **Execução em background**
- ✅ **Mesmos resultados do comando manual**

---

## 🎯 **Casos de Uso**

### **1. Integração com Frontend:**
Adicionar botão "Executar Scraping" na interface web que chama a API.

### **2. Scripts Automatizados:**
Criar scripts Python/JavaScript que executam scraping em horários específicos.

### **3. Webhook/Integração:**
Configurar sistemas externos para disparar scraping via HTTP.

### **4. Monitoramento/Dashboard:**
Criar dashboard que permite executar e monitorar scraping via web.

### **5. Desenvolvimento/Testes:**
Facilitar testes durante desenvolvimento sem precisar acessar terminal.

---

## 🚀 **Resumo**

**Agora você pode executar o scraping de 3 formas:**

1. 🤖 **Automático:** 06:00 e 14:00 (agendamento)
2. 🛠️ **Manual via terminal:** `docker-compose exec scraper python scraping.py run ...`
3. 🌐 **Manual via API:** `POST /run/scraping` com JSON

**Todos usam exatamente o mesmo código do `scraping.py` e produzem resultados idênticos!** 🎯 