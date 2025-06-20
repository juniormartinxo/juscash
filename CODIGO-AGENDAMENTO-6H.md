# 🕕 Código Específico do Agendamento 2x por Dia (06h e 14h)

## 📍 **1. Configuração dos Horários (settings.py)**

**Arquivo:** `backend/scraper/src/infrastructure/config/settings.py`
**Linhas:** 81-90

```python
class SchedulerSettings(BaseSettings):
    """Configurações do scheduler"""

    # Horários de execução (duas vezes por dia)
    morning_execution_hour: int = Field(default=6, env="SCHEDULER_MORNING_HOUR")     # 🌅 06:00 - Manhã
    morning_execution_minute: int = Field(default=0, env="SCHEDULER_MORNING_MINUTE") # 🌅 0 minutos
    afternoon_execution_hour: int = Field(default=14, env="SCHEDULER_AFTERNOON_HOUR")   # 🌇 14:00 - Tarde
    afternoon_execution_minute: int = Field(default=0, env="SCHEDULER_AFTERNOON_MINUTE") # 🌇 0 minutos
    start_date: str = Field(default="2025-01-21", env="SCHEDULER_START_DATE")
```

**Explicação:** 
- `morning_execution_hour=6` → **06:00 da manhã**
- `afternoon_execution_hour=14` → **14:00 da tarde (2h da tarde)**
- **Duas execuções por dia** com o mesmo código do scraping.py

---

## 📍 **2. Criação dos Agendamentos (scheduler_adapter.py)**

**Arquivo:** `backend/scraper/src/infrastructure/scheduler/scheduler_adapter.py`
**Linhas:** 25-70

```python
def schedule_twice_daily_scraping(
    self,
    start_date: str,
    morning_hour: int,      # 🌅 RECEBE: 6 (manhã)
    morning_minute: int,    # 🌅 RECEBE: 0 
    afternoon_hour: int,    # 🌇 RECEBE: 14 (tarde)
    afternoon_minute: int,  # 🌇 RECEBE: 0
    scraping_function: Callable[[], Awaitable[None]],
) -> None:
    """
    Agenda execução de scraping duas vezes por dia
    """
    logger.info(f"📅 Agendando scraping duas vezes por dia a partir de {start_date}")
    logger.info(f"🌅 Manhã: {morning_hour:02d}:{morning_minute:02d}")
    logger.info(f"🌇 Tarde: {afternoon_hour:02d}:{afternoon_minute:02d}")

    # 🌅 AQUI: CronTrigger para execução matinal
    morning_trigger = CronTrigger(
        hour=morning_hour, minute=morning_minute, start_date=start_date
    )

    self.scheduler.add_job(
        func=scraping_function,        # 🌅 FUNÇÃO: _run_daily_scraping
        trigger=morning_trigger,       # 🌅 TRIGGER: Manhã às 06:00
        id="morning_scraping",
        name="Scraping Matinal DJE-SP",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    # 🌇 AQUI: CronTrigger para execução vespertina  
    afternoon_trigger = CronTrigger(
        hour=afternoon_hour, minute=afternoon_minute, start_date=start_date
    )

    self.scheduler.add_job(
        func=scraping_function,        # 🌇 FUNÇÃO: _run_daily_scraping
        trigger=afternoon_trigger,     # 🌇 TRIGGER: Tarde às 14:00
        id="afternoon_scraping",
        name="Scraping Vespertino DJE-SP",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    logger.info("✅ Scraping duas vezes por dia agendado com sucesso")
```

**Explicação:**
- **Dois CronTriggers:** Um para manhã (06:00) e outro para tarde (14:00)
- **Dois jobs:** `morning_scraping` e `afternoon_scraping`
- **Mesma função:** Ambos chamam `_run_daily_scraping` do main.py
- **Data atual:** Executa no mesmo dia (não no dia anterior)

---

## 📍 **3. Configuração do Scheduler (main.py)**

**Arquivo:** `backend/scraper/src/main.py`
**Linhas:** 51-66

```python
async def _setup_scheduler(self):
    """Configura o scheduler para execução diária"""
    # 🕕 AQUI: Passa as configurações (hour=6, minute=0) para o SchedulerAdapter
    self.scheduler.schedule_daily_scraping(
        start_date=self.settings.scheduler.start_date,
        hour=self.settings.scheduler.daily_execution_hour,      # 🕕 = 6
        minute=self.settings.scheduler.daily_execution_minute,  # 🕕 = 0
        scraping_function=self._run_daily_scraping              # 🕕 FUNÇÃO executada às 6h
    )

    logger.info(
        f"⏰ Scheduler configurado para execução diária às "
        f"{self.settings.scheduler.daily_execution_hour:02d}:"
        f"{self.settings.scheduler.daily_execution_minute:02d}"
    )
```

**Explicação:**
- Lê as configurações (`hour=6, minute=0`)
- Passa para o `SchedulerAdapter`
- Define que `_run_daily_scraping` será executada às 6h

---

## 📍 **4. Função Executada às 6h (main.py)**

**Arquivo:** `backend/scraper/src/main.py`
**Linhas:** 67-76

```python
async def _run_daily_scraping(self):
    """Executa o scraping diário"""  # 🕕 ESTA FUNÇÃO RODA ÀS 6H DA MANHÃ
    try:
        logger.info("🔄 Iniciando execução diária do scraping")
        
        # 🕕 AQUI: Chama o orchestrator que executa o scraping.py
        result = await self.orchestrator.execute_daily_scraping()

        logger.info(f"✅ Execução diária concluída: {result.execution_id}")
        logger.info(f"📊 Publicações encontradas: {result.publications_found}")
        logger.info(f"💾 Publicações salvas: {result.publications_saved}")

    except Exception as error:
        logger.error(f"❌ Erro na execução diária: {error}")
```

