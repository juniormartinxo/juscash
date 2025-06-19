# 📖 Guia de Uso Prático - Sistema DJE-SP

## 🎯 Visão Geral

O sistema DJE-SP foi desenvolvido para extrair automaticamente publicações relacionadas a **RPV (Requisição de Pequeno Valor)** e **pagamentos pelo INSS** do Diário da Justiça Eletrônico de São Paulo.

### Principais Funcionalidades

1. **Busca Automatizada**: Pesquisa por termos específicos ("RPV", "pagamento pelo INSS")
2. **Extração Inteligente**: Localiza processos e extrai dados estruturados
3. **Publicações Divididas**: Lida com conteúdo que está em múltiplas páginas PDF
4. **Multi-Data**: Processa várias datas simultaneamente
5. **Formato JSON**: Salva dados em formato estruturado para integração com APIs

## 🚀 Casos de Uso

### 1. Extração Diária Automatizada

```bash
# Execução diária automática (configurar no cron)
python -m src.main

# Ou usando o orquestrador
python multi_date_scraper.py
```

**Resultado**: Busca publicações da data atual e salva em `data/json_reports/`

### 2. Extração de Período Específico

```python
# Modificar multi_date_scraper.py
START_DATE = "01/03/2025"  # Data inicial
END_DATE = "31/03/2025"    # Data final
NUM_WORKERS = 2            # Número de workers paralelos

# Executar
python multi_date_scraper.py
```

**Resultado**: Processa todas as datas do período especificado

### 3. Extração de Data Única

```python
# Script personalizado
import asyncio
from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter

async def scrape_specific_date(target_date: str):
    scraper = DJEScraperAdapter()
    await scraper.initialize()
    
    try:
        # Definir data específica
        scraper.set_target_date(target_date)
        
        # Executar busca
        search_terms = ["RPV", "pagamento pelo INSS"]
        async for publication in scraper.scrape_publications(search_terms, max_pages=5):
            print(f"📋 Encontrada: {publication.process_number}")
            print(f"👥 Autores: {', '.join(publication.authors)}")
            
    finally:
        await scraper.cleanup()

# Usar
asyncio.run(scrape_specific_date("17/03/2025"))
```

## 📊 Estrutura dos Dados Extraídos

### Formato JSON das Publicações

```json
{
  "process_number": "1234567-89.2024.8.26.0001",
  "availability_date": "2025-03-17T00:00:00.000Z",
  "authors": ["JOÃO DA SILVA SANTOS", "MARIA OLIVEIRA COSTA"],
  "defendant": "Instituto Nacional do Seguro Social - INSS",
  "lawyers": [
    {
      "name": "Dr. Pedro Advogado Silva",
      "oab": "123456"
    }
  ],
  "gross_value": 545030,  // Valor em centavos (R$ 5.450,30)
  "net_value": 490527,    // Valor líquido em centavos
  "interest_value": 15020, // Juros em centavos
  "attorney_fees": 54503,  // Honorários em centavos
  "content": "Conteúdo completo da publicação...",
  "status": "NOVA",
  "scraping_source": "DJE-SP",
  "caderno": "3",
  "instancia": "1", 
  "local": "Capital",
  "parte": "1",
  "extraction_metadata": {
    "extraction_method": "enhanced_parser_v2",
    "source_url": "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?...",
    "rpv_term_found": "RPV",
    "extraction_date": "2025-06-19T12:30:45.123Z",
    "confidence_score": 0.92,
    "content_was_merged": false,
    "current_page_number": 4759
  }
}
```

### Campos Importantes

| Campo | Descrição | Obrigatório |
|-------|-----------|-------------|
| `process_number` | Número do processo no formato CNJ | ✅ |
| `authors` | Lista de autores/requerentes | ✅ |
| `availability_date` | Data de disponibilização no DJE | ✅ |
| `content` | Conteúdo completo da publicação | ✅ |
| `defendant` | Sempre "Instituto Nacional do Seguro Social - INSS" | ✅ |
| `lawyers` | Advogados com nome e OAB | ❌ |
| `gross_value` | Valor principal em centavos | ❌ |
| `net_value` | Valor líquido em centavos | ❌ |
| `interest_value` | Juros moratórios em centavos | ❌ |
| `attorney_fees` | Honorários advocatícios em centavos | ❌ |

## 🔧 Configurações Avançadas

### 1. Personalizar Termos de Busca

```python
# Em enhanced_content_parser.py, modificar:
RPV_PATTERNS = [
    re.compile(r"\bRPV\b", re.IGNORECASE),
    re.compile(r"requisição\s+de\s+pequeno\s+valor", re.IGNORECASE),
    re.compile(r"pagamento\s+pelo\s+INSS", re.IGNORECASE),
    re.compile(r"pagamento\s+de\s+benefício", re.IGNORECASE),
    # Adicionar novos padrões aqui
    re.compile(r"cumprimento\s+de\s+sentença", re.IGNORECASE),
]
```

