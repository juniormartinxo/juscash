# 🕕 Configuração de Agendamento do Scraper

> Guia consolidado para configuração do agendamento automático do scraper DJE-SP

## ✅ **Status Atual**

O sistema de agendamento está **completamente implementado** e funcional, permitindo execução automática 2x por dia (06:00 e 14:00).

## 🎯 **Configurações Necessárias**

### **1. Variáveis de Ambiente (.env)**

Adicione as seguintes linhas ao arquivo `.env`:

```bash
# ===========================================
# CONFIGURAÇÕES DO AGENDADOR (2x POR DIA)
# ===========================================

# Execução matinal (06:00)
SCHEDULER_MORNING_HOUR=6
SCHEDULER_MORNING_MINUTE=0

# Execução vespertina (14:00 - 2h da tarde)  
SCHEDULER_AFTERNOON_HOUR=14
SCHEDULER_AFTERNOON_MINUTE=0

# Data de início
SCHEDULER_START_DATE=2025-01-21
```

### **2. Habilitar no supervisord.conf**

No arquivo `backend/scraper/supervisord.conf`, altere:

```ini
# DE:
autostart=false

# PARA:
autostart=true
```

### **3. Ativar o Sistema**

```bash
# Reiniciar container
docker-compose down
docker-compose up --build scraper -d

# Verificar logs
docker-compose logs -f scraper
```

## 🌅🌇 **Como Funciona**

### **Execução Automática:**

- **06:00** - Scraping da data atual
- **14:00** - Scraping da data atual (mesmo dia)
- **Comando executado:** `python scraping.py run --start-date YYYY-MM-DD --headless`

### **Fluxo Técnico:**

```
APScheduler → CronTrigger → _run_daily_scraping() → ScrapingOrchestrator 
→ subprocess: python scraping.py run → DJEScraperPlaywright → Resultados em reports/json/
```

## ⚙️ **Personalização de Horários**

### **Exemplo 1: 08:00 e 16:00**

```bash
SCHEDULER_MORNING_HOUR=8
SCHEDULER_AFTERNOON_HOUR=16
```

### **Exemplo 2: 07:30 e 15:30**

```bash
SCHEDULER_MORNING_HOUR=7
SCHEDULER_MORNING_MINUTE=30
SCHEDULER_AFTERNOON_HOUR=15
SCHEDULER_AFTERNOON_MINUTE=30
```

## 🧪 **Verificação e Teste**

### **Verificar Configurações:**

```bash
docker-compose exec scraper python -c "
from src.infrastructure.config.settings import get_settings
s = get_settings().scheduler
print(f'🌅 Manhã: {s.morning_execution_hour:02d}:{s.morning_execution_minute:02d}')
print(f'🌇 Tarde: {s.afternoon_execution_hour:02d}:{s.afternoon_execution_minute:02d}')
"
```

### **Verificar Jobs Agendados:**

```bash
docker-compose exec scraper python -c "
from src.infrastructure.scheduler.scheduler_adapter import SchedulerAdapter
scheduler = SchedulerAdapter()
jobs = scheduler.scheduler.get_jobs()
for job in jobs:
    print(f'📊 Job: {job.id} - {job.name}')
"
```

### **Teste Manual (mesmo código do agendamento):**

```bash
docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
```

## 🔍 **Monitoramento**

### **Logs Esperados:**

```
⏰ Scheduler configurado para execução duas vezes por dia:
🌅 Manhã: 06:00  
🌇 Tarde: 14:00
✅ Scraping duas vezes por dia agendado com sucesso
```

**Durante execução:**

```
🔄 Iniciando execução do scraping às 06:00
📅 Executando scraping para data: 2025-01-21
🚀 Iniciando DJE Scraper com Playwright
✅ Execução concluída: [execution-id]
📊 Publicações encontradas: X
💾 Publicações salvas: Y
```

## 🚨 **Troubleshooting**

### **Jobs não aparecem:**

1. Verificar `autostart=true` no supervisord.conf
2. Verificar se main_app está rodando: `docker-compose exec scraper supervisorctl status`
3. Reiniciar: `docker-compose restart scraper`

### **Configurações não carregam:**

1. Verificar variáveis no .env
2. Verificar sintaxe (sem espaços): `SCHEDULER_MORNING_HOUR=6`
3. Rebuild: `docker-compose up --build scraper -d`

### **Execução falha:**

1. Testar scraping.py manualmente
2. Verificar logs de erro
3. Verificar conectividade

## 📋 **Integração com API HTTP**

O scraper também pode ser executado via API HTTP (porta 5000):

### **Execução via API:**

```bash
# Scraping de hoje
curl -X POST "http://localhost:5000/run/scraping/today"

# Scraping de datas específicas
curl -X POST "http://localhost:5000/run/scraping" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-21",
    "end_date": "2025-01-21",
    "headless": true
  }'
```

### **Verificar status:**

```bash
curl "http://localhost:5000/status"
```

## ✅ **Resumo**

**Você tem 3 formas de execução:**

1. 🤖 **Automático:** 06:00 e 14:00 (agendamento)
2. 🛠️ **Manual via terminal:** `docker-compose exec scraper python scraping.py run ...`
3. 🌐 **Manual via API:** `POST /run/scraping` com JSON

**Todos usam exatamente o mesmo código do `scraping.py` funcional!**

---

**Para mais detalhes técnicos, consulte:**

- [Documentação do Scraper](./README.md)
- [Guia de Implementação](./IMPLEMENTATION-GUIDE.md)
- [Troubleshooting Geral](../TROUBLESHOOTING.md)
