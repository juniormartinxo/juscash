# Correção de Problemas do Supervisor

Este documento explica como resolver os problemas identificados nos logs do supervisord.

## 🐛 Problemas Identificados

### 1. `scraper_api` entrando em estado FATAL
```
WARN exited: scraper_api (exit status 0; not expected)
INFO gave up: scraper_api entered FATAL state, too many start retries too quickly
```

### 2. `multi_date_scraper` reiniciando constantemente
```
WARN exited: multi_date_scraper (exit status 0; not expected)
INFO gave up: multi_date_scraper entered FATAL state, too many start retries too quickly
```

## ✅ Soluções Aplicadas

### 1. Configuração do `multi_date_scraper`

**Problema**: O scraper estava reiniciando quando terminava normalmente (todas as datas processadas).

**Solução**:
```ini
[program:multi_date_scraper]
autostart=false                     # Não inicia automaticamente
autorestart=false                   # Não reinicia quando termina normalmente
```

### 2. Correção das Datas

**Problema**: O sistema estava usando 2024/2025 incorretamente.

**Solução**: Ajustadas para o ano correto do sistema (2025):
```python
START_DATE = "17/03/2025"  # Março de 2025
END_DATE = "NOW"           # Junho de 2025
```

## 🚀 Como Usar Agora

### Inicialização Manual do Multi-Date Scraper

```bash
# Entrar no supervisorctl
supervisorctl

# Verificar status
status

# Iniciar o multi-date scraper manualmente
start multi_date_scraper

# Monitorar logs
tail -f multi_date_scraper
```

### Estados Esperados

1. **Primeira execução**: 
   - Inicializa 93 datas (17/03/2025 até 17/06/2025)
   - Processa as datas com 3 workers
   - Termina com exit status 0

2. **Execuções subsequentes**:
   - Se todas as datas foram processadas: termina imediatamente
   - Se há datas pendentes: continua o processamento

### Monitoramento

```bash
# Monitor contínuo de progresso
start progress_monitor

# Ver status do monitor
status progress_monitor

# Ver logs do monitor
tail -f progress_monitor
```

## 🔧 Troubleshooting

### Se o `scraper_api` continua falhando

1. **Verificar logs específicos**:
```bash
supervisorctl tail scraper_api stderr
```

2. **Desabilitar temporariamente**:
```bash
supervisorctl stop scraper_api
```

3. **O `multi_date_scraper` funciona independentemente da API**

### Se não há trabalho para processar

```bash
# Verificar arquivo de progresso
cat src/scrap_workrs.json

# Resetar progresso (CUIDADO!)
rm src/scrap_workrs.json
supervisorctl start multi_date_scraper
```

### Se workers não processam

1. **Verificar datas no arquivo de progresso**
2. **Logs de debug do scraper**
3. **Conexão com DJE-SP**

## 📋 Checklist de Verificação

- [ ] Data do sistema está correta (2025)
- [ ] Arquivo `src/scrap_workrs.json` existe e é válido
- [ ] Há datas não processadas no arquivo
- [ ] `multi_date_scraper` não está em loop infinito
- [ ] Workers têm recursos suficientes (memória, browser)

## 🎛️ Controles Rápidos

```bash
# Status completo
supervisorctl status

# Logs em tempo real
supervisorctl tail -f multi_date_scraper

# Parar tudo
supervisorctl stop all

# Iniciar essenciais
supervisorctl start file_monitor multi_date_scraper progress_monitor
```

## 💡 Dicas de Performance

1. **Reduzir workers se necessário**:
   ```python
   NUM_WORKERS = 2  # Em vez de 3
   ```

2. **Monitorar recursos do sistema**:
   ```bash
   htop  # CPU e memória
   ```

3. **Verificar conectividade**:
   ```bash
   curl -I https://esaj.tjsp.jus.br/cdje/
   ```

---

**O sistema está agora configurado para funcionamento estável e controlado manualmente.** 