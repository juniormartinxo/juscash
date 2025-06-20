# 🕕 Guia de Configuração do Agendamento do Scraper

## ✅ Status Atual

**Problema resolvido!** Identifiquei que havia duas implementações diferentes de scraping e corrigi para que **o agendamento agora use o código do `scraping.py` que funciona completamente**.

## 🔧 **Correção Implementada**

### **ANTES (Problema):**
```
Agendamento → src/main.py → DJEScraperAdapter (incompleto)
Manual → scraping.py → DJEScraperPlaywright (completo)
```

### **DEPOIS (Solução):**
```
Agendamento → src/main.py → executa scraping.py → DJEScraperPlaywright (completo)
Manual → scraping.py → DJEScraperPlaywright (completo)
```

**Agora ambos usam o mesmo código funcional!**

## 📋 Configurações Necessárias

### 1. Adicionar Configurações do Scheduler ao .env

Adicione as seguintes linhas ao seu arquivo `.env`:

```bash
# ===========================================
# CONFIGURAÇÕES DO AGENDADOR (SCHEDULER)
# ===========================================
# Execução automática todos os dias às 06:00
SCHEDULER_DAILY_HOUR=6
SCHEDULER_DAILY_MINUTE=0
SCHEDULER_START_DATE=2025-01-21
```

### 2. Habilitar o Main App no Supervisord

No arquivo `backend/scraper/supervisord.conf`, altere a configuração do `main_app`:

**ATUAL:**
```ini
[program:main_app]
autostart=false     # <- MUDAR PARA true
```

**NOVO:**
```ini
[program:main_app]
autostart=true      # <- Habilita o agendamento automático
```

## 🚀 Como Funciona Agora

### **Fluxo do Agendamento:**

1. **06:00** - Scheduler dispara
2. **src/main.py** - Recebe o trigger
3. **ScrapingOrchestrator** - Executa automaticamente:
   ```bash
   python scraping.py run --start-date 2025-01-20 --end-date 2025-01-20 --headless
   ```
4. **scraping.py** - Faz o scraping completo (mesmo código do manual)
5. **Resultados** - Salvos em `reports/json/`

### **Vantagens da Correção:**
- ✅ **Usa o código que funciona** (`DJEScraperPlaywright`)
- ✅ **Scraping completo** (PDFs, ESAJ, valores, advogados)
- ✅ **Mesma qualidade** que execução manual
- ✅ **Logs detalhados** do processo
- ✅ **Compatibilidade total**

## 🚀 Como Executar

### Opção 1: Via Docker (Recomendado)

1. **Parar serviços atuais:**
```bash
docker-compose down
```

2. **Reconstruir e iniciar com agendamento:**
```bash
docker-compose up --build scraper -d
```

3. **Verificar logs do agendamento:**
```bash
docker-compose logs -f scraper
```

Você verá logs como:
```
📅 Scheduler inicializado
📅 Agendando scraping diário a partir de 2025-01-21 às 06:00
⏰ Scheduler configurado para execução diária às 06:00
✅ Scraping diário agendado com sucesso
```

**No horário agendado (06:00):**
```
🚀 Iniciando execução diária [execution-id]
📅 Executando scraping para data: 2025-01-20
📄 Usando script: /app/scraping.py
🔄 Executando comando: python scraping.py run --start-date 2025-01-20 --end-date 2025-01-20 --headless
🚀 Iniciando DJE Scraper com Playwright
📅 Período: 2025-01-20 até 2025-01-20
✅ scraping.py executado com sucesso
📊 Publicações encontradas: X
💾 Publicações salvas: Y
```

### Opção 2: Execução Local

1. **Navegar para o diretório do scraper:**
```bash
cd backend/scraper
```

2. **Ativar ambiente virtual:**
```bash
source venv/bin/activate
```

3. **Executar o agendador:**
```bash
python -m src.main
```

## 📊 Monitoramento

### Verificar Status do Agendamento

```bash
# Logs em tempo real
docker-compose logs -f scraper

# Verificar se o scheduler está ativo
docker-compose exec scraper supervisorctl status

# Verificar processos Python
docker-compose exec scraper ps aux | grep python
```

### Logs Importantes

Os logs do agendamento aparecerão como:
```
🚀 Iniciando DJE Scraper Application
📅 Execução programada diária a partir de 2025-01-21
⏰ Scheduler configurado para execução diária às 06:00
🔄 Aguardando próxima execução...
```

