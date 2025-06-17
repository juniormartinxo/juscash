# Controle do Supervisor - Multi-Date Scraper

Este documento explica como controlar os processos do scraper usando o `supervisorctl`.

## 🎛️ Processos Disponíveis

### Processos Principais

1. **`multi_date_scraper`** - Scraper principal multi-data multi-worker
2. **`scraper_api`** - API do scraper 
3. **`file_monitor`** - Monitor de arquivos JSON
4. **`progress_monitor`** - Monitor de progresso (opcional)

### Processos Auxiliares

5. **`main_app`** - Scraper original (DESABILITADO para evitar conflitos)
6. **`scraper_cli`** - Interface CLI (manual)

## 🚀 Comandos de Controle

### Iniciar/Parar Processos

```bash
# Entrar no supervisorctl
supervisorctl

# Ver status de todos os processos
status

# Iniciar o multi-date scraper
start multi_date_scraper

# Parar o multi-date scraper (shutdown graceful)
stop multi_date_scraper

# Reiniciar o multi-date scraper
restart multi_date_scraper

# Iniciar monitor de progresso
start progress_monitor

# Parar monitor de progresso
stop progress_monitor
```

### Controle de Múltiplos Processos

```bash
# Iniciar todos os processos essenciais
start scraper_api file_monitor multi_date_scraper

# Parar todos os processos
stop all

# Reiniciar todos os processos
restart all

# Ver logs em tempo real
tail -f multi_date_scraper
```

## 📊 Configurações Específicas

### Multi-Date Scraper
```ini
[program:multi_date_scraper]
autostart=true                     # Inicia automaticamente
autorestart=unexpected             # Só reinicia em falhas inesperadas
stopwaitsecs=30                     # 30s para shutdown graceful
stopsignal=SIGINT                   # Permite cleanup adequado
```

### Progress Monitor
```ini
[program:progress_monitor]
autostart=false                    # Não inicia automaticamente
autorestart=true                   # Reinicia se falhar
command=monitor_progress.py --interval 60  # Atualiza a cada 60s
```

## 🔄 Cenários de Uso

### 1. Inicialização Completa do Sistema

```bash
supervisorctl start scraper_api
supervisorctl start file_monitor
supervisorctl start multi_date_scraper
supervisorctl start progress_monitor  # Opcional
```

### 2. Parar Tudo para Manutenção

```bash
supervisorctl stop all
```

### 3. Reiniciar Apenas o Scraper

```bash
supervisorctl restart multi_date_scraper
```

### 4. Monitoramento

```bash
# Ver status
supervisorctl status

# Ver logs do scraper
supervisorctl tail -f multi_date_scraper

# Ver logs do monitor
supervisorctl tail -f progress_monitor
```

## 🛡️ Configurações de Segurança

### Prevenção de Conflitos

- **`main_app`** está `autostart=false` para evitar conflito com `multi_date_scraper`
- Apenas um processo de scraping ativo por vez
- Prioridades configuradas para ordem correta de inicialização

### Shutdown Graceful

- `stopwaitsecs=30` - Tempo suficiente para salvar progresso
- `stopsignal=SIGINT` - Permite cleanup adequado
- `autorestart=unexpected` - Não reinicia quando termina normalmente

## 📝 Status dos Processos

### Estados Possíveis

- **RUNNING** - Processo executando normalmente
- **STOPPED** - Processo parado
- **STARTING** - Processo iniciando
- **STOPPING** - Processo parando
- **EXITED** - Processo terminou (código de saída)
- **FATAL** - Processo falhou ao iniciar

### Códigos de Saída

- **0** - Terminação normal (todas as datas processadas)
- **1** - Erro geral
- **2** - Interrupção por usuário (Ctrl+C)
- **130** - SIGINT recebido

## 🔧 Troubleshooting

### Scraper Não Inicia

```bash
# Ver logs detalhados
supervisorctl tail multi_date_scraper

# Verificar configuração
supervisorctl status multi_date_scraper

# Tentar restart
supervisorctl restart multi_date_scraper
```

### Conflitos de Processo

```bash
# Verificar se main_app está rodando
supervisorctl status main_app

# Parar main_app se necessário
supervisorctl stop main_app

# Iniciar multi_date_scraper
supervisorctl start multi_date_scraper
```

### Monitor Não Funciona

```bash
# Verificar se arquivo de progresso existe
ls -la src/scrap_workrs.json

# Iniciar manualmente para debug
python monitor_progress.py --once

# Iniciar via supervisor
supervisorctl start progress_monitor
```

## 📋 Checklist de Inicialização

1. ✅ Verificar se Docker está rodando
2. ✅ Verificar se containers estão up
3. ✅ Entrar no container do scraper
4. ✅ Executar `supervisorctl status`
5. ✅ Iniciar processos necessários
6. ✅ Verificar logs com `tail -f`

## 🚨 Alertas e Monitoramento

### Logs Importantes

- Processo iniciado: "🚀 Iniciando scraping multi-data"
- Processo concluído: "✅ Todas as datas foram processadas!"
- Erro crítico: "❌ Erro durante execução"
- Shutdown: "✅ Shutdown graceful concluído"

### Métricas de Performance

- Datas processadas por hora
- Workers ativos
- Publicações encontradas
- Taxa de erro por data

---

**Use este guia para controlar efetivamente o sistema de scraping multi-data.** 