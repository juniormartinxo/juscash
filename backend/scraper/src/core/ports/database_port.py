from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.core.entities.publication import Publication
from src.shared.value_objects import Status, ProcessNumber


class DatabasePort(ABC):
    """
    Interface para implementações de persistência de dados.
    
    Define o contrato que deve ser implementado por qualquer
    adaptador que realize operações de banco de dados.
    """
    
    @abstractmethod
    async def save_publication(self, publication: Publication) -> Publication:
        """
        Salva uma publicação no banco de dados.
        
        Args:
            publication: Publicação a ser salva
            
        Returns:
            Publicação salva com ID atualizado
            
        Raises:
            DatabaseException: Se houver erro na operação de salvamento
            ValidationException: Se dados da publicação estiverem inválidos
        """
        pass
    
    @abstractmethod
    async def save_publications(self, publications: List[Publication]) -> List[Publication]:
        """
        Salva múltiplas publicações em uma transação.
        
        Args:
            publications: Lista de publicações a serem salvas
            
        Returns:
            Lista de publicações salvas
            
        Raises:
            DatabaseException: Se houver erro na operação de salvamento
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, publication_id: UUID) -> Optional[Publication]:
        """
        Busca uma publicação pelo ID.
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Publicação encontrada ou None
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_process_number(self, process_number: ProcessNumber) -> Optional[Publication]:
        """
        Busca uma publicação pelo número do processo.
        
        Args:
            process_number: Número do processo
            
        Returns:
            Publicação encontrada ou None
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def exists_by_process_number(self, process_number: ProcessNumber) -> bool:
        """
        Verifica se já existe uma publicação com o número do processo.
        
        Args:
            process_number: Número do processo a verificar
            
        Returns:
            True se já existe
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def update_status(self, publication_id: UUID, new_status: Status) -> bool:
        """
        Atualiza o status de uma publicação.
        
        Args:
            publication_id: ID da publicação
            new_status: Novo status
            
        Returns:
            True se atualização foi bem-sucedida
            
        Raises:
            DatabaseException: Se houver erro na atualização
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: Status, limit: Optional[int] = None) -> List[Publication]:
        """
        Busca publicações por status.
        
        Args:
            status: Status das publicações a buscar
            limit: Limite de resultados
            
        Returns:
            Lista de publicações encontradas
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: Status) -> int:
        """
        Conta publicações por status.
        
        Args:
            status: Status a contar
            
        Returns:
            Número de publicações com o status
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        pass