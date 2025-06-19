"""
Integração atualizada do DJEScraperAdapter com o parser aprimorado
Demonstra como usar o novo sistema de extração com páginas divididas
"""

# Atualização para o método _process_pdf_content no DJEScraperAdapter

async def _process_pdf_content_enhanced(self, pdf_path: Path, source_url: str = "") -> AsyncGenerator[Publication, None]:
    """
    Versão aprimorada do processamento de PDF que usa o parser enhanced
    com suporte a publicações divididas entre páginas
    """
    logger.info(f"📖 Processando conteúdo do PDF aprimorado: {pdf_path}")

    try:
        # 1. Extrair texto do PDF usando PyPDF2 ou pdfplumber
        text_content = await self._extract_text_from_pdf(pdf_path)
        
        if not text_content or len(text_content.strip()) < 50:
            logger.warning("⚠️ Conteúdo do PDF muito pequeno ou vazio")
            return

        # 2. Extrair número da página da URL/caminho
        page_number = self._extract_page_number_from_url(source_url or str(pdf_path))
        
        logger.info(f"📄 Processando página {page_number or 'desconhecida'} ({len(text_content)} chars)")

        # 3. Usar o parser aprimorado com suporte a páginas divididas
        try:
            enhanced_publications = await self.enhanced_parser.parse_multiple_publications_enhanced(
                text_content, 
                source_url, 
                page_number
            )

            if enhanced_publications:
                logger.info(f"✅ Parser aprimorado extraiu {len(enhanced_publications)} publicações")
                
                for publication in enhanced_publications:
                    logger.info(f"✅ Publicação extraída: {publication.process_number}")
                    
                    # Salvar como JSON
                    await self._save_publication_json(publication)
                    
                    yield publication
            else:
                # Fallback para parser tradicional se o aprimorado não encontrar nada
                logger.info("🔄 Parser aprimorado não encontrou publicações, tentando parser tradicional")
                await self._fallback_to_traditional_parser(text_content, source_url)

        except Exception as e:
            logger.error(f"❌ Erro no parser aprimorado: {e}")
            # Fallback para parser tradicional
            await self._fallback_to_traditional_parser(text_content, source_url)

    except Exception as error:
        logger.error(f"❌ Erro ao processar PDF {pdf_path}: {error}")

async def _extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
    """
    Extrai texto do PDF usando bibliotecas disponíveis
    """
    try:
        # Tentar PyPDF2 primeiro
        try:
            import PyPDF2
            
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                    
            logger.debug(f"✅ Texto extraído com PyPDF2 ({len(text_content)} chars)")
            return text_content
            
        except ImportError:
            logger.debug("PyPDF2 não disponível, tentando pdfplumber")
            
        # Fallback para pdfplumber
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                text_content = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                        
            logger.debug(f"✅ Texto extraído com pdfplumber ({len(text_content)} chars)")
            return text_content
            
        except ImportError:
            logger.error("❌ Nenhuma biblioteca de PDF disponível (PyPDF2 ou pdfplumber)")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao extrair texto do PDF: {e}")
        return None

async def _save_publication_json(self, publication: Publication) -> None:
    """
    Salva publicação como JSON
    """
    try:
        json_path = await self.json_saver.save_publication_json(publication)
        if json_path:
            logger.info(f"📋 JSON salvo: {json_path}")
        else:
            logger.warning(f"⚠️ Falha ao salvar JSON para {publication.process_number}")
    except Exception as json_error:
        logger.error(f"❌ Erro ao salvar JSON: {json_error}")

async def _fallback_to_traditional_parser(self, text_content: str, source_url: str) -> None:
    """
    Fallback para o parser tradicional quando o aprimorado falha
    """
    try:
        logger.info("🔄 Usando parser tradicional como fallback")
        publications = self.parser.parse_multiple_publications(text_content, source_url)
        
        for publication in publications:
            logger.info(f"✅ Publicação extraída (tradicional): {publication.process_number}")
            await self._save_publication_json(publication)
            
    except Exception as e:
        logger.error(f"❌ Erro no parser tradicional: {e}")