No horário agendado (06:00), você verá os **mesmos logs do scraping.py manual**, mostrando que está usando o código completo!

## ⚙️ Personalização do Horário

Para alterar o horário de execução, modifique no arquivo `.env`:

```bash
# Para executar às 08:30 da manhã
SCHEDULER_DAILY_HOUR=8
SCHEDULER_DAILY_MINUTE=30

# Para executar às 18:00 (6h da tarde)
SCHEDULER_DAILY_HOUR=18
SCHEDULER_DAILY_MINUTE=0
```

## 🔧 Configurações Avançadas

### Data de Scraping

Por padrão, o agendamento faz scraping da **data anterior** (ontem), que é o comportamento correto para execução diária às 06h.

### Modo Headless

O agendamento sempre executa em modo headless (`--headless`) para garantir estabilidade no ambiente Docker.

### Tolerância a Atrasos

O scheduler está configurado com:
- **Tolerância de atraso:** 1 hora (`misfire_grace_time=3600`)
- **Execução única:** Impede execuções simultâneas (`max_instances=1`)

## 🧪 Teste do Agendamento

### Teste Manual Imediato

Para testar se o scraping funciona sem aguardar o horário:

```bash
# Testar integração completa
docker-compose exec scraper python -c "
import asyncio
from src.application.services.scraping_orchestrator import ScrapingOrchestrator
from src.shared.container import Container

async def test():
    container = Container()
    orchestrator = ScrapingOrchestrator(container)
    result = await orchestrator.execute_daily_scraping()
    print(f'✅ Teste concluído: {result.publications_found} publicações')

asyncio.run(test())
"
```

### Teste Manual Direto

```bash
# Testar scraping.py diretamente (mesmo código que o agendamento usa)
docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
```

### Teste do Scheduler

Para testar se o agendamento está funcionando, altere temporariamente para executar em alguns minutos:

```bash
# No .env, definir para daqui a 2 minutos
SCHEDULER_DAILY_HOUR=14  # (se agora são 14:00)
SCHEDULER_DAILY_MINUTE=2  # (para executar às 14:02)
```

## 🚨 Solução de Problemas

### Problema: "scraping.py não encontrado"

```bash
# Verificar se o arquivo existe
docker-compose exec scraper ls -la scraping.py

# Se não existir, verificar estrutura
docker-compose exec scraper find /app -name "scraping.py"
```

### Problema: "Scheduler não está executando"

1. **Verificar logs:**
```bash
docker-compose logs scraper | grep -i scheduler
```

2. **Verificar se main_app está rodando:**
```bash
docker-compose exec scraper supervisorctl status main_app
```

3. **Restart do serviço:**
```bash
docker-compose restart scraper
```

### Problema: "Execução falhou"

1. **Verificar logs do scraping.py:**
```bash
docker-compose logs scraper | grep -A 10 -B 10 "Executando comando"
```

2. **Testar scraping.py manualmente:**
```bash
docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21 --headless
```

3. **Verificar dependências:**
```bash
docker-compose exec scraper python -c "from playwright.async_api import async_playwright; print('Playwright OK')"
```

## 📈 Resultado Esperado

Com a correção implementada, você terá:

- ✅ **Execução automática diária às 06:00**
- ✅ **Uso do código completo do scraping.py**
- ✅ **PDFs baixados e processados**
- ✅ **Dados extraídos do ESAJ**
- ✅ **Publicações salvas em JSON**
- ✅ **Logs detalhados de cada execução**
- ✅ **Mesma qualidade da execução manual**

## 🔄 Comandos Úteis

```bash
# Parar agendamento
docker-compose stop scraper

# Reiniciar agendamento
docker-compose restart scraper

# Ver status de todos os serviços
docker-compose ps

# Logs de todos os serviços
docker-compose logs -f

# Entrar no container do scraper
docker-compose exec scraper bash

# Testar scraping manual (mesmo código do agendamento)
docker-compose exec scraper python scraping.py run --start-date 2025-01-21 --end-date 2025-01-21
```

## 📞 Próximos Passos

1. **Adicionar as configurações ao .env**
2. **Habilitar autostart=true no supervisord.conf**
3. **Reiniciar o container com docker-compose up --build scraper -d**
4. **Monitorar os logs para confirmar o agendamento**

**Agora o agendamento realmente executa o `python scraping.py run` às 06:00 da manhã todos os dias!** 🎉 