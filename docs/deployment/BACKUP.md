# 📋 DOCUMENTAÇÃO DE BACKUP - IMPLEMENTAÇÃO ATUAL DO SCRAPER

**Data do Backup**: 19 de dezembro de 2025  
**Branch**: backup/current-scraper-implementation  
**Versão**: 1.0.0 (pré-melhorias)

## 🏗️ **ARQUITETURA ATUAL**

### **Componentes Principais**

```txt
📦 DJE Scraper System v1.0
├── 🕷️ DJEScraperAdapter (infrastructure/web/dje_scraper_adapter.py)
│   ├── Browser: Playwright Chromium
│   ├── Parser: DJEContentParser + EnhancedDJEContentParser
│   ├── PDF Download: Automático via onclick events
│   └── JSON Output: ReportJsonSaver
├── 🧠 Parsers
│   ├── DJEContentParser (básico)
│   ├── EnhancedDJEContentParser (padrão RPV/INSS)
│   └── PublicationValidator
├── 🔄 Orchestrator
│   ├── ScrapingOrchestrator
│   ├── ExtractPublicationsUseCase
│   └── SavePublicationsToFilesUseCase
├── 📊 Monitoring
│   ├── APIWorker (Redis queue processing)
│   ├── FileMonitor
│   └── PerformanceMonitor
└── 🔧 Infrastructure
    ├── Container (DI)
    ├── Settings/Config
    ├── Logging (loguru)
    └── Health Checks
```

## 📋 **FLUXO DE FUNCIONAMENTO ATUAL**

### **1. Inicialização**

1. Container injeta dependências
2. DJEScraperAdapter inicializa Playwright
3. Enhanced parser é configurado com scraper adapter

### **2. Scraping Process**

1. Navega para consultaAvancada.do
2. Preenche formulário (data, termos de busca)
3. Encontra elementos tr.ementaClass
4. Extrai URLs de PDF via onclick events
5. Baixa PDFs em páginas separadas
6. Processa conteúdo via parsers
7. Salva publicações como JSON

### **3. Parsing Strategy**

- **Parser básico**: Regex simples para dados gerais
- **Enhanced parser**: Busca por RPV/INSS com lógica reversa
- **Fallback**: Enhanced → Basic se falhar

## 🔧 **DEPENDÊNCIAS ATUAIS**

### **Python (Scraper)**

```txt
playwright==1.52.0          # Automação browser
loguru==0.7.3               # Logging avançado
pydantic==2.11.5            # Validação de dados
httpx==0.28.1               # HTTP client
beautifulsoup4==4.13.4      # HTML parsing
PyPDF2==3.0.1               # PDF text extraction
pdfplumber==0.11.4          # PDF parsing alternativo
redis==6.2.0                # Queue sistema
psycopg2-binary==2.9.10     # PostgreSQL
SQLAlchemy==2.0.41          # ORM
APScheduler==3.11.0         # Task scheduling
watchdog>=6.0.0             # File monitoring
```

### **Node.js (API)**

```txt
typescript: 5.8.3           # Language
express: 5.1.0              # Web framework
prisma: 6.9.0               # ORM
zod: 3.22.4                 # Validation
winston: 3.11.0             # Logging
jsonwebtoken: 9.0.2        # Auth
swagger-ui-express: 5.0.0   # Documentation
```

## 📊 **LIMITAÇÕES IDENTIFICADAS**

### **1. Publicações Divididas**

❌ **Problema**: Parser não consegue lidar com publicações que começam em uma página e continuam na próxima  
📋 **Comportamento atual**: Perde início ou fim da publicação  
🔧 **Tentativa existente**: Enhanced parser tem método `_download_previous_page()` mas implementação incompleta

### **2. Cache de Páginas**

❌ **Problema**: Não há cache para páginas baixadas  
📋 **Comportamento atual**: Re-baixa a mesma página múltiplas vezes  
🔧 **Impacto**: Performance degradada e potencial rate limiting

### **3. Validação de Merge**

❌ **Problema**: Não há validação se conteúdo merged está correto  
📋 **Comportamento atual**: Pode fazer merge incorreto silenciosamente  
🔧 **Impacto**: Dados incorretos ou incompletos

### **4. Analytics Limitado**

❌ **Problema**: Falta sistema de análise de qualidade das extrações  
📋 **Comportamento atual**: Apenas logs básicos  
🔧 **Impacto**: Difícil identificar problemas de qualidade

### **5. Rate Limiting Básico**

⚠️ **Problema**: Rate limiting simples baseado apenas em delays  
📋 **Comportamento atual**: Delay fixo entre requisições  
🔧 **Impacto**: Pode ser bloqueado pelo servidor