### 2. Ajustar Confiança do Parser

```python
# Em enhanced_content_parser.py
def __init__(self):
    self.confidence_threshold = 0.8  # Padrão: 80%
    # Reduzir para capturar mais publicações (menos rigoroso)
    # Aumentar para capturar apenas publicações muito precisas
```

### 3. Configurar Rate Limiting

```python
# Em dje_scraper_adapter.py
class DJEScraperAdapter:
    def __init__(self):
        # ...
        self._min_request_interval = 2.0  # 2 segundos entre requisições
        # Aumentar para ser mais "gentil" com o servidor
        # Diminuir para processamento mais rápido (cuidado!)
```

### 4. Personalizar Formatos de Saída

```python
# Script personalizado para exportar dados
import json
from pathlib import Path
from datetime import datetime

def export_to_csv():
    """Exporta publicações JSON para CSV"""
    import pandas as pd
    
    json_files = Path("data/json_reports").glob("*.json")
    publications = []
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Converter valores de centavos para reais
            if data.get('gross_value'):
                data['gross_value_reais'] = data['gross_value'] / 100
            
            publications.append(data)
    
    df = pd.DataFrame(publications)
    
    # Salvar CSV
    output_file = f"publicacoes_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Exportado para: {output_file}")

# Executar
export_to_csv()
```

## 📈 Monitoramento e Relatórios

### 1. Verificar Progresso do Multi-Date

```bash
# Ver progresso em tempo real
tail -f src/scrap_workrs.json

# Usando jq para formatação bonita
cat src/scrap_workrs.json | jq '.metadata'
```

### 2. Estatísticas de Extração

```python
# Script para gerar estatísticas
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

def generate_stats():
    """Gera estatísticas das extrações"""
    json_files = Path("data/json_reports").glob("*.json")
    
    stats = {
        "total_publications": 0,
        "by_date": Counter(),
        "by_author_count": Counter(),
        "with_lawyers": 0,
        "with_monetary_values": 0,
        "total_gross_value": 0,
        "confidence_scores": []
    }
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            stats["total_publications"] += 1
            
            # Por data
            date_str = data.get("availability_date", "")[:10]
            stats["by_date"][date_str] += 1
            
            # Por número de autores
            author_count = len(data.get("authors", []))
            stats["by_author_count"][author_count] += 1
            
            # Com advogados
            if data.get("lawyers"):
                stats["with_lawyers"] += 1
            
            # Com valores monetários
            if data.get("gross_value"):
                stats["with_monetary_values"] += 1
                stats["total_gross_value"] += data["gross_value"]
            
            # Confiança
            confidence = data.get("extraction_metadata", {}).get("confidence_score", 0)
            stats["confidence_scores"].append(confidence)
    
    # Calcular médias
    if stats["confidence_scores"]:
        stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(stats["confidence_scores"])
    
    # Valor total em reais
    stats["total_gross_value_reais"] = stats["total_gross_value"] / 100
    
    print("📊 ESTATÍSTICAS DE EXTRAÇÃO")
    print("="*50)
    print(f"Total de publicações: {stats['total_publications']}")
    print(f"Com advogados: {stats['with_lawyers']} ({stats['with_lawyers']/stats['total_publications']*100:.1f}%)")
    print(f"Com valores: {stats['with_monetary_values']} ({stats['with_monetary_values']/stats['total_publications']*100:.1f}%)")
    print(f"Valor total: R$ {stats['total_gross_value_reais']:,.2f}")
    print(f"Confiança média: {stats.get('avg_confidence', 0):.2f}")
    print(f"\nTop 5 datas:")
    for date, count in stats["by_date"].most_common(5):
        print(f"  {date}: {count} publicações")

# Executar
generate_stats()
```

### 3. Monitoramento de Falhas

```python
# Script para analisar logs de erro
import re
from pathlib import Path
from collections import Counter

def analyze_errors():
    """Analisa logs de erro para identificar padrões"""
    log_files = Path("logs").glob("errors_*.log")
    
    error_patterns = Counter()
    
    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "ERROR" in line:
                    # Extrair tipo de erro
                    if "Timeout" in line:
                        error_patterns["Timeout"] += 1
                    elif "ConnectionError" in line:
                        error_patterns["Connection Error"] += 1
                    elif "Parser" in line:
                        error_patterns["Parser Error"] += 1
                    elif "PDF" in line:
                        error_patterns["PDF Error"] += 1
                    else:
                        error_patterns["Other"] += 1
    
    print("🔍 ANÁLISE DE ERROS")
    print("="*30)
    for error_type, count in error_patterns.most_common():
        print(f"{error_type}: {count}")

# Executar
analyze_errors()
```

