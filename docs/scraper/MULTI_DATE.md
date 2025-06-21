# Multi-Date Multi-Worker Scraper para DJE-SP

Este sistema permite buscar publicações do DJE-SP em múltiplas datas de forma concorrente, com controle de progresso e capacidade de retomar execuções interrompidas.

## 📋 Funcionalidades

- ✅ **Busca em múltiplas datas**: De 17/03/2025 até hoje
- ✅ **Multi-worker**: 3 workers processando datas simultaneamente
- ✅ **Controle de progresso**: Salva progresso em arquivo JSON
- ✅ **Retomada automática**: Continua de onde parou se interrompido
- ✅ **Tratamento de erros**: Retry automático para falhas temporárias
- ✅ **Monitoramento**: Scripts para acompanhar o progresso em tempo real

## 🚀 Como Usar

### 1. Executar o Scraper

```bash
# Navegar para o diretório do scraper
cd backend/scraper

# Executar o scraper multi-data
python run_multi_date_scraper.py
```

### 2. Monitorar Progresso

Em outro terminal:

```bash
# Monitor contínuo (atualiza a cada 30 segundos)
python monitor_progress.py

# Monitor com intervalo personalizado (60 segundos)
python monitor_progress.py --interval 60

# Verificação única (sem loop)
python monitor_progress.py --once

# Monitor com arquivo personalizado
python monitor_progress.py --file /caminho/para/arquivo.json
```

### 3. Parar e Retomar

Para parar o scraper:

- Pressione `Ctrl+C` para shutdown graceful
- O progresso será salvo automaticamente

Para retomar:

- Execute novamente o script `run_multi_date_scraper.py`
- O sistema detectará automaticamente onde parou e continuará

## 📁 Estrutura dos Arquivos

### Arquivo de Progresso (`backend/scraper/src/scrap_workrs.json`)

```json
{
  "metadata": {
    "start_date": "17/03/2025",
    "end_date": "17/06/2025",
    "num_workers": 3,
    "last_updated": "2025-06-17T14:30:00",
    "total_dates": 92,
    "processed_dates": 15,
    "total_publications": 1250
  },
  "dates": {
    "17/03/2025": {
      "date": "17/03/2025",
      "processed": true,
      "worker_id": "worker_1",
      "start_time": "2025-06-17T14:00:00",
      "end_time": "2025-06-17T14:05:00",
      "publications_found": 85,
      "error": null,
      "retry_count": 0
    }
  },
  "workers": {
    "worker_1": {
      "worker_id": "worker_1",
      "current_date": "18/03/2025",
      "dates_processed": 5,
      "total_publications": 425,
      "status": "working"
    }
  }
}
```

### Estrutura de Status

#### Status de Data

- `processed`: `true` se a data foi processada com sucesso
- `worker_id`: ID do worker que processou a data
- `start_time`/`end_time`: Timestamps de início e fim do processamento
- `publications_found`: Número de publicações encontradas
- `error`: Mensagem de erro (se houver)
- `retry_count`: Número de tentativas realizadas

#### Status de Worker

- `idle`: Worker aguardando nova tarefa
- `working`: Worker processando uma data
- `completed`: Worker finalizou todas as tarefas
- `error`: Worker teve erro crítico

## ⚙️ Configuração

### Parâmetros Principais

Os parâmetros podem ser modificados no arquivo `multi_date_scraper.py`:

```python
# Parâmetros de entrada
START_DATE = "17/03/2025"        # Data inicial
END_DATE = "NOW"                 # Data final (NOW = hoje)
JSON_FILE_PATH = "src/scrap_workrs.json"  # Arquivo de progresso
NUM_WORKERS = 3                  # Número de workers
```

### Configurações do Scraper

As configurações do scraper estão em `src/infrastructure/config/settings.py`:

```python
class ScraperSettings:
    max_retries: int = 3           # Tentativas por página
    retry_delay: int = 5           # Delay entre tentativas
    max_pages: int = 20            # Páginas máximas por data
    search_terms: List[str] = ["RPV", "pagamento pelo INSS"]
```

## 🛠️ Scripts Disponíveis

### 1. `multi_date_scraper.py`

Script principal com a implementação completa do sistema multi-worker.

### 2. `run_multi_date_scraper.py`

Script executável simples para iniciar o scraping.

### 3. `monitor_progress.py`

Monitor de progresso com interface de linha de comando.

