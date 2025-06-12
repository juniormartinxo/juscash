from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import timedelta


class CachePort(ABC):
    """
    Interface para implementações de cache.
    
    Define o contrato que deve ser implementado por qualquer
    adaptador que realize operações de cache.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera um valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não existir
            
        Raises:
            CacheException: Se houver erro na operação
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        Armazena um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida do cache
            
        Returns:
            True se operação foi bem-sucedida
            
        Raises:
            CacheException: Se houver erro na operação
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave a remover
            
        Returns:
            True se remoção foi bem-sucedida
            
        Raises:
            CacheException: Se houver erro na operação
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a verificar
            
        Returns:
            True se existe
            
        Raises:
            CacheException: Se houver erro na operação
        """
        pass
    
    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se limpeza foi bem-sucedida
            
        Raises:
            CacheException: Se houver erro na operação
        """
        pass