from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from src.core.entities.publication import Publication
from src.shared.value_objects import ScrapingCriteria, DJEUrl


class ScraperPort(ABC):
    """
    Interface para implementações de scraping do DJE.
    
    Define o contrato que deve ser implementado por qualquer
    adaptador que realize scraping do Diário da Justiça Eletrônico.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Inicializa o scraper (browser, configurações, etc.).
        
        Raises:
            BrowserException: Se houver erro na inicialização do browser
            ConfigurationException: Se configurações estiverem inválidas
        """
        pass
    
    @abstractmethod
    async def navigate_to_dje(self, url: DJEUrl) -> bool:
        """
        Navega para a página principal do DJE.
        
        Args:
            url: Objeto contendo URLs do DJE
            
        Returns:
            True se navegação foi bem-sucedida
            
        Raises:
            NavigationException: Se não conseguir acessar a página
            TimeoutException: Se timeout na navegação
        """
        pass
    
    @abstractmethod
    async def navigate_to_caderno(self, criteria: ScrapingCriteria) -> bool:
        """
        Navega para o caderno específico conforme critérios.
        
        Args:
            criteria: Critérios de busca incluindo caderno alvo
            
        Returns:
            True se navegação foi bem-sucedida
            
        Raises:
            NavigationException: Se não conseguir acessar o caderno
            ElementNotFoundException: Se elementos de navegação não forem encontrados
        """
        pass
    
    @abstractmethod
    async def extract_publications(self, criteria: ScrapingCriteria, 
                                 max_publications: Optional[int] = None) -> List[Publication]:
        """
        Extrai publicações da página atual que atendem aos critérios.
        
        Args:
            criteria: Critérios de busca e filtragem
            max_publications: Limite máximo de publicações para extrair
            
        Returns:
            Lista de publicações extraídas
            
        Raises:
            ParsingException: Se houver erro no parsing das publicações
            ElementNotFoundException: Se elementos de publicação não forem encontrados
        """
        pass
    
    @abstractmethod
    async def extract_publication_details(self, publication: Publication) -> Publication:
        """
        Extrai detalhes completos de uma publicação específica.
        
        Args:
            publication: Publicação com dados básicos
            
        Returns:
            Publicação com todos os detalhes extraídos
            
        Raises:
            ParsingException: Se houver erro no parsing dos detalhes
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Fecha o scraper e libera recursos (browser, conexões, etc.).
        
        Raises:
            BrowserException: Se houver erro ao fechar o browser
        """
        pass