# Exemplo de como modificar o __init__ do DJEScraperAdapter
def __init__(self):
    """
    Construtor atualizado do DJEScraperAdapter
    """
    self.settings = get_settings()
    self.browser: Optional[Browser] = None
    self.page: Optional[Page] = None
    self.playwright = None
    
    # Parsers
    self.parser = DJEContentParser()  # Parser tradicional
    self.enhanced_parser = EnhancedDJEContentParser()  # Parser aprimorado
    self.enhanced_parser.set_scraper_adapter(self)  # Importante: definir referência
    
    # Outros componentes
    self.temp_dir = Path(tempfile.gettempdir()) / "dje_scraper_pdfs"
    self.temp_dir.mkdir(exist_ok=True)
    self.failed_pdfs = set()
    
    # JSON saver
    from infrastructure.files.report_json_saver import ReportJsonSaver
    self.json_saver = ReportJsonSaver()
    
    logger.info("🕷️ DJEScraperAdapter inicializado com parser aprimorado")

# Exemplo de uso completo no método principal
async def _download_and_process_pdf_enhanced(self, pdf_url: str) -> AsyncGenerator[Publication, None]:
    """
    Versão aprimorada do download e processamento de PDF
    """
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"📥 Baixando PDF (tentativa {attempt + 1}/{max_retries}): {pdf_url}")

            # Abrir nova aba para download
            pdf_page = await self.browser.new_page()

            try:
                # Configurar timeouts
                pdf_page.set_default_timeout(60000)
                pdf_page.set_default_navigation_timeout(60000)

                # Configurar para interceptar downloads
                download_info = None

                async def handle_download(download):
                    nonlocal download_info
                    download_info = download

                pdf_page.on("download", handle_download)

                # Navegar para URL do PDF
                await pdf_page.goto(pdf_url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Se houve download, processar o arquivo
                if download_info:
                    pdf_path = self.temp_dir / f"dje_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
                    await download_info.save_as(pdf_path)
                    logger.info(f"✅ PDF baixado: {pdf_path}")

                    # Processar PDF com parser aprimorado
                    async for publication in self._process_pdf_content_enhanced(pdf_path, pdf_url):
                        yield publication

                    # Remover arquivo após processamento
                    pdf_path.unlink()
                    return  # Sucesso, sair do loop de retry

                else:
                    # Fallback para conteúdo HTML
                    content = await pdf_page.content()
                    if content and len(content) > 100:
                        logger.info("📄 Processando conteúdo HTML como fallback")
                        
                        # Extrair número da página para o parser aprimorado
                        page_number = self._extract_page_number_from_url(pdf_url)
                        
                        # Usar parser aprimorado mesmo para HTML
                        enhanced_publications = await self.enhanced_parser.parse_multiple_publications_enhanced(
                            content, pdf_url, page_number
                        )
                        
                        for publication in enhanced_publications:
                            await self._save_publication_json(publication)
                            yield publication

            finally:
                await pdf_page.close()

        except Exception as error:
            logger.warning(f"⚠️ Erro na tentativa {attempt + 1} para PDF {pdf_url}: {error}")

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.info(f"🔄 Aguardando {delay}s antes da próxima tentativa...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"❌ Falha definitiva ao processar PDF após {max_retries} tentativas: {pdf_url}")
                self.failed_pdfs.add(pdf_url)

# Exemplo de configuração para usar data específica
def set_target_date(self, date_str: str):
    """
    Define uma data específica para busca (formato DD/MM/YYYY)
    Usado pelo multi-date scraper
    """
    self._target_date = date_str
    logger.info(f"📅 Data alvo definida: {date_str}")

# Integração com o MultiDateScraper
async def _configure_scraper_for_date_enhanced(self, web_scraper, date_str: str):
    """
    Versão aprimorada da configuração de data
    """
    if hasattr(web_scraper, 'set_target_date'):
        web_scraper.set_target_date(date_str)
    else:
        setattr(web_scraper, '_target_date', date_str)
    
    logger.info(f"📅 Scraper configurado para data: {date_str}")

# Exemplo de como usar no main.py ou script principal
async def main_example():
    """
    Exemplo de uso do sistema completo
    """
    from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
    
    # Inicializar scraper
    scraper = DJEScraperAdapter()
    await scraper.initialize()
    
    try:
        # Definir data específica (opcional)
        scraper.set_target_date("17/03/2025")
        
        # Executar scraping
        search_terms = ["RPV", "pagamento pelo INSS"]
        
        async for publication in scraper.scrape_publications(search_terms, max_pages=5):
            logger.info(f"📋 Publicação processada: {publication.process_number}")
            logger.info(f"👥 Autores: {publication.authors}")
            logger.info(f"⚖️ Advogados: {len(publication.lawyers)}")
            
            # Verificar se foi merged de páginas
            if publication.extraction_metadata.get('content_was_merged'):
                logger.info("🔗 Esta publicação foi recuperada através de merge de páginas")
                
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_example())
