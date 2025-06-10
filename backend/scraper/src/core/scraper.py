import re
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential


class DJEScraper:
    def __init__(self):
        self.base_url = "https://dje.tjsp.jus.br/cdje/index.do"
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        """Context manager para garantir limpeza de recursos"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fecha browser ao sair do context"""
        await self.cleanup()

    async def setup(self):
        """Inicializa o browser com configurações otimizadas"""
        playwright = await async_playwright().start()

        # Configurações do browser
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-gpu",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        # Context com configurações anti-detecção
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            ignore_https_errors=True,
            # Bloquear recursos desnecessários para performance
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )

        # Interceptar e bloquear imagens/fonts para performance
        await self.context.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2}", lambda route: route.abort()
        )

        self.page = await self.context.new_page()

        # Configurar timeouts
        self.page.set_default_timeout(30000)  # 30 segundos
        self.page.set_default_navigation_timeout(30000)

        logger.info("Browser configurado com sucesso")

    async def cleanup(self):
        """Fecha o browser e limpa recursos"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def navigate_to_caderno(self):
        """Navega até o Caderno 3 - Judicial - 1ª Instância - Capital Parte 1"""
        try:
            logger.info("Acessando DJE...")
            await self.page.goto(self.base_url, wait_until="networkidle")

            # Playwright aguarda automaticamente elementos ficarem visíveis
            # Localizar e clicar no Caderno 3
            await self.page.click('text="Caderno 3"')

            # Aguardar navegação
            await self.page.wait_for_load_state("networkidle")

            # Selecionar 1ª Instância - Capital Parte 1
            await self.page.click("text=/.*Judicial.*1ª Instância.*Capital.*Parte 1/")

            await self.page.wait_for_load_state("domcontentloaded")
            logger.info("Navegação concluída com sucesso")

        except Exception as e:
            logger.error(f"Erro na navegação: {e}")
            # Capturar screenshot para debug
            await self.page.screenshot(
                path=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            raise

    async def search_publications(self, required_terms: List[str]) -> List[Dict]:
        """Busca publicações que contenham TODOS os termos obrigatórios"""
        publications = []

        try:
            # Localizar campo de busca (adaptar seletores conforme site real)
            search_input = await self.page.wait_for_selector(
                '#searchInput, input[name="search"], input[type="search"]'
            )

            # Construir query de busca
            search_query = " ".join(required_terms)
            await search_input.fill(search_query)

            # Submeter busca
            await self.page.press("#searchInput", "Enter")
            # Ou clicar no botão se houver
            # await self.page.click('button[type="submit"], #searchButton')

            # Aguardar resultados carregarem
            await self.page.wait_for_load_state("networkidle")

            # Processar todas as páginas de resultados
            has_next_page = True
            page_num = 1

            while has_next_page:
                logger.info(f"Processando página {page_num} de resultados...")

                # Extrair publicações da página atual
                page_publications = await self._extract_publications_from_page(
                    required_terms
                )
                publications.extend(page_publications)

                # Verificar se há próxima página
                next_button = await self.page.query_selector(
                    'a:has-text("Próxima"), button:has-text(">")'
                )

                if next_button and await next_button.is_enabled():
                    await next_button.click()
                    await self.page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    has_next_page = False

            logger.info(f"Total de publicações encontradas: {len(publications)}")

        except Exception as e:
            logger.error(f"Erro na busca: {e}")

        return publications

    async def _extract_publications_from_page(
        self, required_terms: List[str]
    ) -> List[Dict]:
        """Extrai publicações da página atual que contenham TODOS os termos"""
        publications = []

        # Obter todos os elementos de publicação
        publication_elements = await self.page.query_selector_all(
            ".publication, article, .processo"
        )

        for element in publication_elements:
            # Obter HTML do elemento
            html = await element.inner_html()
            text_content = await element.text_content()

            # Verificar se contém TODOS os termos obrigatórios
            if all(term.lower() in text_content.lower() for term in required_terms):
                publication_data = await self._extract_publication_data(element, html)
                if publication_data:
                    publications.append(publication_data)

        return publications

    async def _extract_publication_data(self, element, html: str) -> Optional[Dict]:
        """Extrai dados detalhados de uma publicação"""
        try:
            soup = BeautifulSoup(html, "lxml")

            # Clicar no elemento para abrir detalhes (se necessário)
            await element.click()
            await self.page.wait_for_load_state("networkidle")

            # Capturar conteúdo completo
            full_content = await self.page.text_content("body")

            data = {
                "process_number": self._extract_process_number(full_content),
                "availability_date": self._extract_availability_date(full_content),
                "publication_date": datetime.now().date(),
                "authors": self._extract_authors(full_content),
                "defendant": "Instituto Nacional do Seguro Social - INSS",
                "lawyers": self._extract_lawyers(full_content),
                "gross_value": self._extract_value(full_content, "principal|bruto"),
                "net_value": self._extract_value(full_content, "líquido"),
                "interest_value": self._extract_value(full_content, "juros"),
                "attorney_fees": self._extract_value(full_content, "honorários"),
                "content": full_content,
                "status": "nova",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            # Voltar para lista se necessário
            if await self.page.query_selector(
                '.back-button, button:has-text("Voltar")'
            ):
                await self.page.click('.back-button, button:has-text("Voltar")')
                await self.page.wait_for_load_state("networkidle")

            return data if data["process_number"] else None

        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return None

    def _extract_process_number(self, text: str) -> Optional[str]:
        """Extrai número do processo usando regex"""
        # Padrão: XXXX.X.XX.XXXX.X.XX.XXXX
        pattern = r"\d{4}\.\d\.\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_availability_date(self, text: str) -> Optional[datetime]:
        """Extrai data de disponibilização"""
        # Padrões comuns de data
        patterns = [
            r"Disponibilização:\s*(\d{2}/\d{2}/\d{4})",
            r"DJE\s+de\s+(\d{2}/\d{2}/\d{4})",
            r"Publicado\s+em\s+(\d{2}/\d{2}/\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                return datetime.strptime(date_str, "%d/%m/%Y").date()

        return None

    def _extract_authors(self, text: str) -> List[str]:
        """Extrai autores da publicação"""
        authors = []

        # Padrões para encontrar autores
        patterns = [
            r"Autor[a]?:\s*([^\n]+)",
            r"Requerente:\s*([^\n]+)",
            r"Exequente:\s*([^\n]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            authors.extend(matches)

        # Limpar e remover duplicatas
        authors = list(set(author.strip() for author in authors if author.strip()))
        return authors

    def _extract_lawyers(self, text: str) -> List[Dict[str, str]]:
        """Extrai advogados com OAB"""
        lawyers = []

        # Padrão: Nome do Advogado - OAB/SP XXXXX
        pattern = r"([^-\n]+?)\s*-\s*OAB/\w+\s*(\d+)"
        matches = re.findall(pattern, text)

        for name, oab in matches:
            lawyers.append({"name": name.strip(), "oab": oab.strip()})

        return lawyers

    def _extract_value(self, text: str, value_type: str) -> float:
        """Extrai valores monetários"""
        # Padrão para valores em R$
        pattern = rf"{value_type}[^R$]*R\$\s*([\d.,]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value_str = match.group(1)
            # Converter para float
            value_str = value_str.replace(".", "").replace(",", ".")
            try:
                return float(value_str)
            except ValueError:
                return 0.0

        return 0.0
