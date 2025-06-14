"""
Port - Interface do repositório de scraping
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.publication import Publication
from domain.entities.scraping_execution import ScrapingExecution


class ScrapingRepositoryPort(ABC):
    """
    Interface para persistência de dados do scraping
    """

    @abstractmethod
    async def save_publication(self, publication: Publication) -> bool:
        """Salva uma publicação via API"""
        pass

    @abstractmethod
    async def save_scraping_execution(self, execution: ScrapingExecution) -> bool:
        """Salva informações da execução"""
        pass

    @abstractmethod
    async def check_publication_exists(self, process_number: str) -> bool:
        """Verifica se publicação já existe"""
        pass
