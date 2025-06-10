from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date

from ..entities.publication import Publication as PublicationEntity


class PublicationRepository(ABC):
    """Interface (Port) para repositório de publicações"""
    
    @abstractmethod
    def save(self, publication: PublicationEntity) -> PublicationEntity:
        """Salva uma publicação no banco de dados"""
        pass
    
    @abstractmethod
    def find_by_process_number(self, process_number: str) -> Optional[PublicationEntity]:
        """Busca uma publicação pelo número do processo"""
        pass
    
    @abstractmethod
    def find_by_id(self, publication_id: str) -> Optional[PublicationEntity]:
        """Busca uma publicação pelo ID"""
        pass
    
    @abstractmethod
    def find_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[PublicationEntity]:
        """Busca todas as publicações com paginação e filtros opcionais"""
        pass
    
    @abstractmethod
    def update_status(self, publication_id: str, new_status: str) -> bool:
        """Atualiza o status de uma publicação"""
        pass
    
    @abstractmethod
    def exists_by_process_number(self, process_number: str) -> bool:
        """Verifica se uma publicação já existe pelo número do processo"""
        pass
    
    @abstractmethod
    def count_by_filters(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta o número de publicações que atendem aos filtros"""
        pass
    
    @abstractmethod
    def delete_by_id(self, publication_id: str) -> bool:
        """Remove uma publicação pelo ID"""
        pass