## 📁 **ESTRUTURA DE ARQUIVOS ATUAL**

```txt
backend/scraper/src/
├── application/
│   ├── services/scraping_orchestrator.py
│   └── usecases/
│       ├── extract_publications.py
│       ├── save_publications_to_files.py
│       └── validate_extracted_data.py
├── domain/
│   ├── entities/
│   │   ├── publication.py
│   │   └── scraping_execution.py
│   ├── ports/
│   │   ├── scraping_repository.py
│   │   └── web_scraper.py
│   └── services/
│       └── publication_validator.py
├── infrastructure/
│   ├── api/api_client_adapter.py
│   ├── config/
│   │   ├── settings.py
│   │   └── dynamic_config.py
│   ├── database/repositories/
│   ├── files/report_json_saver.py
│   ├── logging/logger.py
│   ├── monitoring/
│   │   ├── api_worker.py
│   │   ├── file_monitor.py
│   │   └── performance_monitor.py
│   └── web/
│       ├── content_parser.py
│       ├── enhanced_content_parser.py
│       └── dje_scraper_adapter.py
└── shared/container.py
```

## 🔑 **CONFIGURAÇÕES IMPORTANTES**

### **Variáveis de Ambiente**

```bash
# Scraper
SCRAPER_TARGET_URL=https://esaj.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5
SCRAPER_MAX_PAGES=20

# API
API_BASE_URL=http://localhost:3001
SCRAPER_API_KEY=scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/juscash
REDIS_URL=redis://localhost:6379

# Browser
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
```

### **Seletores CSS Utilizados**

```python
# tr.ementaClass - Links para PDFs
ementa_elements = await page.query_selector_all("tr.ementaClass")

# onclick events com popup
onclick_elements = await element.query_selector_all('[onclick*="popup"]')

# Navegação páginas
next_selectors = [
    'a:text("Próxima")',
    'a:text(">")',
    'a[title*="próxima"]',
    'input[value="Próxima"]',
]
```

## 📈 **MÉTRICAS ATUAIS**

### **Performance Típica**

- **PDFs por minuto**: 10-20 (com delays)
- **Taxa de sucesso**: ~85-90%
- **Tempo por página**: 5-10 segundos
- **Memory usage**: 200-400MB

### **Limitações Conhecidas**

- **Publicações perdidas**: ~10-15% (páginas divididas)
- **Re-downloads**: 20-30% das páginas
- **Rate limiting hits**: 2-5% das execuções

## 🚨 **PONTOS CRÍTICOS PARA PRESERVAR**

### **✅ Funcionalidades que FUNCIONAM**

1. **Navegação automatizada** para consultaAvancada.do
2. **Preenchimento de formulário** com data específica
3. **Download de PDFs** via onclick events
4. **Extração básica** de dados de publicações
5. **Salvamento em JSON** estruturado
6. **Rate limiting básico** funcional
7. **Retry logic** em falhas de rede
8. **Logging detalhado** com loguru
9. **Container de DI** funcionando
10. **API integration** via queue Redis

### **⚠️ Configurações Críticas**

1. **User Agent**: Deve ser mantido para evitar bloqueio
2. **Timeouts**: Valores atuais funcionam bem
3. **Seletores CSS**: tr.ementaClass é estável
4. **Termos de busca**: ["RPV", "pagamento pelo INSS"] validados
5. **Headers HTTP**: Configuração atual evita detecção

## 📋 **CHECKLIST DE RECUPERAÇÃO**

### **Se algo der errado com as melhorias:**

1. **Voltar para este branch**:

   ```bash
   git checkout backup/current-scraper-implementation
   ```

2. **Restaurar dependências**:

   ```bash
   cd backend/scraper
   pip install -r requirements.txt
   ```

3. **Verificar configurações**:
   - Variáveis de ambiente (.env)
   - Redis funcionando
   - PostgreSQL funcionando

4. **Testar funcionamento básico**:

   ```bash
   python -m src.main
   ```

5. **Verificar logs**:
   - logs/scraper.log
   - logs/debug_images/ (screenshots)
   - data/json_reports/ (outputs)

## 🎯 **PRÓXIMOS PASSOS (MELHORIAS)**

1. **Implementar Page Manager** para páginas divididas
2. **Sistema de cache** para evitar re-downloads
3. **Validação de merge** robusta
4. **Analytics avançado** de qualidade
5. **Rate limiting inteligente** adaptativo
6. **Testes automatizados** completos
7. **Monitoramento em tempo real** melhorado

---

**📅 Criado em**: 19/12/2025  
**👨‍💻 Responsável**: Sistema automatizado de backup  
**🔄 Versão**: 1.0.0-backup  
**🌟 Status**: ✅ Funcional e estável
