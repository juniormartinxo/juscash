# 🎯 Resumo: Agendamento 2x por Dia (06h e 14h)

## ✅ **Mudanças Implementadas**

### **ANTES (Original):**
- ⏰ Execução **1x por dia** às 06:00
- 📅 Data **anterior** (ontem)
- 🔧 Configuração única

### **DEPOIS (Atualizado):**
- ⏰ Execução **2x por dia** às **06:00** e **14:00**
- 📅 Data **atual** (hoje)
- 🔧 Configurações separadas para manhã e tarde

---

## 🔧 **Arquivos Modificados**

### 1. **settings.py** - Novas Configurações
```python
# Duas execuções por dia
morning_execution_hour: int = Field(default=6, env="SCHEDULER_MORNING_HOUR")     # 06:00
afternoon_execution_hour: int = Field(default=14, env="SCHEDULER_AFTERNOON_HOUR") # 14:00
```

### 2. **scheduler_adapter.py** - Novo Método
```python
def schedule_twice_daily_scraping(...)
    # Cria dois jobs: morning_scraping e afternoon_scraping
    # CronTrigger para 06:00 e outro para 14:00
```

### 3. **main.py** - Usa Novo Agendamento
```python
# Agenda duas vezes por dia
self.scheduler.schedule_twice_daily_scraping(
    morning_hour=6, afternoon_hour=14, ...
)
```

### 4. **scraping_orchestrator.py** - Data Atual
```python
# Data atual (não mais "ontem")
today = datetime.now()
date_str = today.strftime("%Y-%m-%d")
```

---

## 🌅🌇 **Fluxo de Execução**

### **06:00 (Manhã):**
```
CronTrigger → Job: morning_scraping → _run_daily_scraping() 
→ python scraping.py run --start-date 2025-01-21 --headless
```

### **14:00 (Tarde):**
```
CronTrigger → Job: afternoon_scraping → _run_daily_scraping()
→ python scraping.py run --start-date 2025-01-21 --headless
```

### **Resultado:**
- 📁 **Manhã:** `reports/json/` com publicações da data atual
- 📁 **Tarde:** `reports/json/` com publicações da data atual
- 🔄 **Mesmo código:** Ambos usam `scraping.py` completo

---

## 📋 **Configurações Necessárias**

### **1. Adicionar ao .env:**
```bash
# Horários (06:00 e 14:00)
SCHEDULER_MORNING_HOUR=6
SCHEDULER_MORNING_MINUTE=0
SCHEDULER_AFTERNOON_HOUR=14
SCHEDULER_AFTERNOON_MINUTE=0
SCHEDULER_START_DATE=2025-01-21
```

### **2. Habilitar no supervisord.conf:**
```ini
[program:main_app]
autostart=true  # Mudar de false para true
```

### **3. Ativar:**
```bash
docker-compose up --build scraper -d
```

---

## 🎯 **Resultados Esperados**

### **Logs do Agendamento:**
```
⏰ Scheduler configurado para execução duas vezes por dia:
🌅 Manhã: 06:00
🌇 Tarde: 14:00
✅ Scraping duas vezes por dia agendado com sucesso
```

### **Logs de Execução (06:00):**
```
🔄 Iniciando execução do scraping às 06:00
📅 Executando scraping para data: 2025-01-21
📄 Usando script: /app/scraping.py
🔄 Executando comando: python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
✅ Execução concluída: [execution-id]
📊 Publicações encontradas: X
💾 Publicações salvas: Y
```

### **Logs de Execução (14:00):**
```
🔄 Iniciando execução do scraping às 14:00
📅 Executando scraping para data: 2025-01-21
[... mesmo processo ...]
```

---

## 🔍 **Verificação**

### **Jobs Agendados:**
```bash
# Ver jobs ativos
docker-compose exec scraper python -c "
from src.infrastructure.scheduler.scheduler_adapter import SchedulerAdapter
scheduler = SchedulerAdapter()
print('Jobs agendados:', [job.id for job in scheduler.scheduler.get_jobs()])
"

# Output esperado: ['morning_scraping', 'afternoon_scraping']
```

### **Configurações Carregadas:**
```bash
docker-compose exec scraper python -c "
from src.infrastructure.config.settings import get_settings
s = get_settings().scheduler
print(f'Manhã: {s.morning_execution_hour:02d}:{s.morning_execution_minute:02d}')
print(f'Tarde: {s.afternoon_execution_hour:02d}:{s.afternoon_execution_minute:02d}')
"

# Output esperado:
# Manhã: 06:00
# Tarde: 14:00
```

---

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

### **Exemplo 3: Apenas manhã (desabilitar tarde)**
```bash
SCHEDULER_MORNING_HOUR=6
SCHEDULER_AFTERNOON_HOUR=-1  # Valor inválido desabilita
```

---

## 🎉 **Resumo**

**Agora o scraping executa automaticamente:**

- 🌅 **06:00 da manhã** → Scraping da data atual
- 🌇 **14:00 da tarde** → Scraping da data atual
- 📅 **Mesmo dia** (não mais dia anterior)
- 🔄 **Mesmo código** do `scraping.py` que já funciona
- 📊 **Duas chances** de capturar publicações por dia

**O sistema está pronto para funcionar 2x por dia!** 🚀 