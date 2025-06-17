"""
Adapter - Implementação do web scraper para DJE-SP
"""

import re
import asyncio
import tempfile
import os
from typing import List, AsyncGenerator, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, Download

from domain.ports.web_scraper import WebScraperPort
from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.web.content_parser import DJEContentParser
from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser
from infrastructure.files.report_txt_saver import ReportTxtSaver
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class DJEScraperAdapter(WebScraperPort):
    """
    Implementação do scraper para o DJE de São Paulo
    Fluxo correto: acessa consultaAvancada.do, encontra links em tr[class="ementaClass"], baixa PDFs
    """

    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.parser = DJEContentParser()
        self.enhanced_parser = EnhancedDJEContentParser()
        self.enhanced_parser.set_scraper_adapter(self)
        self.temp_dir = Path(tempfile.gettempdir()) / "dje_scraper_pdfs"
        self.temp_dir.mkdir(exist_ok=True)
        # Controle de PDFs problemáticos
        self.failed_pdfs = set()  # URLs que falharam múltiplas vezes
        # Instanciar o salvador de relatórios TXT
        self.report_saver = ReportTxtSaver()
        # Instanciar o salvador de relatórios JSON
        from infrastructure.files.report_json_saver import ReportJsonSaver
        self.json_saver = ReportJsonSaver()

    async def initialize(self) -> None:
        """Inicializa o browser e navegação"""
        logger.info("🌐 Inicializando browser Playwright")

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
        )

        self.page = await self.browser.new_page()

        # Configurar timeout e user agent
        await self.page.set_extra_http_headers(
            {"User-Agent": self.settings.browser.user_agent}
        )

        self.page.set_default_timeout(self.settings.browser.timeout)

        logger.info("✅ Browser inicializado com sucesso")

    async def cleanup(self) -> None:
        """Limpeza de recursos"""
        logger.info("🧹 Limpando recursos do browser")

        # Limpar PDFs temporários
        try:
            for pdf_file in self.temp_dir.glob("*.pdf"):
                pdf_file.unlink()
            logger.info("🗑️ PDFs temporários removidos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar PDFs: {e}")

        if self.page:
            await self.page.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

    async def scrape_publications(
        self, search_terms: List[str], max_pages: int = 10
    ) -> AsyncGenerator[Publication, None]:
        """
        Extrai publicações do DJE-SP com o fluxo correto:
        1. Acessa consultaAvancada.do
        2. Preenche formulário de pesquisa avançada
        3. Encontra links em tr[class="ementaClass"]
        4. Baixa PDFs dos links onclick
        5. Processa PDFs para extrair publicações
        """
        logger.info(f"🕷️ Iniciando scraping DJE-SP com termos: {search_terms}")

        try:
            # Navegar para página de consulta avançada
            await self._navigate_to_advanced_search()

            # Preencher formulário de pesquisa avançada
            await self._fill_advanced_search_form(search_terms)

            # Extrair publicações das páginas de resultado
            page_count = 0
            async for publication in self._extract_publications_from_pdf_links(
                max_pages
            ):
                yield publication

        except Exception as error:
            logger.error(f"❌ Erro durante scraping: {error}")
            raise

    async def _navigate_to_advanced_search(self) -> None:
        """Navega para a página de consulta avançada do DJE"""
        target_url = "https://esaj.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada"
        logger.info(f"📍 Navegando para {target_url}")

        await self.page.goto(target_url)
        await self.page.wait_for_load_state("networkidle")

        logger.info("✅ Página de consulta avançada carregada")

    async def _fill_advanced_search_form(self, search_terms: List[str]) -> None:
        """
        Preenche o formulário de pesquisa avançada com critérios específicos da imagem
        Data: 13/11/2024, Caderno 3, Palavras: "RPV" e "pagamento pelo INSS"
        """
        logger.info("📝 Preenchendo formulário de pesquisa avançada")

        try:
            # Aguardar carregamento completo do formulário
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # 1. FORÇAR DATA ESPECÍFICA: 13/11/2024
            logger.info("📅 Configurando data específica: 13/11/2024...")

            # Forçar data início
            data_inicio_script = """
            (() => {
                const dataInicio = document.querySelector('#dtInicioString');
                if (dataInicio) {
                    dataInicio.removeAttribute('readonly');
                    dataInicio.disabled = false;
                    dataInicio.value = '13/11/2024';
                    dataInicio.dispatchEvent(new Event('change', { bubbles: true }));
                    return dataInicio.value;
                }
                return null;
            })()
            """

            # Forçar data fim
            data_fim_script = """
            (() => {
                const dataFim = document.querySelector('#dtFimString');
                if (dataFim) {
                    dataFim.removeAttribute('readonly');
                    dataFim.disabled = false;
                    dataFim.value = '13/11/2024';
                    dataFim.dispatchEvent(new Event('change', { bubbles: true }));
                    return dataFim.value;
                }
                return null;
            })()
            """

            try:
                data_inicio = await self.page.evaluate(data_inicio_script)
                data_fim = await self.page.evaluate(data_fim_script)
                logger.info(f"✅ Datas configuradas: {data_inicio} até {data_fim}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao forçar datas: {e}")

            # 2. SELECIONAR CADERNO - Caderno 3 - Judicial - 1ª Instância - Capital - Parte I
            caderno_selector = 'select[name="dadosConsulta.cdCaderno"]'
            await self.page.wait_for_selector(caderno_selector)

            # Usar value="12" que corresponde ao Caderno 3
            try:
                await self.page.select_option(caderno_selector, value="12")

                # Verificar seleção
                selected_option = await self.page.evaluate(
                    """
                    (() => {
                        const select = document.querySelector('select[name="dadosConsulta.cdCaderno"]');
                        const selectedOption = select.options[select.selectedIndex];
                        return {
                            value: select.value,
                            text: selectedOption.text
                        };
                    })()
                    """
                )

                logger.info(
                    f"✅ Caderno selecionado: {selected_option['text']} (value: {selected_option['value']})"
                )
            except Exception as e:
                logger.error(f"❌ Erro ao selecionar caderno: {e}")

            # 3. PREENCHER PALAVRAS-CHAVE EXATAS
            logger.info("🔍 Preenchendo palavras-chave...")
            search_query = '"RPV" e "pagamento pelo INSS"'

            # Aguardar campo estar disponível
            await self.page.wait_for_selector("#procura", timeout=10000)

            # Preencher usando JavaScript para garantir
            keywords_script = f"""
            (() => {{
                const campo = document.querySelector('#procura');
                if (campo) {{
                    campo.value = '{search_query}';
                    campo.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    campo.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return campo.value;
                }}
                return null;
            }})()
            """

            filled_value = await self.page.evaluate(keywords_script)
            logger.info(f"✅ Palavras-chave preenchidas: '{filled_value}'")

            # 4. AGUARDAR UM POUCO ANTES DE SUBMETER
            await asyncio.sleep(2)

            # 5. SUBMETER FORMULÁRIO
            submit_selectors = [
                'input[value="Pesquisar"]',
                'button:text("Pesquisar")',
                'input[type="submit"]',
                'button[type="submit"]',
            ]

            submitted = False
            for selector in submit_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    try:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)  # Aguardar resultados carregarem
                        logger.info(f"✅ Formulário submetido (selector: {selector})")
                        submitted = True
                        break
                    except Exception as e:
                        logger.debug(f"Falha ao submeter com {selector}: {e}")

            if not submitted:
                logger.error("❌ Não foi possível submeter o formulário")
                raise Exception("Falha ao submeter formulário")

            logger.info("✅ Pesquisa executada com critérios específicos")

        except Exception as error:
            logger.error(f"❌ Erro ao preencher formulário: {error}")
            # Debug: capturar screenshot
            await self._save_debug_screenshot("form_error")
            raise

    async def _extract_publications_from_pdf_links(
        self, max_pages: int
    ) -> AsyncGenerator[Publication, None]:
        """
        Encontra os links em tr[class="ementaClass"] e baixa os PDFs para processamento
        """
        logger.info("🔍 Buscando links de PDF nos resultados")

        current_page = 1

        while current_page <= max_pages:
            logger.info(f"📄 Processando página {current_page}/{max_pages}")

            try:
                # Aguardar carregamento dos resultados
                await asyncio.sleep(3)

                # Tentar aguardar elementos aparecerem
                try:
                    await self.page.wait_for_selector("tr.ementaClass", timeout=10000)
                except:
                    logger.warning("⚠️ Timeout aguardando tr.ementaClass")

                # Encontrar todos os elementos tr com class="ementaClass"
                ementa_elements = await self.page.query_selector_all("tr.ementaClass")

                if not ementa_elements:
                    logger.warning("⚠️ Nenhum elemento tr.ementaClass encontrado")

                    # Debug: verificar se há outros elementos
                    all_tr = await self.page.query_selector_all("tr")
                    logger.info(f"🔍 Total de elementos tr: {len(all_tr)}")

                    onclick_elements = await self.page.query_selector_all(
                        '[onclick*="consultaSimples.do"]'
                    )
                    logger.info(
                        f"🔍 Elementos com consultaSimples.do: {len(onclick_elements)}"
                    )

                    if onclick_elements:
                        logger.info(
                            "✅ Encontrados elementos com consultaSimples.do, processando diretamente..."
                        )
                        # Processar elementos com onclick diretamente
                        for i, element in enumerate(onclick_elements):
                            try:
                                onclick_attr = await element.get_attribute("onclick")
                                if (
                                    onclick_attr
                                    and "consultaSimples.do" in onclick_attr
                                ):
                                    pdf_url = await self._extract_pdf_url_from_onclick(
                                        onclick_attr
                                    )
                                    if pdf_url:
                                        # Verificar se este PDF já falhou antes
                                        if pdf_url in self.failed_pdfs:
                                            logger.warning(
                                                f"⏭️ Pulando PDF que falhou anteriormente: {pdf_url}"
                                            )
                                            continue

                                        async for (
                                            publication
                                        ) in self._download_and_process_pdf(pdf_url):
                                            yield publication
                            except Exception as e:
                                logger.warning(
                                    f"⚠️ Erro ao processar elemento onclick {i+1}: {e}"
                                )
                                continue

                    break

                logger.info(
                    f"✅ Encontrados {len(ementa_elements)} elementos com links"
                )

                # Processar cada elemento para extrair links
                for i, element in enumerate(ementa_elements):
                    try:
                        # Buscar elementos com onclick que contém links para PDF
                        onclick_elements = await element.query_selector_all(
                            '[onclick*="popup"]'
                        )

                        for onclick_element in onclick_elements:
                            onclick_attr = await onclick_element.get_attribute(
                                "onclick"
                            )

                            if onclick_attr and "consultaSimples.do" in onclick_attr:
                                # Extrair URL do PDF do atributo onclick
                                pdf_url = await self._extract_pdf_url_from_onclick(
                                    onclick_attr
                                )

                                if pdf_url:
                                    # Verificar se este PDF já falhou antes
                                    if pdf_url in self.failed_pdfs:
                                        logger.warning(
                                            f"⏭️ Pulando PDF que falhou anteriormente: {pdf_url}"
                                        )
                                        continue

                                    # Baixar e processar PDF
                                    async for (
                                        publication
                                    ) in self._download_and_process_pdf(pdf_url):
                                        yield publication

                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao processar elemento {i+1}: {e}")
                        continue

                # Tentar navegar para próxima página
                has_next = await self._navigate_to_next_page()
                if not has_next:
                    logger.info("📄 Não há mais páginas disponíveis")
                    break

                current_page += 1

            except Exception as error:
                logger.error(f"❌ Erro na página {current_page}: {error}")
                break

    async def _extract_pdf_url_from_onclick(self, onclick_attr: str) -> Optional[str]:
        """
        Extrai URL do PDF do atributo onclick
        Exemplo: onclick="return popup('/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710');"
        """
        try:
            # Usar regex para extrair a URL do popup
            match = re.search(r"popup\('([^']+)'\)", onclick_attr)
            if match:
                relative_url = match.group(1)
                # Construir URL completa
                base_url = "https://esaj.tjsp.jus.br"
                full_url = f"{base_url}{relative_url}"
                logger.debug(f"📄 URL do PDF extraída: {full_url}")
                return full_url
        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair URL do PDF: {e}")

        return None

    async def _download_and_process_pdf(
        self, pdf_url: str
    ) -> AsyncGenerator[Publication, None]:
        """
        Baixa o PDF e processa seu conteúdo para extrair publicações
        Com retry e timeouts configuráveis
        """
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"📥 Baixando PDF (tentativa {attempt + 1}/{max_retries}): {pdf_url}"
                )

                # Abrir nova aba para download
                pdf_page = await self.browser.new_page()

                try:
                    # Configurar timeouts mais longos para PDFs problemáticos
                    pdf_page.set_default_timeout(60000)  # 60 segundos
                    pdf_page.set_default_navigation_timeout(60000)  # 60 segundos

                    # Configurar para interceptar downloads
                    download_info = None

                    async def handle_download(download: Download):
                        nonlocal download_info
                        download_info = download

                    pdf_page.on("download", handle_download)

                    # Navegar para URL do PDF com timeout específico
                    try:
                        await pdf_page.goto(
                            pdf_url, timeout=60000, wait_until="domcontentloaded"
                        )

                        # Aguardar um pouco para o download começar
                        await asyncio.sleep(2)

                        # Tentar aguardar networkidle com timeout menor
                        try:
                            await pdf_page.wait_for_load_state(
                                "networkidle", timeout=10000
                            )
                        except:
                            logger.debug("⏰ Timeout no networkidle, continuando...")

                    except Exception as nav_error:
                        if "Timeout" in str(nav_error):
                            logger.warning(
                                f"⏰ Timeout na navegação (tentativa {attempt + 1}): {pdf_url}"
                            )
                            if attempt < max_retries - 1:
                                delay = base_delay * (2**attempt)
                                logger.info(
                                    f"🔄 Aguardando {delay}s antes da próxima tentativa..."
                                )
                                await asyncio.sleep(delay)
                                continue
                        raise nav_error

                    # Se houve download, processar o arquivo
                    if download_info:
                        pdf_path = (
                            self.temp_dir
                            / f"dje_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
                        )
                        await download_info.save_as(pdf_path)
                        logger.info(f"✅ PDF baixado: {pdf_path}")

                        # Processar PDF para extrair publicações
                        async for publication in self._process_pdf_content(pdf_path):
                            yield publication

                        # Remover arquivo após processamento
                        pdf_path.unlink()
                        return  # Sucesso, sair do loop de retry

                    else:
                        # Se não houve download, tentar extrair conteúdo da página
                        content = await pdf_page.content()
                        if content and len(content) > 100:
                            logger.info("📄 Processando conteúdo HTML como fallback")
                            # Processar conteúdo HTML como fallback
                            publications = self.parser.parse_multiple_publications(
                                content, pdf_url
                            )
                            for publication in publications:
                                # Salvar relatório como arquivo TXT
                                try:
                                    saved_path = (
                                        await self.report_saver.save_publication_report(
                                            publication
                                        )
                                    )
                                    if saved_path:
                                        logger.info(
                                            f"📄 Relatório TXT salvo (HTML fallback): {saved_path}"
                                        )
                                    else:
                                        logger.warning(
                                            f"⚠️ Falha ao salvar relatório TXT para {publication.process_number}"
                                        )
                                except Exception as txt_error:
                                    logger.error(
                                        f"❌ Erro ao salvar relatório TXT (HTML fallback): {txt_error}"
                                    )

                                # Salvar também como JSON
                                try:
                                    json_path = await self.json_saver.save_publication_json(
                                        publication
                                    )
                                    if json_path:
                                        logger.info(
                                            f"📋 JSON salvo (HTML fallback): {json_path}"
                                        )
                                    else:
                                        logger.warning(
                                            f"⚠️ Falha ao salvar JSON para {publication.process_number}"
                                        )
                                except Exception as json_error:
                                    logger.error(
                                        f"❌ Erro ao salvar JSON (HTML fallback): {json_error}"
                                    )

                                yield publication
                            return  # Sucesso, sair do loop de retry
                        else:
                            logger.warning(
                                "⚠️ Nenhum download detectado e conteúdo insuficiente"
                            )

                finally:
                    await pdf_page.close()

            except Exception as error:
                logger.warning(
                    f"⚠️ Erro na tentativa {attempt + 1} para PDF {pdf_url}: {error}"
                )

                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.info(f"🔄 Aguardando {delay}s antes da próxima tentativa...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"❌ Falha definitiva ao baixar/processar PDF após {max_retries} tentativas: {pdf_url}"
                    )
                    logger.error(f"   Último erro: {error}")
                    # Marcar PDF como problemático para evitar tentativas futuras
                    self.failed_pdfs.add(pdf_url)
                    logger.info(f"🚫 PDF marcado como problemático: {pdf_url}")
                    # Não yieldar nada em caso de falha total

    async def _process_pdf_content(
        self, pdf_path: Path
    ) -> AsyncGenerator[Publication, None]:
        """
        Processa o conteúdo do PDF para extrair publicações
        """
        logger.info(f"📖 Processando conteúdo do PDF: {pdf_path}")

        try:
            # Importar PyPDF2 ou usar alternativa para extrair texto do PDF
            try:
                import PyPDF2

                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""

                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"

                logger.info(f"✅ Texto extraído do PDF ({len(text_content)} chars)")

            except ImportError:
                logger.warning("⚠️ PyPDF2 não disponível, tentando método alternativo")
                # Fallback: usar pdfplumber ou similar
                try:
                    import pdfplumber

                    with pdfplumber.open(pdf_path) as pdf:
                        text_content = ""
                        for page in pdf.pages:
                            text_content += page.extract_text() + "\n"

                    logger.info(
                        f"✅ Texto extraído com pdfplumber ({len(text_content)} chars)"
                    )

                except ImportError:
                    logger.error("❌ Nenhuma biblioteca de PDF disponível")
                    return

            # Usar o parser aprimorado para extrair publicações
            if text_content and len(text_content.strip()) > 50:
                # Tentar primeiro com o parser aprimorado (padrão RPV/INSS)
                try:
                    # Extrair número da página da URL se possível
                    page_number = self._extract_page_number_from_url(str(pdf_path))

                    enhanced_publications = (
                        await self.enhanced_parser.parse_multiple_publications_enhanced(
                            text_content, str(pdf_path), page_number
                        )
                    )

                    if enhanced_publications:
                        logger.info(
                            f"✅ Parser aprimorado extraiu {len(enhanced_publications)} publicações"
                        )
                        for publication in enhanced_publications:
                            logger.info(
                                f"✅ Publicação extraída (aprimorado): {publication.process_number}"
                            )

                            # Salvar relatório como arquivo TXT
                            try:
                                saved_path = (
                                    await self.report_saver.save_publication_report(
                                        publication
                                    )
                                )
                                if saved_path:
                                    logger.info(f"📄 Relatório TXT salvo: {saved_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar relatório TXT para {publication.process_number}"
                                    )
                            except Exception as txt_error:
                                logger.error(
                                    f"❌ Erro ao salvar relatório TXT: {txt_error}"
                                )

                            # Salvar também como JSON
                            try:
                                json_path = await self.json_saver.save_publication_json(
                                    publication
                                )
                                if json_path:
                                    logger.info(f"📋 JSON salvo: {json_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar JSON para {publication.process_number}"
                                    )
                            except Exception as json_error:
                                logger.error(
                                    f"❌ Erro ao salvar JSON: {json_error}"
                                )

                            yield publication
                        logger.info(
                            f"✅ Parser aprimorado extraiu {len(enhanced_publications)} publicações"
                        )
                        for publication in enhanced_publications:
                            logger.info(
                                f"✅ Publicação extraída (aprimorado): {publication.process_number}"
                            )

                            # Salvar relatório como arquivo TXT
                            try:
                                saved_path = (
                                    await self.report_saver.save_publication_report(
                                        publication
                                    )
                                )
                                if saved_path:
                                    logger.info(f"📄 Relatório TXT salvo: {saved_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar relatório TXT para {publication.process_number}"
                                    )
                            except Exception as txt_error:
                                logger.error(
                                    f"❌ Erro ao salvar relatório TXT: {txt_error}"
                                )

                            # Salvar também como JSON
                            try:
                                json_path = await self.json_saver.save_publication_json(
                                    publication
                                )
                                if json_path:
                                    logger.info(f"📋 JSON salvo: {json_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar JSON para {publication.process_number}"
                                    )
                            except Exception as json_error:
                                logger.error(
                                    f"❌ Erro ao salvar JSON: {json_error}"
                                )

                            yield publication
                    else:
                        # Fallback para parser tradicional
                        logger.info("🔄 Usando parser tradicional como fallback")
                        publications = self.parser.parse_multiple_publications(
                            text_content, str(pdf_path)
                        )

                        for publication in publications:
                            logger.info(
                                f"✅ Publicação extraída (tradicional): {publication.process_number}"
                            )

                            # Salvar relatório como arquivo TXT
                            try:
                                saved_path = (
                                    await self.report_saver.save_publication_report(
                                        publication
                                    )
                                )
                                if saved_path:
                                    logger.info(f"📄 Relatório TXT salvo: {saved_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar relatório TXT para {publication.process_number}"
                                    )
                            except Exception as txt_error:
                                logger.error(
                                    f"❌ Erro ao salvar relatório TXT: {txt_error}"
                                )

                            # Salvar também como JSON
                            try:
                                json_path = await self.json_saver.save_publication_json(
                                    publication
                                )
                                if json_path:
                                    logger.info(f"📋 JSON salvo: {json_path}")
                                else:
                                    logger.warning(
                                        f"⚠️ Falha ao salvar JSON para {publication.process_number}"
                                    )
                            except Exception as json_error:
                                logger.error(
                                    f"❌ Erro ao salvar JSON: {json_error}"
                                )

                            yield publication

                except Exception as e:
                    logger.warning(
                        f"⚠️ Erro no parser aprimorado, usando tradicional: {e}"
                    )
                    # Fallback para parser tradicional
                    publications = self.parser.parse_multiple_publications(
                        text_content, str(pdf_path)
                    )

                    for publication in publications:
                        logger.info(
                            f"✅ Publicação extraída (fallback): {publication.process_number}"
                        )

                        # Salvar relatório como arquivo TXT
                        try:
                            saved_path = (
                                await self.report_saver.save_publication_report(
                                    publication
                                )
                            )
                            if saved_path:
                                logger.info(f"📄 Relatório TXT salvo: {saved_path}")
                            else:
                                logger.warning(
                                    f"⚠️ Falha ao salvar relatório TXT para {publication.process_number}"
                                )
                        except Exception as txt_error:
                            logger.error(
                                f"❌ Erro ao salvar relatório TXT: {txt_error}"
                            )

                        # Salvar também como JSON
                        try:
                            json_path = await self.json_saver.save_publication_json(
                                publication
                            )
                            if json_path:
                                logger.info(f"📋 JSON salvo: {json_path}")
                            else:
                                logger.warning(
                                    f"⚠️ Falha ao salvar JSON para {publication.process_number}"
                                )
                        except Exception as json_error:
                            logger.error(
                                f"❌ Erro ao salvar JSON: {json_error}"
                            )

                        yield publication
            else:
                logger.warning("⚠️ Conteúdo do PDF muito pequeno ou vazio")

        except Exception as error:
            logger.error(f"❌ Erro ao processar PDF {pdf_path}: {error}")

    async def _navigate_to_next_page(self) -> bool:
        """Navega para a próxima página de resultados"""
        try:
            # Procurar por link de próxima página
            next_selectors = [
                'a:text("Próxima")',
                'a:text(">")',
                'a[title*="próxima"]',
                'input[value="Próxima"]',
            ]

            for selector in next_selectors:
                next_element = await self.page.query_selector(selector)
                if next_element:
                    await next_element.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("✅ Navegação para próxima página")
                    return True

            logger.info("📄 Nenhum link para próxima página encontrado")
            return False

        except Exception as error:
            logger.warning(f"⚠️ Erro ao navegar para próxima página: {error}")
            return False

    async def _save_debug_screenshot(self, name: str) -> None:
        """Salva screenshot para debug"""
        try:
            screenshot_path = (
                f"debug_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            await self.page.screenshot(path=screenshot_path)
            logger.info(f"🐛 Screenshot de debug: {screenshot_path}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar screenshot: {e}")

    # Métodos legados removidos - agora tudo é processado via PDF
    def _contains_all_terms(self, content: str, search_terms: List[str]) -> bool:
        """Verifica se o conteúdo contém todos os termos obrigatórios"""
        content_lower = content.lower()
        return all(term.lower() in content_lower for term in search_terms)

    def _extract_page_number_from_url(self, url_or_path: str) -> Optional[int]:
        """Extrai número da página da URL ou caminho do PDF"""
        try:
            # Buscar padrão nuSeqpagina=XXXX na URL
            match = re.search(r"nuSeqpagina=(\d+)", url_or_path)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.debug(f"Erro ao extrair número da página: {e}")
        return None
