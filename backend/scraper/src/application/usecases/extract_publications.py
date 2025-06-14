"""
Use Case - Extração de publicações
"""

from typing import List, AsyncGenerator
from domain.ports.web_scraper import WebScraperPort
from domain.entities.publication import Publication
from domain.services.publication_validator import PublicationValidator
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ExtractPublicationsUseCase:
    """
    Use case responsável pela extração de publicações do DJE
    """

    def __init__(self, web_scraper: WebScraperPort):
        self.web_scraper = web_scraper
        self.validator = PublicationValidator()

    async def execute(
        self, search_terms: List[str], max_pages: int = 10
    ) -> AsyncGenerator[Publication, None]:
        """
        Executa a extração de publicações

        Args:
            search_terms: Termos que devem estar presentes na publicação
            max_pages: Número máximo de páginas para processar

        Yields:
            Publication: Publicações válidas encontradas
        """
        logger.info(f"🔍 Iniciando extração com termos: {search_terms}")

        try:
            await self.web_scraper.initialize()

            async for publication in self.web_scraper.scrape_publications(
                search_terms, max_pages
            ):
                # Validar publicação extraída
                if self.validator.validate_publication(publication, search_terms):
                    logger.debug(f"✅ Publicação válida: {publication.process_number}")
                    yield publication
                else:
                    logger.warning(
                        f"⚠️  Publicação inválida descartada: {publication.process_number}"
                    )

        except Exception as error:
            logger.error(f"❌ Erro durante extração: {error}")
            raise

        finally:
            await self.web_scraper.cleanup()
