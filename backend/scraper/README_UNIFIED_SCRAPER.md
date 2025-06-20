# Serviço Unificado de Scraper DJE + e-SAJ

## Visão Geral

O `unified_scraper_service.py` é um serviço completo que combina a extração de publicações do DJE-SP com enriquecimento automático de dados do e-SAJ. Este serviço unifica as funcionalidades do multi-date scraper e do CLI em uma única aplicação.

## Características

- ✅ Extração de publicações do DJE-SP
- ✅ Enriquecimento automático com dados do e-SAJ
- ✅ Suporte para data única ou período de datas
- ✅ Sistema de progresso persistente
- ✅ Logs detalhados de execução
- ✅ Configuração flexível via linha de comando

## Instalação

O serviço já está incluído no container Docker do scraper. Não é necessária instalação adicional.

## Uso

### Executar para uma data específica

```bash
docker-compose exec scraper python unified_scraper_service.py --date 17/03/2025
```

### Executar para um período

```bash
docker-compose exec scraper python unified_scraper_service.py \
  --start-date 17/03/2025 \
  --end-date 20/03/2025
```

### Opções disponíveis

```bash
# Ver todas as opções
docker-compose exec scraper python unified_scraper_service.py --help

# Principais opções:
--date DD/MM/YYYY           # Data específica
--start-date DD/MM/YYYY     # Data inicial do período
--end-date DD/MM/YYYY       # Data final (padrão: hoje)
--search-terms TERMO1 TERMO2 # Termos de busca (padrão: RPV "pagamento pelo INSS")
--max-pages N               # Máximo de páginas por busca (padrão: 20)
--no-enrichment            # Desabilita enriquecimento e-SAJ
--no-save                  # Não salva arquivos JSON
--progress-file ARQUIVO    # Arquivo de progresso (padrão: scraper_progress.json)
```

### Exemplos práticos

1. **Buscar publicações de hoje com enriquecimento:**
```bash
docker-compose exec scraper python unified_scraper_service.py \
  --date $(date +%d/%m/%Y)
```

2. **Buscar período sem enriquecimento:**
```bash
docker-compose exec scraper python unified_scraper_service.py \
  --start-date 01/06/2025 \
  --end-date 30/06/2025 \
  --no-enrichment
```

3. **Buscar com termos customizados:**
```bash
docker-compose exec scraper python unified_scraper_service.py \
  --date 17/03/2025 \
  --search-terms "precatório" "RPV" "INSS" \
  --max-pages 5
```

## Funcionamento

### Fluxo de execução

1. **Inicialização**: Carrega configurações e arquivo de progresso
2. **Extração DJE**: Busca publicações para cada data/termo
3. **Enriquecimento**: Para cada publicação encontrada:
   - Acessa o e-SAJ com o número do processo
   - Extrai valores monetários detalhados
   - Obtém informações de advogados com OAB
   - Identifica datas de disponibilização
4. **Consolidação**: Mescla dados DJE + e-SAJ
5. **Salvamento**: Gera arquivos JSON enriquecidos

### Estrutura dos dados enriquecidos

```json
{
  "process_number": "0009027-08.2024.8.26.0053",
  "publication_date": "2025-03-17T00:00:00",
  "authors": ["Nome do Autor"],
  "lawyers": [
    {
      "name": "Dr. Advogado Silva",
      "oab": "SP 123456"
    }
  ],
  "gross_value": 150000,  // em centavos
  "interest_value": 5000,
  "attorney_fees": 15000,
  "content": "Conteúdo da publicação..."
}
```

## Arquivo de Progresso

O serviço mantém um arquivo de progresso (`scraper_progress.json`) que registra:
- Datas processadas
- Quantidade de publicações encontradas
- Quantidade de publicações enriquecidas
- Erros encontrados

Exemplo:
```json
{
  "metadata": {
    "last_updated": "2025-06-20T01:57:38",
    "total_dates": 10,
    "processed_dates": 8,
    "total_publications": 1250,
    "total_enriched": 1180
  },
  "dates": {
    "17/03/2025": {
      "processed": true,
      "publications_found": 156,
      "publications_enriched": 148,
      "enrichment_errors": 8
    }
  }
}
```

## Integração com Supervisor

Para executar como serviço contínuo:

1. Edite `/app/supervisord.conf`:
```ini
[program:unified_scraper]
command=python unified_scraper_service.py --start-date 17/03/2025 --end-date 20/06/2025
directory=/app
autostart=true
autorestart=false
```

2. Recarregue supervisor:
```bash
docker-compose exec scraper supervisorctl reread
docker-compose exec scraper supervisorctl update
docker-compose exec scraper supervisorctl start unified_scraper
```

## Monitoramento

### Ver logs em tempo real
```bash
docker logs -f juscash-scraper 2>&1 | grep unified_scraper
```

### Ver progresso
```bash
docker exec juscash-scraper cat scraper_progress.json | python -m json.tool
```

### Ver estatísticas
```bash
docker logs juscash-scraper --tail 1000 | grep "RESUMO"
```

## Solução de Problemas

### Processo não encontra publicações
- Verifique se a data tem publicações do DJE
- Confirme os termos de busca
- Aumente o `--max-pages`

### Enriquecimento falha
- Verifique conectividade com e-SAJ
- Alguns processos podem não estar disponíveis no e-SAJ
- O serviço continua mesmo com falhas parciais

### Erro de memória
- Reduza o `--max-pages`
- Processe períodos menores
- Execute com `--no-enrichment` temporariamente

## Performance

- Extração DJE: ~20-30 publicações/minuto
- Enriquecimento e-SAJ: ~2-3 processos/minuto
- Taxa de sucesso enriquecimento: ~85-95%

## Notas Importantes

1. O enriquecimento é significativamente mais lento que a extração
2. Alguns processos podem não ter dados disponíveis no e-SAJ
3. O serviço salva progresso regularmente (recuperável em caso de falha)
4. Arquivos JSON são salvos em `/app/reports/json/` 