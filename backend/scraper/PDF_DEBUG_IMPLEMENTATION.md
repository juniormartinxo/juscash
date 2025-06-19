# 🐛 Implementação de Debug de PDFs

## 📋 **RESUMO DAS MODIFICAÇÕES**

Para facilitar o debug do scraper, foram feitas modificações no código para **salvar os PDFs ao invés de deletá-los** após o processamento.

## 🔧 **MODIFICAÇÕES IMPLEMENTADAS**

### 1. **Constructor do DJEScraperAdapter** (`src/infrastructure/web/dje_scraper_adapter.py`)

**ANTES:**
```python
def __init__(self):
    # ... código existente ...
    self.temp_dir = Path(tempfile.gettempdir()) / "dje_scraper_pdfs"
    self.temp_dir.mkdir(exist_ok=True)
```

**DEPOIS:**
```python
def __init__(self):
    # ... código existente ...
    self.temp_dir = Path(tempfile.gettempdir()) / "dje_scraper_pdfs"
    self.temp_dir.mkdir(exist_ok=True)
    
    # 🆕 Pasta para salvar PDFs para debug
    self.pdf_debug_dir = Path("reports/pdf")
    self.pdf_debug_dir.mkdir(parents=True, exist_ok=True)
```

### 2. **Processamento de PDFs** (`método _download_and_process_pdf`)

**ANTES:**
```python
# Processar PDF para extrair publicações
async for publication in self._process_pdf_content(pdf_path):
    yield publication

# Remover arquivo após processamento
pdf_path.unlink()
```

**DEPOIS:**
```python
# Processar PDF para extrair publicações
async for publication in self._process_pdf_content(pdf_path):
    yield publication

# 🐛 MODO DEBUG: Mover PDF para pasta de debug ao invés de apagar
debug_filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
debug_path = self.pdf_debug_dir / debug_filename
pdf_path.rename(debug_path)
logger.info(f"🐛 PDF salvo para debug: {debug_path}")
```

### 3. **Método Cleanup** (`método cleanup`)

**ANTES:**
```python
# Limpar PDFs temporários
try:
    for pdf_file in self.temp_dir.glob("*.pdf"):
        pdf_file.unlink()
    logger.info("🗑️ PDFs temporários removidos")
```

**DEPOIS:**
```python
# Limpar PDFs temporários (mas NÃO os de debug)
try:
    for pdf_file in self.temp_dir.glob("*.pdf"):
        pdf_file.unlink()
    logger.info("🗑️ PDFs temporários removidos")
    logger.info(f"🐛 PDFs de debug mantidos em: {self.pdf_debug_dir}")
```

## 📁 **ESTRUTURA DE ARQUIVOS**

Após as modificações, os PDFs serão salvos em:
```
backend/scraper/reports/pdf/
├── debug_20250619_185723_123456.pdf
├── debug_20250619_185724_234567.pdf
└── debug_20250619_185725_345678.pdf
```

## 🔍 **COMO USAR PARA DEBUG**

### 1. **Executar o Scraper Normalmente**
```bash
cd backend/scraper
python scraper_cli.py run --search-terms "RPV" --max-pages 2
```

### 2. **Verificar PDFs Salvos**
```bash
ls -la reports/pdf/
```

### 3. **Analisar PDFs Individuais**
Os PDFs podem ser abertos com qualquer visualizador para análise manual:
- **Nome do arquivo** inclui timestamp preciso para identificação
- **Conteúdo original** do DJE sem modificações
- **Permite verificação** se o parser está extraindo corretamente

## 🎯 **BENEFÍCIOS DO DEBUG**

1. **🔍 Análise Visual**: Comparar PDF original com dados extraídos
2. **🐛 Identificação de Problemas**: Ver exatamente onde o parser falha
3. **📊 Validação de Dados**: Confirmar se advogados/processos estão corretos
4. **🔧 Melhoria Contínua**: Refinar padrões regex baseado em casos reais

## ⚠️ **CONSIDERAÇÕES IMPORTANTES**

### **Espaço em Disco**
- PDFs podem ocupar espaço considerável (2-10MB cada)
- Implementar limpeza periódica se necessário:
```bash
# Manter apenas PDFs dos últimos 7 dias
find reports/pdf/ -name "debug_*.pdf" -mtime +7 -delete
```

### **Privacidade**
- PDFs contêm dados públicos do DJE
- Garantir que pasta `reports/pdf/` está no `.gitignore`
- Não fazer commit dos PDFs para o repositório

### **Performance**
- Operação `rename()` é mais rápida que `copy()`
- Não impacta significativamente a performance do scraper
- Apenas muda destino do arquivo

## 🔄 **REVERTER AS MUDANÇAS**

Para desabilitar o debug e voltar ao comportamento original:

```python
# Substituir esta linha:
pdf_path.rename(debug_path)
logger.info(f"🐛 PDF salvo para debug: {debug_path}")

# Por esta:
pdf_path.unlink()
```

## 🧪 **TESTE DE VALIDAÇÃO**

Foi criado um script de teste em `test_debug_pdf_save.py` para validar a funcionalidade:

```bash
python test_debug_pdf_save.py
```

**Resultado esperado:**
- ✅ Pasta `reports/pdf/` criada automaticamente
- ✅ PDFs salvos com nome timestampado
- ✅ Logs indicando onde os PDFs foram salvos
- ✅ Scraper funciona normalmente

## 📞 **SUPORTE**

Se houver problemas:
1. Verificar se pasta `reports/pdf/` tem permissões de escrita
2. Verificar logs do scraper para mensagens de erro
3. Confirmar que as modificações foram aplicadas corretamente

---
**Data da implementação:** 19/06/2025  
**Versão:** 1.0  
**Status:** ✅ Implementado e testado 