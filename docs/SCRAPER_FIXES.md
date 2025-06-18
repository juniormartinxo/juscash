# Correções Aplicadas ao Scraper Multi-Date

Este documento detalha as correções aplicadas baseadas nos logs de erro do sistema.

## 🐛 Problemas Identificados nos Logs

### 1. Falha na Submissão do Formulário
```
ERROR | ❌ Não foi possível submeter o formulário
ERROR | ❌ Erro ao preencher formulário: Falha ao submeter formulário
```

### 2. Browser Fechado Prematuramente
```
ERROR | Page.query_selector: Target page, context or browser has been closed
INFO reaped unknown pid 1403 (terminated by SIGKILL)
```

### 3. Sobrecarga de Recursos
- 3 workers simultâneos causando problemas de memória
- Múltiplos browsers consumindo recursos excessivos

## ✅ Correções Aplicadas

### 1. Melhorias na Submissão do Formulário

**Arquivo**: `src/infrastructure/web/dje_scraper_adapter.py`

- ✅ **Novos seletores** para botão de submissão
- ✅ **Verificação de visibilidade** dos elementos
- ✅ **Fallback JavaScript** quando seletores falham
- ✅ **Verificação de mudança de URL** para confirmar submissão

```python
submit_selectors = [
    'input[value="Pesquisar"]',
    'input[name="pbConsultar"]',     # NOVO
    'button:text("Pesquisar")',
    'input[type="submit"]',
    'button[type="submit"]',
    '.botaoPesquisar',               # NOVO
    '#pbConsultar',                  # NOVO
    '[onclick*="consultar"]'         # NOVO
]
```

### 2. Melhorias no Cleanup do Browser

- ✅ **Verificações de página válida** antes do uso
- ✅ **Cleanup robusto** com tratamento de erros
- ✅ **Verificação de página fechada** antes de operações

```python
if not self.page or self.page.is_closed():
    raise Exception("Página do browser foi fechada")
```

### 3. Redução de Concorrência

**Arquivo**: `multi_date_scraper.py`

- ✅ **Reduzido de 3 para 1 worker** para evitar sobrecarga
- ✅ **Timeout por data** (5 minutos máximo)
- ✅ **Delay entre processamentos** (2 segundos)
- ✅ **Cleanup individual** por worker

```python
NUM_WORKERS = 1  # Reduzido para evitar sobrecarga
timeout=300      # 5 minutos por data
await asyncio.sleep(2)  # Delay entre processamentos
```

### 4. Tratamento de Erros Melhorado

- ✅ **Timeout individual** por data processada
- ✅ **Isolamento de erros** entre workers
- ✅ **Retry inteligente** para falhas temporárias
- ✅ **Cleanup automático** de recursos

## 🚀 Como Testar as Correções

### 1. Teste Local (Desenvolvimento)

```bash
cd backend/scraper

# Resetar progresso (opcional)
rm -f src/scrap_workrs.json

# Executar scraper
python run_multi_date_scraper.py
```

### 2. Teste via Supervisor (Produção)

```bash
# Entrar no supervisorctl
supervisorctl

# Ver status
status

# Parar processo atual (se rodando)
stop multi_date_scraper

# Iniciar com correções
start multi_date_scraper

# Monitorar logs
tail -f multi_date_scraper
```

### 3. Monitoramento de Progresso

```bash
# Monitor contínuo
python monitor_progress.py

# Verificação única
python monitor_progress.py --once
```

## 📊 Comportamento Esperado Após Correções

### Estados Normais

1. **Inicialização**:
   ```
   🔧 Inicializando datas de 17/03/2025 até 17/06/2025
   ✅ Inicializadas 93 datas para processamento
   👷 Worker worker_1 iniciado
   ```

2. **Processamento**:
   ```
   📅 Configurando data específica: 17/03/2025...
   ✅ Datas configuradas: 17/03/2025 até 17/03/2025
   🎯 Tentando submeter com selector: input[value="Pesquisar"]
   ✅ Formulário submetido com sucesso
   ```

3. **Conclusão**:
   ```
   ✅ Data 17/03/2025 processada pelo worker worker_1: X publicações encontradas
   🧹 Cleanup worker worker_1 concluído
   ```

### Tratamento de Erros

1. **Falha na submissão**:
   ```
   🔄 Tentando submissão via JavaScript...
   ✅ Formulário submetido via JavaScript
   ```

2. **Timeout**:
   ```
   ⏰ Timeout processando data 17/03/2025 no worker worker_1
   🔄 Data 17/03/2025 recolocada na fila (tentativa 1/3)
   ```

3. **Browser fechado**:
   ```
   ❌ Página do browser foi fechada
   🧹 Cleanup worker worker_1 concluído
   ```

## 🛠️ Configurações Ajustadas

### Timeouts e Delays

```python
# Timeout por data
timeout=300  # 5 minutos

# Delay entre processamentos  
await asyncio.sleep(2)

# Timeout de navegação
await self.page.wait_for_load_state("networkidle", timeout=15000)
```

### Recursos

```python
# Workers reduzidos
NUM_WORKERS = 1

# Retry por data
max_retries = 3

# Verificações de saúde
if not self.page or self.page.is_closed():
    raise Exception("Página do browser foi fechada")
```

## 📈 Métricas de Sucesso

- ✅ **0 browsers mortos** com SIGKILL
- ✅ **Formulários submetidos** sem falha
- ✅ **Workers estáveis** sem crashes
- ✅ **Progresso salvo** após cada data
- ✅ **Cleanup adequado** de recursos

## 🔧 Troubleshooting

### Se ainda houver falhas na submissão:

1. **Verificar conectividade**:
   ```bash
   curl -I https://esaj.tjsp.jus.br/cdje/
   ```

2. **Screenshot de debug**:
   - Procurar por arquivos `debug_*.png` em `/app/debug/`

3. **Tentar submissão manual**:
   - Acessar o site e verificar mudanças na interface

### Se workers continuarem falhando:

1. **Reduzir timeout**:
   ```python
   timeout=180  # 3 minutos
   ```

2. **Aumentar delay**:
   ```python
   await asyncio.sleep(5)  # 5 segundos
   ```

3. **Verificar recursos do sistema**:
   ```bash
   htop  # CPU e memória
   df -h  # Espaço em disco
   ```

---

**As correções foram aplicadas para tornar o scraper mais robusto e estável.** 🎯 