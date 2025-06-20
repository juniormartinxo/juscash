"""
Adaptador otimizado do DJE Scraper - Extrai apenas números de processo sem baixar PDFs
"""

import asyncio
import re
from typing import List, AsyncGenerator, Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page
from domain.entities.publication import Publication, MonetaryValue
from domain.ports.web_scraper import WebScraperPort
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class DJEScraperOptimized(WebScraperPort):
    """
    Versão otimizada do scraper DJE que extrai apenas números de processo
    sem fazer download de PDFs - mais rápido e eficiente
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.settings = get_settings()
        self.base_url = "https://esaj.tjsp.jus.br/cdje/index.do"
        self._target_date = None  # Data específica para buscar

    async def initialize(self) -> None:
        """Inicializa o browser e navegador"""
        logger.info("🚀 Inicializando DJE Scraper Otimizado (sem PDFs)")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        self.page = await self.browser.new_page()
        self.page.set_default_timeout(30000)

        logger.info("✅ Browser inicializado - modo otimizado")

    async def cleanup(self) -> None:
        """Limpa recursos do browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info("🧹 Recursos liberados")

    async def scrape_publications(
        self, search_terms: List[str], max_pages: int = 10
    ) -> AsyncGenerator[Publication, None]:
        """
        Extrai publicações apenas com números de processo (sem baixar PDFs)
        """
        logger.info(f"🔍 Iniciando busca otimizada por: {search_terms}")
        logger.info(f"📄 Máximo de páginas: {max_pages}")

        try:
            # Navegar para página de busca
            await self._navigate_to_advanced_search()

            # Preencher formulário
            await self._fill_advanced_search_form(search_terms)

            # Extrair números de processo das páginas de resultado
            async for publication in self._extract_process_numbers(max_pages):
                yield publication

        except Exception as error:
            logger.error(f"❌ Erro durante scraping otimizado: {error}")
            raise

    async def _navigate_to_advanced_search(self) -> None:
        """Navega para página de consulta avançada"""
        logger.info(f"📍 Navegando para {self.base_url}")

        await self.page.goto(self.base_url, wait_until="networkidle")
        await asyncio.sleep(2)

        # Tentar múltiplos seletores para "Consulta Avançada"
        selectors = [
            'a:text("Consulta Avançada")',
            'a:has-text("Consulta Avançada")',
            'a[href*="consultaAvancada"]',
            "text=Consulta Avançada",
            '//a[contains(text(), "Consulta Avançada")]',
        ]

        clicked = False
        for selector in selectors:
            try:
                logger.debug(f"🔍 Tentando selector: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    clicked = True
                    logger.info(f"✅ Clicou em Consulta Avançada usando: {selector}")
                    break
            except:
                continue

        if not clicked:
            # Se não encontrou, tentar navegar direto para URL de consulta avançada
            logger.warning("⚠️ Não encontrou link, tentando URL direta")
            advanced_url = "https://esaj.tjsp.jus.br/cdje/consultaAvancada.do"
            await self.page.goto(advanced_url, wait_until="networkidle")

        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        logger.info("✅ Página de consulta avançada carregada")

    async def _fill_advanced_search_form(self, search_terms: List[str]) -> None:
        """Preenche formulário de busca avançada"""
        logger.info("📝 Preenchendo formulário de busca")

        # Configurar datas
        if self._target_date:
            logger.info(f"📅 Usando data específica: {self._target_date}")
            await self.page.fill(
                'input[name="dadosConsulta.dtInicio"]', self._target_date
            )
            await self.page.fill('input[name="dadosConsulta.dtFim"]', self._target_date)
        else:
            # Usar data de hoje
            today = datetime.now().strftime("%d/%m/%Y")
            await self.page.fill('input[name="dadosConsulta.dtInicio"]', today)
            await self.page.fill('input[name="dadosConsulta.dtFim"]', today)

        # Selecionar caderno
        await self.page.select_option(
            'select[name="dadosConsulta.cdCaderno"]',
            value="12",  # Judicial - 1ª Instância - Capital
        )

        # Preencher palavras-chave
        keywords = " e ".join([f'"{term}"' for term in search_terms])
        await self.page.fill('textarea[name="dadosConsulta.pesquisaLivre"]', keywords)

        # Submeter formulário
        await self.page.click('input[type="submit"][value="Pesquisar"]')
        await self.page.wait_for_load_state("networkidle")

        logger.info("✅ Busca executada")

    async def _extract_process_numbers(
        self, max_pages: int
    ) -> AsyncGenerator[Publication, None]:
        """
        Extrai números de processo diretamente da página de resultados
        sem baixar PDFs
        """
        current_page = 1
        process_numbers_found = set()  # Para evitar duplicatas

        while current_page <= max_pages:
            logger.info(f"📄 Processando página {current_page}/{max_pages}")

            try:
                # Aguardar elementos carregarem
                await self.page.wait_for_selector("tr.ementaClass", timeout=10000)

                # Buscar todos os elementos com links
                elements = await self.page.query_selector_all("tr.ementaClass")
                logger.info(f"✅ Encontrados {len(elements)} elementos na página")

                # Extrair texto de cada elemento
                for i, element in enumerate(elements):
                    try:
                        # Pegar texto completo do elemento
                        text_content = await element.text_content()

                        if text_content:
                            # Buscar números de processo no texto
                            # Padrão: XXXXXXX-XX.XXXX.X.XX.XXXX
                            process_pattern = (
                                r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"
                            )
                            matches = re.findall(process_pattern, text_content)

                            for process_number in matches:
                                if process_number not in process_numbers_found:
                                    process_numbers_found.add(process_number)

                                    # Criar publicação básica
                                    publication = self._create_basic_publication(
                                        process_number, text_content
                                    )

                                    logger.info(
                                        f"✅ Processo encontrado: {process_number}"
                                    )
                                    yield publication

                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao processar elemento {i}: {e}")
                        continue

                # Verificar se há próxima página
                has_next = await self._navigate_to_next_page()
                if not has_next:
                    logger.info("📄 Não há mais páginas")
                    break

                current_page += 1
                await asyncio.sleep(1)  # Delay entre páginas

            except Exception as error:
                logger.error(f"❌ Erro na página {current_page}: {error}")
                break

        logger.info(
            f"✅ Total de processos únicos encontrados: {len(process_numbers_found)}"
        )

    def _create_basic_publication(
        self, process_number: str, content: str
    ) -> Publication:
        """
        Cria uma publicação básica com dados mínimos
        Os dados completos serão obtidos do e-SAJ posteriormente
        """
        # Extrair autores do conteúdo se possível
        authors = []
        author_pattern = r"(?:Autor|Requerente|Exequente):\s*([^-\n]+)"
        author_matches = re.findall(author_pattern, content, re.IGNORECASE)
        if author_matches:
            authors = [
                match.strip() for match in author_matches[:3]
            ]  # Máximo 3 autores

        # Criar publicação com dados básicos
        return Publication(
            process_number=process_number,
            publication_date=datetime.now(),  # Será atualizada pelo e-SAJ
            availability_date=datetime.now(),  # Será atualizada pelo e-SAJ
            authors=authors if authors else ["A definir"],
            lawyers=[],  # Será preenchido pelo e-SAJ
            gross_value=MonetaryValue.from_real(0),  # Será atualizado pelo e-SAJ
            interest_value=MonetaryValue.from_real(0),  # Será atualizado pelo e-SAJ
            attorney_fees=MonetaryValue.from_real(0),  # Será atualizado pelo e-SAJ
            content=content[:500] if content else "",  # Primeiros 500 chars
            defendant="Instituto Nacional do Seguro Social - INSS",
            status="NOVA",
            scraping_source="DJE-SP",
            caderno="3",
            instancia="1",
            local="Capital",
            parte="1",
        )

    async def _navigate_to_next_page(self) -> bool:
        """Navega para próxima página de resultados"""
        try:
            next_selectors = ['a:text("Próxima")', 'a:text(">")', 'a[title*="próxima"]']

            for selector in next_selectors:
                next_element = await self.page.query_selector(selector)
                if next_element:
                    await next_element.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("✅ Navegou para próxima página")
                    return True

            return False

        except Exception as error:
            logger.warning(f"⚠️ Erro ao navegar: {error}")
            return False
