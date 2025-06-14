"""
Port - Interface do web scraper
"""

from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
from domain.entities.publication import Publication


class WebScraperPort(ABC):
    """
    Interface para web scraping do DJE
    """

    @abstractmethod
    async def scrape_publications(
        self, search_terms: List[str], max_pages: int = 10
    ) -> AsyncGenerator[Publication, None]:
        """
        Extrai publicações do DJE que contenham os termos de busca

        Args:
            search_terms: Lista de termos que devem estar presentes
            max_pages: Número máximo de páginas para processar

        Yields:
            Publication: Publicações encontradas
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Inicializa o scraper"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Limpeza de recursos"""
        pass
