# 🚀 Implementar Agendamento 2x por Dia (06h e 14h)

## ✅ **STATUS: Código Pronto!**

Todas as modificações já foram implementadas no código. Você só precisa **configurar e ativar**.

---

## 📋 **Passos para Ativar**

### **1. Adicionar Configurações ao .env**

Adicione estas linhas ao seu arquivo `.env`:

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

No arquivo `backend/scraper/supervisord.conf`, linha ~32, altere:

```ini
# DE:
autostart=false

# PARA:
autostart=true
```

### **3. Reiniciar o Container**

```bash
docker-compose down
docker-compose up --build scraper -d
```

### **4. Verificar Logs**

```bash
docker-compose logs -f scraper
```

**Você deve ver:**
```
⏰ Scheduler configurado para execução duas vezes por dia:
🌅 Manhã: 06:00
🌇 Tarde: 14:00
✅ Scraping duas vezes por dia agendado com sucesso
```

---

## 🌅🌇 **Como Funciona Agora**

### **06:00 da Manhã:**
- ⏰ APScheduler dispara automaticamente
- 🚀 Executa: `python scraping.py run --start-date 2025-01-21 --headless`
- 📅 Data: **Hoje** (não mais ontem)
- 📁 Salva em: `backend/scraper/reports/json/`

### **14:00 da Tarde:**
- ⏰ APScheduler dispara automaticamente  
- 🚀 Executa: `python scraping.py run --start-date 2025-01-21 --headless`
- 📅 Data: **Hoje** (mesmo dia)
- 📁 Salva em: `backend/scraper/reports/json/`

### **Vantagens:**
- 🔄 **Duas execuções por dia** = mais chances de capturar publicações
- 📅 **Data atual** = publicações do mesmo dia
- 🎯 **Mesmo código** do `scraping.py` que já funciona perfeitamente

---

## 🧪 **Testes**

### **Teste 1: Verificar Configurações**
```bash
docker-compose exec scraper python -c "
from src.infrastructure.config.settings import get_settings
s = get_settings().scheduler
print(f'🌅 Manhã: {s.morning_execution_hour:02d}:{s.morning_execution_minute:02d}')
print(f'🌇 Tarde: {s.afternoon_execution_hour:02d}:{s.afternoon_execution_minute:02d}')
"
```

**Output esperado:**
```
🌅 Manhã: 06:00
🌇 Tarde: 14:00
```

### **Teste 2: Verificar Jobs Agendados**
```bash
docker-compose exec scraper python -c "
from src.infrastructure.scheduler.scheduler_adapter import SchedulerAdapter
scheduler = SchedulerAdapter()
jobs = scheduler.scheduler.get_jobs()
for job in jobs:
    print(f'📊 Job: {job.id} - {job.name}')
"
```

**Output esperado:**
```
📊 Job: morning_scraping - Scraping Matinal DJE-SP
📊 Job: afternoon_scraping - Scraping Vespertino DJE-SP
```

### **Teste 3: Execução Manual**
```bash
# Testar o mesmo comando que será executado automaticamente
docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
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

### **Exemplo 3: 09:00 e 18:00**
```bash
SCHEDULER_MORNING_HOUR=9
SCHEDULER_AFTERNOON_HOUR=18
```

---

## 🔍 **Monitoramento**

### **Logs de Execução:**

**06:00:**
```
🔄 Iniciando execução do scraping às 06:00
📅 Executando scraping para data: 2025-01-21
🚀 Iniciando DJE Scraper com Playwright
📅 Período: 2025-01-21 até 2025-01-21
✅ Execução concluída: [execution-id]
📊 Publicações encontradas: X
💾 Publicações salvas: Y
```

**14:00:**
```
🔄 Iniciando execução do scraping às 14:00
📅 Executando scraping para data: 2025-01-21
[... mesmo processo ...]
```

### **Arquivos Gerados:**
```
backend/scraper/reports/json/
├── 0001234-56_2025_8_26_0100.json  # Manhã
├── 0001235-67_2025_8_26_0200.json  # Manhã
├── 0001236-78_2025_8_26_0300.json  # Tarde
└── 0001237-89_2025_8_26_0400.json  # Tarde
```

---

## 🚨 **Solução de Problemas**

### **Problema: "Jobs não aparecem"**
1. Verificar se `autostart=true` no supervisord.conf
2. Verificar se main_app está rodando: `docker-compose exec scraper supervisorctl status`
3. Reiniciar: `docker-compose restart scraper`

### **Problema: "Configurações não carregam"**
1. Verificar se as variáveis estão no .env
2. Verificar sintaxe: `SCHEDULER_MORNING_HOUR=6` (sem espaços)
3. Rebuild: `docker-compose up --build scraper -d`

### **Problema: "Execução falha"**
1. Testar scraping.py manualmente:
   ```bash
   docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
   ```
2. Verificar logs: `docker-compose logs scraper | grep -A 5 -B 5 "erro\|fail\|Error"`

---

## 🎯 **Resumo Final**

**Você tem agora:**

- ✅ **Código implementado** e funcional
- ✅ **Duas execuções por dia** (06:00 e 14:00)
- ✅ **Data atual** (não mais dia anterior)
- ✅ **Mesmo scraping.py** que já funciona
- ✅ **Configuração flexível** via .env

**Para ativar:**
1. ➕ Adicionar configurações ao .env
2. ✏️ Alterar autostart=true no supervisord.conf  
3. 🔄 Reiniciar container
4. 👀 Monitorar logs

**O agendamento 2x por dia está pronto para funcionar!** 🚀 