## 🔄 Integração com APIs

### 1. Enviar para API Externa

```python
# Script para enviar JSONs para API
import httpx
import json
from pathlib import Path

async def sync_with_api():
    """Sincroniza publicações com API externa"""
    
    api_url = "https://sua-api.com/api/publications"
    api_key = "sua-chave-api"
    
    json_files = Path("data/json_reports").glob("*.json")
    
    async with httpx.AsyncClient() as client:
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                publication_data = json.load(f)
            
            try:
                response = await client.post(
                    api_url,
                    json=publication_data,
                    headers={"X-API-Key": api_key}
                )
                
                if response.status_code == 201:
                    print(f"✅ Enviado: {publication_data['process_number']}")
                    # Mover arquivo para pasta "sent"
                    sent_dir = Path("data/json_reports/sent")
                    sent_dir.mkdir(exist_ok=True)
                    json_file.rename(sent_dir / json_file.name)
                else:
                    print(f"❌ Erro: {response.status_code} - {publication_data['process_number']}")
                    
            except Exception as e:
                print(f"❌ Exceção: {e}")

# Executar
import asyncio
asyncio.run(sync_with_api())
```

### 2. Webhook para Notificações

```python
# Script para enviar notificações
import httpx
import json
from datetime import datetime

async def send_daily_report():
    """Envia relatório diário via webhook"""
    
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    # Contar publicações do dia
    today = datetime.now().strftime("%Y-%m-%d")
    json_files = Path("data/json_reports").glob(f"*{today}*.json")
    count = len(list(json_files))
    
    message = {
        "text": f"📊 Relatório Diário DJE-SP",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Publicações extraídas hoje:* {count}\n*Data:* {today}"
                }
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=message)
        
        if response.status_code == 200:
            print("✅ Relatório enviado")
        else:
            print(f"❌ Falha ao enviar: {response.status_code}")

# Executar
asyncio.run(send_daily_report())
```

## 🎛️ Automação e Cron Jobs

### 1. Script de Execução Diária

```bash
#!/bin/bash
# daily_scraper.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando scraping diário DJE-SP - $(date)"

# Ir para diretório do projeto
cd /path/to/juscash-dje-system

# Ativar ambiente virtual (se usar)
source venv/bin/activate

# Executar scraping
python multi_date_scraper.py

# Verificar se há novos JSONs
NEW_FILES=$(find data/json_reports -name "*.json" -mtime -1 | wc -l)

echo "📊 Encontrados $NEW_FILES novos arquivos"

# Enviar relatório (opcional)
if [ $NEW_FILES -gt 0 ]; then
    python send_daily_report.py
fi

echo "✅ Scraping diário concluído - $(date)"
```

### 2. Configuração do Crontab

```bash
# Editar crontab
crontab -e

# Adicionar linha para execução diária às 8h
0 8 * * * /path/to/daily_scraper.sh >> /path/to/logs/cron.log 2>&1

# Ou execução a cada 6 horas
0 */6 * * * /path/to/daily_scraper.sh >> /path/to/logs/cron.log 2>&1

# Limpeza semanal de logs antigos (domingo às 2h)
0 2 * * 0 find /path/to/logs -name "*.log" -mtime +7 -delete
```

## 🚨 Alertas e Notificações

### Script de Monitoramento

```python
# monitoring_alerts.py
import json
from pathlib import Path
from datetime import datetime, timedelta
import httpx

class DJEMonitor:
    def __init__(self):
        self.webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK"
        
    def check_daily_extraction(self):
        """Verifica se a extração diária está funcionando"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Verificar arquivos de hoje
        today_files = list(Path("data/json_reports").glob(f"*{today}*.json"))
        
        if not today_files:
            # Verificar se ontem teve arquivos (pode ser feriado)
            yesterday_files = list(Path("data/json_reports").glob(f"*{yesterday}*.json"))
            
            if not yesterday_files:
                self.send_alert("❌ Nenhuma publicação extraída há 2 dias!")
            else:
                self.send_alert("⚠️ Nenhuma publicação extraída hoje (possível feriado)")
        else:
            self.send_alert(f"✅ {len(today_files)} publicações extraídas hoje")
    
    async def send_alert(self, message: str):
        """Envia alerta via webhook"""
        payload = {"text": f"🤖 DJE Monitor: {message}"}
        
        async with httpx.AsyncClient() as client:
            await client.post(self.webhook_url, json=payload)

# Usar no cron
# 0 18 * * * python monitoring_alerts.py
```

---

## 📚 Próximos Passos

1. **Configurar execução automática** com cron jobs
2. **Implementar monitoramento** de falhas e alertas
3. **Integrar com sua API** para envio automático dos dados
4. **Personalizar padrões** de busca conforme necessidades específicas
5. **Configurar backup** dos dados extraídos
