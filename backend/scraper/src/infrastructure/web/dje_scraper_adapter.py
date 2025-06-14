"""
Adapter - Implementação do web scraper para DJE-SP
"""

import re
import asyncio
from typing import List, AsyncGenerator, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
from playwright.async_api import async_playwright, Browser, Page

from domain.ports.web_scraper import WebScraperPort
from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class DJEScraperAdapter(WebScraperPort):
    """
    Implementação do scraper para o DJE de São Paulo
    """

    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def initialize(self) -> None:
        """Inicializa o browser e navegação"""
        logger.info("🌐 Inicializando browser Playwright")

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=False,  # self.settings.browser.headless,
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
        Extrai publicações do DJE-SP
        """
        logger.info(f"🕷️  Iniciando scraping DJE-SP com termos: {search_terms}")

        try:
            # Navegar para o DJE
            await self._navigate_to_dje()

            # Acessar Caderno 3 - Judicial - 1ª Instância - Capital Parte 1
            await self._navigate_to_target_section()

            # Extrair publicações das páginas
            page_count = 0
            async for publication in self._extract_publications_from_pages(
                search_terms, max_pages
            ):
                yield publication

        except Exception as error:
            logger.error(f"❌ Erro durante scraping: {error}")
            raise

    async def _navigate_to_dje(self) -> None:
        """Navega para a página principal do DJE"""
        logger.info(f"📍 Navegando para {self.settings.scraper.target_url}")

        await self.page.goto(self.settings.scraper.target_url)

        # Aguardar carregamento da página
        await self.page.wait_for_load_state("networkidle")

        logger.info("✅ Página principal carregada")

    async def _navigate_to_target_section(self) -> None:
        """
        Navega para Caderno 3 - Judicial - 1ª Instância - Capital Parte 1
        Baseado na interface real mostrada nas imagens do DJE
        """
        logger.info(
            "📋 Navegando para Caderno 3 - Judicial - 1ª Instância - Capital Parte 1"
        )

        try:
            # Aguardar página carregar completamente
            await self.page.wait_for_load_state("networkidle")

            input_dt_inicio = await self.page.wait_for_selector("#dtInicioString")
            if input_dt_inicio:
                # O campo está disabled, então não podemos preencher
                # Mas vamos tentar desabilitar o campo
                await input_dt_inicio.evaluate("el => el.disabled = false")
                await input_dt_inicio.evaluate("el => el.readOnly = false")
                await input_dt_inicio.evaluate(
                    "el => el.style.backgroundColor = 'white'"
                )
                await input_dt_inicio.evaluate("el => el.style.color = 'black'")

                await input_dt_inicio.fill("13/11/2024")

            input_dt_fim = await self.page.wait_for_selector("#dtFimString")

            if input_dt_fim:
                await input_dt_fim.evaluate("el => el.disabled = false")
                await input_dt_fim.evaluate("el => el.readOnly = false")
                await input_dt_fim.evaluate("el => el.style.backgroundColor = 'white'")
                await input_dt_fim.evaluate("el => el.style.color = 'black'")

                await input_dt_fim.fill("13/11/2024")

            # Configurar filtros baseados na interface real
            # Campo Caderno - selecionar "Caderno 3 - Judicial - 1ª Instância - Capital - Parte 1"
            caderno_selector = 'select[name="dadosConsulta.cdCaderno"]'
            caderno_element = await self.page.wait_for_selector(caderno_selector)
            if caderno_element:
                # Seleciona pelo value do option
                if await caderno_element.select_option("12"):
                    logger.info("✅ Caderno selecionado com value")
                else:
                    logger.warning("⚠️  Tentando selecionar pelo label")
                    # Valor exato conforme mostrado na imagem
                    if await caderno_element.select_option(
                        caderno_selector,
                        label="caderno 3 - Judicial - 1ª Instância - Capital - Parte I",
                    ):
                        logger.info("✅ Caderno selecionado com label")
                    else:
                        logger.warning("⚠️  Não foi possível selecionar o caderno")

            input_pesquisa = await self.page.wait_for_selector(
                "input[name='dadosConsulta.pesquisaLivre']"
            )
            if await input_pesquisa.evaluate("el => el.disabled = false"):
                await input_pesquisa.evaluate("el => el.readOnly = false")
                await input_pesquisa.evaluate(
                    "el => el.style.backgroundColor = 'white'"
                )
                await input_pesquisa.evaluate("el => el.style.color = 'black'")
                await input_pesquisa.fill("")
                await input_pesquisa.fill('"RPV" e "pagamento pelo INSS"')
                await input_pesquisa.press("Enter")
                logger.info("✅ Campo de pesquisa limpo")
            else:
                logger.warning("⚠️  Campo de pesquisa não está habilitado")

            # Campo Data - deixar em branco para buscar todas as publicações do dia
            # (conforme interface mostrada na imagem)

            # Campo Palavras-chave - inserir termos obrigatórios
            keywords_input = 'input[name*="palavra"], input[name*="termo"], textarea[name*="palavra"]'
            keywords_element = await self.page.query_selector(keywords_input)
            if keywords_element:
                search_terms = " ".join(self.settings.scraper.search_terms)
                await keywords_element.fill(search_terms)
                logger.info(f"✅ Palavras-chave inseridas: {search_terms}")

            # Clicar no botão Pesquisar (como mostrado na imagem)
            search_button = 'input[value="Pesquisar"], button:text("Pesquisar")'
            search_btn = await self.page.query_selector(search_button)
            if search_btn:
                await search_btn.click()
                await self.page.wait_for_load_state("networkidle")
                logger.info("✅ Pesquisa executada")

            # Aguardar resultados carregarem
            await asyncio.sleep(3)

            logger.info("✅ Navegação para seção alvo concluída")

        except Exception as error:
            logger.error(f"❌ Erro ao navegar para seção alvo: {error}")
            # Capturar screenshot para debug
            if self.page:
                debug_path = f"debug_navigation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=debug_path)
                logger.info(f"🐛 Screenshot de debug salvo: {debug_path}")
            raise

    async def _filter_by_instancia_and_location(self) -> None:
        """Filtra por 1ª Instância - Capital Parte 1"""
        # Implementar filtros específicos conforme estrutura da página
        # Exemplo:
        try:
            # Aguardar elementos de filtro
            await asyncio.sleep(2)

            # Selecionar 1ª Instância
            instancia_selector = 'select[name="instancia"], input[value="1"]'
            if await self.page.query_selector(instancia_selector):
                await self.page.select_option(instancia_selector, "1")

            # Selecionar Capital
            capital_selector = 'select[name="local"], input[value="Capital"]'
            if await self.page.query_selector(capital_selector):
                await self.page.select_option(capital_selector, "Capital")

            # Selecionar Parte 1
            parte_selector = 'select[name="parte"], input[value="1"]'
            if await self.page.query_selector(parte_selector):
                await self.page.select_option(parte_selector, "1")

            # Aplicar filtros
            submit_button = 'input[type="submit"], button[type="submit"]'
            if await self.page.query_selector(submit_button):
                await self.page.click(submit_button)
                await self.page.wait_for_load_state("networkidle")

        except Exception as error:
            logger.warning(f"⚠️  Erro ao aplicar filtros: {error}")

    async def _extract_publications_from_pages(
        self, search_terms: List[str], max_pages: int
    ) -> AsyncGenerator[Publication, None]:
        """Extrai publicações de múltiplas páginas"""

        current_page = 1

        while current_page <= max_pages:
            logger.info(f"📄 Processando página {current_page}/{max_pages}")

            try:
                # Extrair publicações da página atual
                publications_count = 0
                async for publication in self._extract_publications_from_current_page(
                    search_terms
                ):
                    yield publication
                    publications_count += 1

                logger.info(
                    f"✅ Página {current_page}: {publications_count} publicações extraídas"
                )

                # Tentar navegar para próxima página
                has_next = await self._navigate_to_next_page()
                if not has_next:
                    logger.info("📄 Não há mais páginas disponíveis")
                    break

                current_page += 1

            except Exception as error:
                logger.error(f"❌ Erro na página {current_page}: {error}")
                break

    async def _extract_publications_from_current_page(
        self, search_terms: List[str]
    ) -> AsyncGenerator[Publication, None]:
        """Extrai publicações da página atual baseado na estrutura real do DJE"""

        # Aguardar carregamento das publicações
        try:
            # Baseado nas imagens, as publicações aparecem em uma estrutura específica
            await self.page.wait_for_selector(
                "table, .resultado, .publicacao", timeout=10000
            )
        except:
            logger.warning("⚠️  Nenhuma publicação encontrada na página")
            return

        # Seletores baseados na estrutura real observada nas imagens
        publication_selectors = [
            'tr:has-text("Caderno 3")',  # Linhas da tabela com Caderno 3
            ".resultado",  # Divs de resultado
            'td:has-text("Processo")',  # Células com processo
            'p:has-text("Processo")',  # Parágrafos com processo
        ]

        publication_elements = []

        # Tentar diferentes seletores para encontrar publicações
        for selector in publication_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    publication_elements = elements
                    logger.info(
                        f"✅ Encontrados {len(elements)} elementos com seletor: {selector}"
                    )
                    break
            except Exception as e:
                logger.debug(f"Seletor {selector} não funcionou: {e}")
                continue

        if not publication_elements:
            logger.warning("⚠️  Nenhum elemento de publicação encontrado")
            return

        for i, element in enumerate(publication_elements):
            try:
                # Extrair texto completo da publicação
                content = await element.inner_text()

                # Verificar se contém todos os termos obrigatórios
                if not self._contains_all_terms(content, search_terms):
                    logger.debug(
                        f"Publicação {i + 1} não contém todos os termos obrigatórios"
                    )
                    continue

                # Parse do conteúdo
                publication = await self._parse_publication_content(content)

                if publication:
                    logger.info(
                        f"✅ Publicação {i + 1} extraída: {publication.process_number}"
                    )
                    yield publication
                else:
                    logger.debug(f"Publicação {i + 1} não pôde ser parseada")

            except Exception as error:
                logger.warning(f"⚠️  Erro ao processar elemento {i + 1}: {error}")
                continue

    def _contains_all_terms(self, content: str, search_terms: List[str]) -> bool:
        """Verifica se o conteúdo contém todos os termos obrigatórios"""
        content_lower = content.lower()
        return all(term.lower() in content_lower for term in search_terms)

    async def _parse_publication_content(self, content: str) -> Optional[Publication]:
        """
        Extrai dados estruturados do conteúdo da publicação
        """
        try:
            # Extrair número do processo
            process_number = self._extract_process_number(content)
            if not process_number:
                return None

            # Extrair outros dados
            publication_date = self._extract_publication_date(content)
            availability_date = (
                self._extract_availability_date(content) or datetime.now()
            )
            authors = self._extract_authors(content)
            lawyers = self._extract_lawyers(content)

            # Extrair valores monetários
            gross_value = self._extract_monetary_value(
                content, "valor bruto", "principal"
            )
            net_value = self._extract_monetary_value(
                content, "valor líquido", "valor devido"
            )
            interest_value = self._extract_monetary_value(content, "juros", "correção")
            attorney_fees = self._extract_monetary_value(
                content, "honorários", "sucumbenciais"
            )

            # Criar entidade Publication
            publication = Publication(
                process_number=process_number,
                publication_date=publication_date,
                availability_date=availability_date,
                authors=authors,
                lawyers=lawyers,
                gross_value=gross_value,
                net_value=net_value,
                interest_value=interest_value,
                attorney_fees=attorney_fees,
                content=content,
                extraction_metadata={
                    "extraction_date": datetime.now().isoformat(),
                    "source_url": self.page.url,
                    "confidence_score": 0.9,
                    "extraction_method": "playwright",
                },
            )

            return publication

        except Exception as error:
            logger.warning(f"⚠️  Erro ao parsear conteúdo: {error}")
            return None

    def _extract_process_number(self, content: str) -> Optional[str]:
        """Extrai número do processo"""
        # Padrão: NNNNNNN-DD.AAAA.J.TR.OOOO
        pattern = r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})"
        match = re.search(pattern, content)
        return match.group(1) if match else None

    def _extract_publication_date(self, content: str) -> Optional[datetime]:
        """Extrai data de publicação"""
        # Padrões comuns de data
        patterns = [
            r"publicad[oa] em (\d{1,2}/\d{1,2}/\d{4})",
            r"data[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%d/%m/%Y")
                except ValueError:
                    continue

        return None

    def _extract_availability_date(self, content: str) -> Optional[datetime]:
        """Extrai data de disponibilização"""
        # Similar à data de publicação, mas pode ter termos específicos
        patterns = [
            r"disponibilizad[oa] em (\d{1,2}/\d{1,2}/\d{4})",
            r"disponível em (\d{1,2}/\d{1,2}/\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%d/%m/%Y")
                except ValueError:
                    continue

        return None

    def _extract_authors(self, content: str) -> List[str]:
        """Extrai lista de autores"""
        # Padrões para identificar autores
        patterns = [
            r"(?:autor|autora|requerente)(?:es)?[:\s]*(.*?)(?:x|versus|vs\.?|réu|advogado)",
            r"(.*?)\s+(?:x|versus|vs\.?)\s+Instituto Nacional",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                authors_text = match.group(1).strip()
                # Dividir por vírgulas ou "e"
                authors = re.split(r"[,;]|\s+e\s+", authors_text)
                return [author.strip() for author in authors if author.strip()]

        return ["Não identificado"]

    def _extract_lawyers(self, content: str) -> List[Lawyer]:
        """Extrai lista de advogados"""
        lawyers = []

        # Padrão para advogados com OAB
        pattern = r"(?:advogad[oa]|dr\.?|dra\.?)[:\s]*([^,]+?)(?:oab[:\s]*(\d+))?"

        matches = re.finditer(pattern, content, re.IGNORECASE)

        for match in matches:
            name = match.group(1).strip()
            oab = match.group(2) if match.group(2) else "Não informado"

            if name and len(name) > 2:  # Filtrar nomes muito curtos
                lawyers.append(Lawyer(name=name, oab=oab))

        return lawyers

    def _extract_monetary_value(
        self, content: str, *keywords
    ) -> Optional[MonetaryValue]:
        """Extrai valores monetários baseado em palavras-chave"""
        for keyword in keywords:
            # Padrões para valores monetários
            patterns = [
                rf"{keyword}[:\s]*r\$\s*([\d.,]+)",
                rf"{keyword}[:\s]*([\d.,]+)",
                rf"r\$\s*([\d.,]+).*?{keyword}",
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        value_str = match.group(1).replace(".", "").replace(",", ".")
                        value = Decimal(value_str)
                        return MonetaryValue.from_real(value)
                    except (ValueError, InvalidOperation):
                        continue

        return None

    async def _navigate_to_next_page(self) -> bool:
        """Navega para a próxima página se disponível"""
        try:
            # Procurar link/botão de próxima página
            next_selectors = [
                'a:text("Próxima")',
                'a:text(">")',
                'a[href*="proxima"]',
                'button:text("Próxima")',
                ".pagination .next",
                ".paginacao .proximo",
            ]

            for selector in next_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await self.page.wait_for_load_state("networkidle")
                    return True

            return False

        except Exception as error:
            logger.warning(f"⚠️  Erro ao navegar para próxima página: {error}")
            return False
