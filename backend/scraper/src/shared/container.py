"""
Container de dependências - Injeção de Dependência
"""

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.web.dje_scraper_optimized import DJEScraperOptimized
from infrastructure.api.api_client_adapter import ApiClientAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class Container:
    """
    Container de dependências seguindo padrão de injeção de dependência
    """

    def __init__(self, use_optimized_scraper: bool = True):
        self._web_scraper = None
        self._scraping_repository = None
        self._use_optimized_scraper = use_optimized_scraper
        logger.info("📦 Container de dependências inicializado")

    @property
    def web_scraper(self):
        """Lazy loading do web scraper"""
        if self._web_scraper is None:
            if self._use_optimized_scraper:
                self._web_scraper = DJEScraperOptimized()
                logger.info("⚡ DJE Scraper Otimizado criado (sem PDFs)")
            else:
                self._web_scraper = DJEScraperAdapter()
                logger.info("📄 DJE Scraper Tradicional criado (com PDFs)")
        return self._web_scraper

    @property
    def scraping_repository(self) -> ApiClientAdapter:
        """Lazy loading do repositório API"""
        if self._scraping_repository is None:
            self._scraping_repository = ApiClientAdapter()
            logger.debug("📡 API Client Adapter criado")
        return self._scraping_repository

    async def cleanup(self):
        """Limpeza de recursos"""
        logger.info("🧹 Limpando recursos do container")

        if self._web_scraper:
            await self._web_scraper.cleanup()

        logger.info("✅ Limpeza do container concluída")