## 📊 Monitoramento

### Exemplo de Saída do Monitor

```
================================================================================
🕷️  MONITOR DE PROGRESSO - MULTI-DATE SCRAPER
================================================================================

📊 RESUMO GERAL:
----------------------------------------
📅 Período: 17/03/2025 até 17/06/2025
👥 Workers: 3
🔄 Última atualização: 2025-06-17T14:30:00
📈 Total de datas: 92
✅ Datas processadas: 15
📄 Total de publicações: 1250
🎯 Progresso: 16.3%

👥 STATUS DOS WORKERS:
----------------------------------------
🔥 worker_1: working
   📅 Data atual: 18/03/2025
   ✅ Datas processadas: 5
   📄 Publicações: 425

😴 worker_2: idle
   📅 Data atual: N/A
   ✅ Datas processadas: 4
   📄 Publicações: 320

🔥 worker_3: working
   📅 Data atual: 20/03/2025
   ✅ Datas processadas: 6
   📄 Publicações: 505

📅 ÚLTIMAS 5 DATAS PROCESSADAS:
----------------------------------------
📅 19/03/2025 | 👷 worker_2 | 📄 75 pub | ⏱️ 4m32s
📅 17/03/2025 | 👷 worker_1 | 📄 85 pub | ⏱️ 5m15s
📅 21/03/2025 | 👷 worker_3 | 📄 92 pub | ⏱️ 3m45s
```

## 🔧 Tratamento de Erros

### Tipos de Erro

1. **Erros de Conexão**: Timeout, DNS, etc.
2. **Erros de Scraping**: Estrutura da página mudou
3. **Erros de Sistema**: Memória, disco, etc.

### Estratégias de Recuperação

1. **Retry Automático**: Até 3 tentativas por data
2. **Backoff Exponencial**: Delay aumenta a cada tentativa
3. **Isolamento de Erros**: Erro em uma data não afeta outras
4. **Logging Detalhado**: Todos os erros são registrados

### Logs

Os logs são salvos em:

- `src/logs/scraper.log`: Log principal
- `src/logs/error.log`: Logs de erro
- `reports/json/`: Publicações extraídas

## 🚨 Limitações e Considerações

### Rate Limiting

- Delay de 2 segundos entre páginas
- Delay de 1 segundo entre requests
- Máximo de 3 workers simultâneos

### Recursos do Sistema

- Cada worker usa um browser Chrome
- Consumo de memória: ~200MB por worker
- Uso de CPU: Moderado

### Dados Extraídos

- Publicações são salvas em arquivos JSON
- Backup automático é mantido
- Não há verificação de duplicatas local (feita na API)

## 📝 Logs e Debugging

### Níveis de Log

- `INFO`: Progresso normal
- `WARNING`: Situações inesperadas
- `ERROR`: Falhas que impedem o processamento
- `DEBUG`: Informações detalhadas (apenas em modo debug)

### Debugging

Para ativar modo debug, modifique em `settings.py`:

```python
enable_debug: bool = True
debug_screenshot_on_error: bool = True
```

## 🔄 Fluxo de Execução

1. **Inicialização**
   - Carrega ou cria arquivo de progresso
   - Inicializa container e configurações
   - Popula fila de datas não processadas

2. **Execução**
   - Workers processam datas da fila
   - Cada data é processada independentemente
   - Progresso é salvo após cada data

3. **Finalização**
   - Shutdown graceful salva progresso final
   - Cleanup de recursos
   - Relatório final

## 🆘 Solução de Problemas

### Scraper Não Inicia

- Verificar dependências: `pip install -r requirements.txt`
- Verificar permissões do arquivo de progresso
- Verificar logs para erros de inicialização

### Workers Param ou Falham

- Verificar memória disponível
- Verificar conexão com internet
- Verificar se o site DJE está acessível

### Progresso Não Salva

- Verificar permissões de escrita
- Verificar espaço em disco
- Verificar se o arquivo não está bloqueado

### Performance Lenta

- Reduzir número de workers
- Aumentar delays entre requests
- Verificar recursos do sistema

## 📞 Suporte

Para problemas ou dúvidas:

1. Verificar logs em `src/logs/`
2. Executar monitor para verificar status
3. Verificar arquivo de progresso
4. Consultar esta documentação

---

**Desenvolvido para o projeto JusCash - Sistema de Scraping DJE-SP**
