# 🗑️ Solução para Arquivos JSON Não Excluídos

## 📋 Problema Identificado

Os arquivos JSON não estavam sendo excluídos após a persistência no banco de dados devido a um erro na implementação do `APIWorker`. O método `delete_json_file` estava sendo chamado apenas com o nome do arquivo em vez do caminho completo.

## ✅ Correções Implementadas

### 1. Correção no APIWorker (`api_worker.py`)

- **Problema**: Método `delete_json_file` chamado com apenas o nome do arquivo
- **Solução**: Modificado para usar o caminho completo do arquivo (`file_path`)
- **Melhorias**: Adicionado tratamento de erros mais robusto

### 2. Exclusão Automática Aprimorada

Agora os arquivos JSON são excluídos em três situações:

1. **✅ Sucesso na API**: Arquivo excluído após envio bem-sucedido
2. **🔄 Duplicatas (409)**: Arquivo excluído se publicação já existe
3. **❌ Erros Não Recuperáveis**: Arquivos excluídos para erros como:
   - `VALIDATION_ERROR`
   - `BAD_REQUEST`
   - `CLIENT_ERROR`

### 3. Limpeza Automática Periódica

- **Frequência**: A cada 1 hora
- **Critério**: Arquivos com mais de 2 horas que não estão na fila Redis
- **Segurança**: Verifica se arquivo ainda está sendo processado

### 4. Script de Limpeza Manual

Criado script `cleanup_json_files.py` para limpeza manual.

## 🚀 Como Usar

### Limpeza Manual Imediata

```bash
# Visualizar arquivos que seriam removidos
cd backend/scraper
python cleanup_json_files.py --dry-run

# Remover arquivos órfãos (mais de 24h)
python cleanup_json_files.py

# Remover arquivos mais antigos que 6 horas
python cleanup_json_files.py --max-age-hours 6

# Forçar remoção de todos os arquivos antigos (CUIDADO!)
python cleanup_json_files.py --force --max-age-hours 2
```

### Verificar Status do Sistema

```bash
# Verificar filas Redis
cd backend/scraper/src/cli
python redis_queue_cli.py

# Ver estatísticas
python redis_queue_cli.py stats

# Ver arquivos na fila
python redis_queue_cli.py peek
```

## 🔧 Configurações

### Limpeza Automática

No `api_worker.py`:

- **Intervalo**: 3600 segundos (1 hora)
- **Idade máxima**: 2 horas
- **Verificação de fila**: Sim

### Script Manual

Opções disponíveis:

- `--json-dir`: Diretório customizado (padrão: `reports/json`)
- `--max-age-hours`: Idade máxima em horas (padrão: 24)
- `--dry-run`: Apenas mostra o que seria removido
- `--force`: Remove sem verificar filas Redis

## 📊 Monitoramento

### Logs a Observar

1. **Exclusão bem-sucedida**:

   ```
   🗑️ Arquivo JSON excluído: /path/to/file.json
   ```

2. **Limpeza automática**:

   ```
   🧹 Starting periodic cleanup of orphaned JSON files...
   🧹 Cleanup completed: X orphaned files removed
   ```

3. **Erros de exclusão**:

   ```
   ❌ Erro de permissão ao excluir arquivo JSON
   ❌ Erro inesperado ao excluir arquivo JSON
   ```

### Verificar Diretório JSON

```bash
# Ver quantidade de arquivos JSON
ls -la backend/scraper/reports/json/ | wc -l

# Ver arquivos mais antigos
ls -la backend/scraper/reports/json/ | head -10

# Ver espaço ocupado
du -h backend/scraper/reports/json/
```

## ⚠️ Troubleshooting

### Arquivos Ainda Não São Excluídos

1. **Verificar logs do APIWorker**:

   ```bash
   tail -f backend/scraper/reports/log/worker_*.log
   ```

2. **Verificar se API Worker está rodando**:

   ```bash
   ps aux | grep api_worker
   ```

3. **Verificar permissões do diretório**:

   ```bash
   ls -la backend/scraper/reports/json/
   ```

### Erro de Permissões

```bash
# Corrigir permissões
sudo chown -R $USER:$USER backend/scraper/reports/
chmod -R 755 backend/scraper/reports/
```

### Redis Não Conecta

```bash
# Verificar Redis
redis-cli ping

# Reiniciar Redis via Docker
docker-compose restart redis
```

## 🔄 Reiniciar Serviços

Se necessário, reinicie os serviços de monitoramento:

```bash
# Parar todos os serviços
pkill -f monitor_json_files
pkill -f api_worker

# Reiniciar monitoramento
cd backend/scraper
python start_monitoring.py --api-endpoint http://localhost:8000
```

## 📈 Resultados Esperados

Após a implementação das correções:

1. ✅ Arquivos JSON são excluídos imediatamente após sucesso na API
2. ✅ Arquivos órfãos são limpos automaticamente a cada hora
3. ✅ Script manual permite limpeza sob demanda
4. ✅ Logs informativos sobre todas as operações
5. ✅ Não há acúmulo desnecessário de arquivos JSON

## 📞 Suporte

Se o problema persistir, verificar:

- Logs do APIWorker em `reports/log/`
- Status das filas Redis
- Permissões do sistema de arquivos
- Conectividade com a API
