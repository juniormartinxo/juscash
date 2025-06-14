from typing import Optional, Any, Dict, List
import json
import time
import redis.asyncio as redis
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.ports.cache_port import CachePort
from src.shared.logger import get_logger

logger = get_logger(__name__)


class RedisCacheAdapter(CachePort):
    """
    Adaptador Redis para implementação de cache distribuído.

    Fornece cache otimizado com retry logic, health check
    e operações específicas para o domínio de publicações.
    """

    def __init__(self, redis_url: str, **kwargs):
        """
        Inicializa o adaptador Redis.

        Args:
            redis_url: URL de conexão Redis
            **kwargs: Configurações adicionais (max_connections, timeouts, etc.)
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.default_ttl = timedelta(hours=24)

        # Configurações de conexão
        self.max_connections = kwargs.get("max_connections", 20)
        self.retry_on_timeout = kwargs.get("retry_on_timeout", True)
        self.socket_timeout = kwargs.get("socket_timeout", 5)
        self.socket_connect_timeout = kwargs.get("socket_connect_timeout", 5)

    async def initialize(self) -> None:
        """Inicializa conexão com Redis usando pool de conexões."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            await self.client.ping()
            logger.info(
                f"Conexão Redis estabelecida - Pool: {self.max_connections} conexões"
            )
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def _execute_with_retry(self, operation):
        """Executa operação com retry automático."""
        return await operation()

    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache com retry automático.

        Args:
            key: Chave do cache

        Returns:
            Valor armazenado ou None
        """
        if not self.client:
            return None

        async def _get_operation():
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None

        try:
            return await self._execute_with_retry(_get_operation)
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache [{key}]: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        Armazena valor no cache com retry automático.

        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida (opcional)

        Returns:
            True se sucesso, False caso contrário
        """
        if not self.client:
            return False

        async def _set_operation():
            ttl_resolved = ttl or self.default_ttl
            ttl_seconds = int(ttl_resolved.total_seconds())
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl_seconds, serialized)
            return True

        try:
            return await self._execute_with_retry(_set_operation)
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache [{key}]: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        if not self.client:
            return False

        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao deletar do cache [{key}]: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Verifica se chave existe no cache."""
        if not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar cache [{key}]: {str(e)}")
            return False

    # Métodos específicos para publicações
    async def add_process_to_set(self, process_number: str) -> bool:
        """Adiciona número de processo ao set de existentes."""
        if not self.client:
            return False

        try:
            await self.client.sadd("existing_processes", process_number)
            await self.client.expire("existing_processes", 86400)  # 24h
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar processo ao set: {str(e)}")
            return False

    async def is_process_exists(self, process_number: str) -> bool:
        """Verifica se processo já existe no cache."""
        if not self.client:
            return False

        try:
            return await self.client.sismember("existing_processes", process_number)
        except Exception as e:
            logger.error(f"Erro ao verificar processo: {str(e)}")
            return False

    async def cache_search_results(
        self, query_hash: str, results: List[Dict], ttl_minutes: int = 5
    ) -> bool:
        """Cache específico para resultados de busca."""
        return await self.set(
            f"search:{query_hash}", results, timedelta(minutes=ttl_minutes)
        )

    async def get_search_results(self, query_hash: str) -> Optional[List[Dict]]:
        """Recupera resultados de busca do cache."""
        return await self.get(f"search:{query_hash}")

    # Operações em batch
    async def set_many(
        self, items: Dict[str, Any], ttl: Optional[timedelta] = None
    ) -> bool:
        """Armazena múltiplos items em uma operação."""
        if not self.client or not items:
            return False

        try:
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())

            pipe = self.client.pipeline()
            for key, value in items.items():
                serialized = json.dumps(value, default=str)
                pipe.setex(key, ttl_seconds, serialized)

            await pipe.execute()
            logger.info(f"Armazenados {len(items)} items em batch")
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar múltiplos items: {str(e)}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Recupera múltiplos valores em uma operação."""
        if not self.client or not keys:
            return {}

        try:
            values = await self.client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Erro ao deserializar valor para chave {key}")

            return result
        except Exception as e:
            logger.error(f"Erro ao recuperar múltiplos valores: {str(e)}")
            return {}

    # Health check e monitoramento
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da conexão Redis."""
        if not self.client:
            return {"status": "disconnected", "latency": None}

        try:
            start_time = time.time()
            await self.client.ping()
            latency = (time.time() - start_time) * 1000  # ms

            info = await self.client.info("memory")

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "redis_version": info.get("redis_version"),
            }
        except Exception as e:
            logger.error(f"Health check falhou: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    async def clear_all(self) -> bool:
        """Limpa todo o cache."""
        if not self.client:
            return False

        try:
            await self.client.flushdb()
            logger.info("Cache Redis limpo completamente")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False

    async def close(self) -> None:
        """Fecha conexão com Redis."""
        if self.client:
            await self.client.close()
            logger.info("Conexão Redis fechada")
