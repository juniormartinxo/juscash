# DJE Scraper com Playwright

Scraper completo implementado do zero usando Playwright para extrair informações de publicações de RPV e pagamentos pelo INSS do Diário da Justiça Eletrônico de São Paulo (DJE-SP).

## 🚀 Funcionalidades

- ✅ Scraping por período de datas (data início até data fim)
- ✅ Busca automática por termos "RPV" e "pagamento pelo INSS"
- ✅ Download e processamento de PDFs das publicações
- ✅ Extração automática de números de processo dos PDFs
- ✅ Consulta automática no ESAJ para dados complementares
- ✅ Extração de advogados, valores monetários e datas
- ✅ Sanitização de conteúdo para prevenir SQL injection
- ✅ Salvamento automático em arquivos JSON
- ✅ Limpeza automática de arquivos temporários

## 📋 Pré-requisitos

- Python 3.8+
- Pip para instalação de dependências

## 🔧 Instalação

1. **Execute o script de instalação:**
```bash
cd backend/scraper
chmod +x install-scraper.sh
./install-scraper.sh
```

2. **Ou instale manualmente:**
```bash
pip install -r requirements-scraper.txt
playwright install chromium
```

## 📖 Como usar

### Comando básico
```bash
python scraping.py run --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

### Opções disponíveis
- `--start-date`: Data de início no formato YYYY-MM-DD
- `--end-date`: Data de fim no formato YYYY-MM-DD  
- `--headless`: Força execução sem interface gráfica (padrão em Docker)
- `--no-headless`: Força execução com interface gráfica (apenas fora do Docker)

### Exemplos

**Scraping de um único dia (modo automático):**
```bash
python scraping.py run --start-date 2025-01-15 --end-date 2025-01-15
```

**Scraping de um período:**
```bash
python scraping.py run --start-date 2025-01-15 --end-date 2025-01-20
```

**Scraping da semana passada:**
```bash
python scraping.py run --start-date 2025-01-08 --end-date 2025-01-14
```

**Forçar modo headless:**
```bash
python scraping.py run --start-date 2025-01-15 --end-date 2025-01-15 --headless
```

**Forçar interface gráfica (apenas fora do Docker):**
```bash
python scraping.py run --start-date 2025-01-15 --end-date 2025-01-15 --no-headless
```

## 🔄 Fluxo de Execução

Para cada data no período informado, o scraper executa:

1. **Acesso ao DJE-SP** - Vai para a página de busca avançada
2. **Preenchimento do formulário** - Define datas usando o padrão do projeto (JavaScript com eventos)
3. **Seleção de caderno** - Detecta automaticamente opções disponíveis
4. **Busca de publicações** - Executa a pesquisa com termos "RPV" e "pagamento pelo INSS"
5. **Download de PDFs** - Baixa cada publicação encontrada
6. **Extração de dados** - Retira número do processo e autores do PDF
7. **Consulta no ESAJ** - Busca informações complementares
8. **Extração completa** - Obtém advogados, valores e datas
9. **Salvamento** - Cria arquivo JSON para cada publicação

## 📄 Dados Extraídos

Para cada publicação, o scraper extrai:

- **process_number** - Número do processo (ex: 0003901-40.2025.8.26.0053)
- **publication_date** - Data de publicação (do ESAJ)
- **availability_date** - Data de disponibilização (da busca)
- **authors** - Lista de autores (do PDF)
- **lawyers** - Lista de advogados com nome e OAB (do ESAJ)
- **gross_value** - Valor bruto em centavos (do ESAJ)
- **net_value** - Valor líquido em centavos (do ESAJ)
- **interest_value** - Valor dos juros em centavos (do ESAJ)
- **attorney_fees** - Honorários advocatícios em centavos (do ESAJ)
- **content** - Conteúdo completo sanitizado (do ESAJ)

## 📁 Arquivos de Saída

Os arquivos JSON são salvos em `backend/scraper/reports/json/` com o nome baseado no número do processo:

```
0003901-40_2025_8_26_0053.json
0004123-55_2025_8_26_0100.json
```

Cada arquivo contém todos os dados estruturados da publicação.

## 🔍 Exemplo de Saída JSON

```json
{
  "process_number": "0003901-40.2025.8.26.0053",
  "publication_date": "2025-01-15",
  "availability_date": "2025-01-16",
  "authors": ["Antonio Elias dos Santos"],
  "defendant": "Instituto Nacional do Seguro Social - INSS",
  "lawyers": [
    {
      "name": "Vladimir Renato de Aquino Lopes",
      "oab": "94932/SP"
    }
  ],
  "gross_value": 1242337,
  "net_value": 1242337,
  "interest_value": 808905,
  "attorney_fees": 215976,
  "content": "Conteúdo completo da movimentação sanitizado...",
  "status": "NOVA",
  "scraping_source": "DJE-SP",
  "caderno": "12",
  "instancia": "1",
  "local": "Capital",
  "parte": "1"
}
```

## ⚙️ Configurações

### Browser
- **Modo automático**: Detecta automaticamente se deve executar em modo headless
- **Docker**: Sempre executa em modo headless (sem interface gráfica)
- **Ambiente local**: Por padrão executa em modo headless
- **Forçar modo**: Use `--headless` ou `--no-headless` para controlar manualmente

### Detecção automática de ambiente
O scraper detecta automaticamente:
- Se está executando em container Docker (arquivo `/.dockerenv`)
- Se há servidor X disponível (variável `$DISPLAY`)
- Se está em ambiente CI/CD
- Força modo headless nesses cenários

### Timeouts
- Timeout padrão: 30 segundos
- Pause entre datas: 2 segundos
- Aguardo após cliques: 2-3 segundos

### Arquivos Temporários
- PDFs são baixados em diretório temporário
- Limpeza automática ao final da execução

## 🛠️ Manutenção

### Logs
O scraper gera logs detalhados mostrando:
- Progresso do processamento
- Erros encontrados
- Estatísticas de cada dia

### Monitoramento
Ao final da execução, são exibidas estatísticas:
- Dias processados
- Publicações encontradas
- Publicações salvas com sucesso
- Falhas ocorridas

### Tratamento de Erros
- Continua execução mesmo com falhas pontuais
- Registra todos os erros para análise
- Limpa recursos automaticamente

## 🐛 Solução de Problemas

Para problemas específicos, consulte o [**Guia de Troubleshooting**](TROUBLESHOOTING.md).

### Debug rápido do campo caderno:
```bash
python debug-caderno.py
```

### Problemas comuns:

**Erro "playwright not found":**
```bash
playwright install chromium
```

**Erro "PyPDF2 not found":**
```bash
pip install PyPDF2==3.0.1
```

**Timeout na seleção do caderno:**
- Execute `python debug-caderno.py` para ver opções disponíveis
- O scraper agora detecta automaticamente as opções corretas
- Verifique logs para ver qual caderno foi selecionado

**Timeout nos sites:**
- Verifique conexão com internet
- Sites podem estar temporariamente lentos
- Tente novamente mais tarde

**PDFs não encontrados:**
- Pode não haver publicações para a data
- Verifique se os termos de busca estão corretos
- Execute debug para verificar se a busca está funcionando

**Erro de permissão:**
```bash
chmod +x scraping.py
chmod +x install-scraper.sh
chmod +x debug-caderno.py
```

## 📝 Notas Importantes

1. **Compatibilidade**: Implementado seguindo os padrões já existentes no projeto (dje_scraper_adapter.py)
2. **Responsabilidade**: Use o scraper de forma responsável, respeitando os termos de uso dos sites
3. **Rate Limiting**: O scraper inclui pausas para não sobrecarregar os servidores
4. **Backup**: Os arquivos JSON são a única persistência dos dados
5. **Atualização**: Atualize o Playwright regularmente para manter compatibilidade

## 🔗 Integração com o Projeto

Este scraper usa os mesmos padrões de:
- Manipulação de datas via JavaScript com eventos
- Estrutura de entidades (Publication, Lawyer, MonetaryValue)
- Sistema de logs da infraestrutura
- Formato JSON compatível com ReportJsonSaver 