from typing import Optional, Any
import json
import redis.asyncio as redis
from datetime import timedelta

from src.core.ports.cache_port import CachePort
from src.shared.logger import get_logger

logger = get_logger(__name__)


class RedisCacheAdapter(CachePort):
    """
    Adaptador Redis para implementação de cache.
    
    Fornece cache distribuído para otimizar operações
    e evitar processamento duplicado.
    """
    
    def __init__(self, redis_url: str):
        """
        Inicializa o adaptador Redis.
        
        Args:
            redis_url: URL de conexão Redis
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.default_ttl = timedelta(hours=24)
    
    async def initialize(self) -> None:
        """Inicializa conexão com Redis."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Conexão Redis estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None
        """
        if not self.client:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida (opcional)
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.client:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido, False caso contrário
        """
        if not self.client:
            return False
            
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao deletar do cache: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se existe, False caso contrário
        """
        if not self.client:
            return False
            
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar cache: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Fecha conexão com Redis."""
        if self.client:
            await self.client.close()
            logger.info("Conexão Redis fechada") 