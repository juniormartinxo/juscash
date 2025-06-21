# 🛠️ Guia de Solução de Problemas - DJE Scraper

## ❌ Problema: Timeout na seleção do caderno

**Erro típico:**

```txt
Page.select_option: Timeout 30000ms exceeded.
Call log:
- waiting for locator("#cadernos")
- did not find some options
```

### 🔍 Diagnóstico

1. **Execute o script de debug:**

   ```bash
   python debug-caderno.py
   ```

2. **Verifique as opções disponíveis** na saída do script

3. **O script mostrará:**
   - Se o campo #cadernos existe
   - Todas as opções disponíveis com seus valores
   - Se a opção "12" existe
   - Sugestões de opções adequadas

### ✅ Soluções Implementadas

O scraper agora inclui:

1. **Detecção automática de opções** - Verifica quais cadernos estão disponíveis
2. **Fallback inteligente** - Tenta várias opções em ordem de prioridade:
   - "12" (preferido)
   - "3" (alternativa comum)  
   - "03" (formato com zero)
   - Busca por texto "Judicial - 1ª Instância"
3. **Log detalhado** - Mostra quais opções foram encontradas
4. **Continuação robusta** - Continua mesmo se não conseguir selecionar caderno específico

### 🔧 Verificações Manuais

Se o problema persistir:

1. **Verifique a conectividade:**

   ```bash
   curl -I https://dje.tjsp.jus.br/cdje/consultaAvancada.do
   ```

2. **Teste em modo não-headless (fora do Docker):**

   ```bash
   python scraping.py run --start-date 2025-01-15 --end-date 2025-01-15 --no-headless
   ```

3. **Verifique logs detalhados**

   - O scraper agora mostra:

4. **Parâmetros**

   - Opções de caderno encontradas
   - Qual caderno foi selecionado
   - Se há resultados de busca

## ❌ Problema: Nenhum resultado encontrado

**Sintomas:**

- "📭 Nenhum resultado encontrado para DD/MM/YYYY"
- Scraper pula para próxima data

### 🔍 Possíveis Causas

1. **Data sem publicações** - Normal, nem todo dia tem publicações de RPV
2. **Problemas de conectividade** - Site lento ou indisponível
3. **Mudanças no site** - Layout ou seletores alterados

### ✅ Verificações

1. **Teste uma data conhecida com resultados:**

   ```bash
   python scraping.py run --start-date 2025-01-15 --end-date 2025-01-15
   ```

2. **Verifique logs**

   - O scraper agora mostra:
   - Se div de resultados foi encontrada
   - Se há mensagens de "nenhum registro"
   - Quantos links de publicação foram encontrados

## ❌ Problema: Erro ao baixar PDF

**Sintomas:**

- "❌ Erro ao baixar PDF"
- Publicações encontradas mas não processadas

### ✅ Soluções

1. **Verificar permissões do diretório temporário**
2. **Espaço em disco suficiente**
3. **Conectividade com site do DJE**

## ❌ Problema: Erro no ESAJ

**Sintomas:**

- "❌ Dados de conteúdo não encontrados para PROCESSO"
- PDF processado mas dados complementares faltando

### ✅ Verificações realizadas

1. **Formato do processo** - Deve ser XXXXXXX-XX.XXXX.8.26.XXXX
2. **Conectividade com ESAJ**
3. **Processo pode estar em segredo de justiça**

## 📊 Logs Úteis

O scraper agora fornece logs detalhados:

```txt
🔍 Opções disponíveis no caderno: [{'value': '3', 'text': 'Judicial - 1ª Instância'}]
✅ Caderno selecionado: 3
🔍 Busca executada, aguardando resultados...
✅ Página de resultados carregada
✅ Encontrados 2 links de publicações
📄 Processando publicação 1/2
📥 PDF baixado: pub_20250620_150730_123456.pdf
💾 Publicação salva: 0003901-40.2025.8.26.0053
```

## 🆘 Quando Buscar Ajuda

Se após seguir este guia o problema persistir:

1. **Colete informações:**
   - Saída completa do `python debug-caderno.py`

   - Logs do scraper com timestamps
   - Data específica que está falhando

2. **Teste isolado:**
   - Execute debug-caderno.py
   - Teste uma única data
   - Verifique conectividade

3. **Informações do ambiente:**
   - Versão do Docker/SO
   - Conectividade de rede
   - Logs de sistema