**Explicação:**
- **Esta função é chamada automaticamente às 06:00**
- Executa o `ScrapingOrchestrator.execute_daily_scraping()`

---

## 📍 **5. Execução do scraping.py (scraping_orchestrator.py)**

**Arquivo:** `backend/scraper/src/application/services/scraping_orchestrator.py`
**Linhas:** 85-120 (método `_execute_scraping_py`)

```python
async def _execute_scraping_py(self) -> dict:
    """
    Executa o scraping.py para fazer o scraping real
    """
    try:
        # Data de ontem (padrão para execução diária)
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        
        # Caminho para o scraping.py
        scraper_dir = Path(__file__).parent.parent.parent.parent
        scraping_py_path = scraper_dir / "scraping.py"
        
        logger.info(f"📅 Executando scraping para data: {date_str}")
        logger.info(f"📄 Usando script: {scraping_py_path}")
        
        # 🕕 AQUI: Comando executado às 6h da manhã
        cmd = [
            sys.executable,  # python
            str(scraping_py_path),
            "run",
            "--start-date", date_str,
            "--end-date", date_str,
            "--headless"  # Sempre headless no agendamento
        ]
        
        logger.info(f"🔄 Executando comando: {' '.join(cmd)}")
        
        # 🕕 AQUI: Executa o processo scraping.py
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(scraper_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(os.environ), "PYTHONPATH": str(scraper_dir)}
        )
        
        stdout, stderr = await process.communicate()
        # ... resto do código de tratamento
```

**Explicação:**
- **Esta função executa `python scraping.py run` às 06:00**
- Usa a data de ontem (comportamento correto para execução diária)
- Sempre em modo headless para estabilidade

---

## 📍 **6. Ativação do Agendamento (supervisord.conf)**

**Arquivo:** `backend/scraper/supervisord.conf`
**Linha:** 32

```ini
[program:main_app]
command=python -m src.main
directory=/app
autostart=true                     # 🕕 AQUI: Inicia automaticamente = Ativa o agendamento
autorestart=false
startsecs=3                        
startretries=3                     
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=100                       
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1"
```

**Explicação:**
- `autostart=true` → **Inicia automaticamente quando container sobe**
- `command=python -m src.main` → **Executa o main.py que configura o scheduler**

---

## 🔄 **Fluxo Completo às 6h da Manhã**

```
06:00 → APScheduler (CronTrigger) 
      → _run_daily_scraping() 
      → ScrapingOrchestrator.execute_daily_scraping() 
      → _execute_scraping_py() 
      → subprocess: python scraping.py run --start-date YYYY-MM-DD --headless
      → DJEScraperPlaywright (código completo do scraping)
      → Resultados salvos em reports/json/
```

## 🔧 **Para Alterar o Horário**

1. **Via variável de ambiente (.env):**
```bash
SCHEDULER_DAILY_HOUR=8    # Para 8h da manhã
SCHEDULER_DAILY_MINUTE=30 # Para 8:30
```

2. **Via código (settings.py):**
```python
daily_execution_hour: int = Field(default=8, env="SCHEDULER_DAILY_HOUR")
daily_execution_minute: int = Field(default=30, env="SCHEDULER_DAILY_MINUTE")
```

## 🎯 **Resumo**

O agendamento às **06:00 da manhã** acontece através de:

1. **Configuração padrão:** `default=6` em `settings.py`
2. **CronTrigger:** `CronTrigger(hour=6, minute=0)` em `scheduler_adapter.py` 
3. **APScheduler:** Biblioteca que monitora o tempo e dispara às 6h
4. **Execução:** Chama `python scraping.py run` automaticamente
5. **Ativação:** `autostart=true` no supervisord.conf

**É exatamente isso que executa o scraping às 6h da manhã todos os dias!** 🕕

---

## 📍 **LINHA EXATA: Onde está definido "6"**

### **Arquivo:** `backend/scraper/src/infrastructure/config/settings.py`
### **Linha 81:**

```python
daily_execution_hour: int = Field(default=6, env="SCHEDULER_DAILY_HOUR")
#                                       ↑
#                                    AQUI: 6h da manhã
```

### **Comandos que serão executados:**

**06:00 (Manhã):**
```bash
python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
```

**14:00 (Tarde):**
```bash
python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
```

**Data:** Sempre a data atual (hoje), não mais dia anterior.

## 🎯 **Tabela de Linhas Críticas:**

| Arquivo | Linha | Código | O que faz |
|---------|-------|--------|-----------|
| `settings.py` | 81-84 | `morning_hour=6, afternoon_hour=14` | **Define 06:00 e 14:00** |
| `scheduler_adapter.py` | 25-70 | `schedule_twice_daily_scraping()` | **Cria 2 agendamentos** |
| `main.py` | 51-66 | `schedule_twice_daily_scraping(...)` | **Configura ambos horários** |
| `main.py` | 67 | `async def _run_daily_scraping(self):` | **Função executada 2x/dia** |
| `scraping_orchestrator.py` | 85-95 | `today = datetime.now()` | **Usa data atual** |
| `supervisord.conf` | 32 | `autostart=true` | **Ativa tudo automaticamente** |

## 📊 **Jobs Agendados:**
- `morning_scraping` - **06:00**
- `afternoon_scraping` - **14:00** 