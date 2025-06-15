"""
Adapter - Fila Redis para publicações
"""

import json
import redis
import asyncio
from typing import List, Optional, Dict, Any
from domain.entities.publication import Publication
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class RedisQueueAdapter:
    """
    Adaptador para fila Redis de publicações
    """

    def __init__(self):
        self.settings = get_settings().redis
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Conecta ao Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.settings.host,
                port=self.settings.port,
                password=self.settings.password or None,
                db=self.settings.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Testar conexão
            self.redis_client.ping()
            logger.info(
                f"✅ Conectado ao Redis: {self.settings.host}:{self.settings.port}"
            )

        except Exception as error:
            logger.error(f"❌ Erro ao conectar no Redis: {error}")
            logger.error(f"🔧 Host: {self.settings.host}:{self.settings.port}")
            logger.error(f"🔧 DB: {self.settings.db}")
            raise

    async def enqueue_publications(self, publications: List[Publication]) -> int:
        """
        Enfileira publicações para processamento

        Args:
            publications: Lista de publicações para enfileirar

        Returns:
            Número de publicações enfileiradas
        """
        if not publications:
            logger.warning("📝 Nenhuma publicação para enfileirar")
            return 0

        logger.info(f"📤 Enfileirando {len(publications)} publicações")

        enqueued_count = 0
        failed_count = 0

        for publication in publications:
            try:
                # Converter publicação para JSON
                publication_data = {
                    "process_number": publication.process_number,
                    "publication_date": (
                        publication.publication_date.isoformat()
                        if publication.publication_date
                        else None
                    ),
                    "availability_date": publication.availability_date.isoformat(),
                    "authors": publication.authors,
                    "lawyers": [
                        {"name": lawyer.name, "oab": lawyer.oab}
                        for lawyer in publication.lawyers
                    ],
                    "monetary_values": [],
                    "content": publication.content,
                    "metadata": publication.extraction_metadata or {},
                    "retry_count": 0,
                    "enqueued_at": asyncio.get_event_loop().time(),
                }

                # Adicionar valores monetários se existirem
                if publication.gross_value:
                    publication_data["monetary_values"].append(
                        {
                            "value": publication.gross_value.amount_cents,
                            "type": "gross_value",
                            "description": "Valor bruto",
                        }
                    )

                if publication.net_value:
                    publication_data["monetary_values"].append(
                        {
                            "value": publication.net_value.amount_cents,
                            "type": "net_value",
                            "description": "Valor líquido",
                        }
                    )

                if publication.interest_value:
                    publication_data["monetary_values"].append(
                        {
                            "value": publication.interest_value.amount_cents,
                            "type": "interest_value",
                            "description": "Juros monetários",
                        }
                    )

                if publication.attorney_fees:
                    publication_data["monetary_values"].append(
                        {
                            "value": publication.attorney_fees.amount_cents,
                            "type": "attorney_fees",
                            "description": "Honorários advocatícios",
                        }
                    )

                # Adicionar à fila
                queue_key = self.settings.queue_name
                self.redis_client.lpush(queue_key, json.dumps(publication_data))
                enqueued_count += 1

                logger.debug(f"📝 Enfileirado: {publication.process_number}")

            except Exception as error:
                logger.error(
                    f"❌ Erro ao enfileirar {publication.process_number}: {error}"
                )
                failed_count += 1

        logger.info(
            f"📊 Enfileiramento concluído: {enqueued_count} sucesso, {failed_count} falhas"
        )
        return enqueued_count

    async def dequeue_publication(self) -> Optional[Dict[str, Any]]:
        """
        Remove publicação da fila para processamento

        Returns:
            Dados da publicação ou None se fila vazia
        """
        try:
            queue_key = self.settings.queue_name

            # Usar BRPOP para aguardar com timeout
            result = self.redis_client.brpop(queue_key, timeout=1)

            if result:
                _, publication_json = result
                publication_data = json.loads(publication_json)

                logger.debug(
                    f"📥 Removido da fila: {publication_data.get('process_number')}"
                )
                return publication_data

            return None

        except Exception as error:
            logger.error(f"❌ Erro ao remover da fila: {error}")
            return None

    async def requeue_publication(
        self, publication_data: Dict[str, Any], delay_seconds: int = None
    ):
        """
        Reenfileira publicação após falha

        Args:
            publication_data: Dados da publicação
            delay_seconds: Delay antes de reprocessar (opcional)
        """
        try:
            # Incrementar contador de tentativas
            publication_data["retry_count"] = publication_data.get("retry_count", 0) + 1
            publication_data["requeued_at"] = asyncio.get_event_loop().time()

            if delay_seconds:
                # Usar fila com delay (sorted set com timestamp)
                delay_queue_key = f"{self.settings.queue_name}:delayed"
                score = asyncio.get_event_loop().time() + delay_seconds

                self.redis_client.zadd(
                    delay_queue_key, {json.dumps(publication_data): score}
                )

                logger.debug(
                    f"⏰ Reenfileirado com delay de {delay_seconds}s: {publication_data.get('process_number')}"
                )
            else:
                # Reenfileirar imediatamente
                queue_key = self.settings.queue_name
                self.redis_client.lpush(queue_key, json.dumps(publication_data))

                logger.debug(
                    f"🔄 Reenfileirado: {publication_data.get('process_number')}"
                )

        except Exception as error:
            logger.error(f"❌ Erro ao reenfileirar: {error}")

    async def process_delayed_queue(self):
        """
        Move publicações da fila com delay para fila principal quando apropriado
        """
        try:
            delay_queue_key = f"{self.settings.queue_name}:delayed"
            current_time = asyncio.get_event_loop().time()

            # Buscar publicações prontas para processamento
            ready_items = self.redis_client.zrangebyscore(
                delay_queue_key, 0, current_time, withscores=True
            )

            if ready_items:
                logger.debug(
                    f"⏰ Processando {len(ready_items)} publicações da fila com delay"
                )

                queue_key = self.settings.queue_name
                pipe = self.redis_client.pipeline()

                for item_json, _ in ready_items:
                    # Mover para fila principal
                    pipe.lpush(queue_key, item_json)
                    # Remover da fila com delay
                    pipe.zrem(delay_queue_key, item_json)

                pipe.execute()

                logger.debug(
                    f"✅ {len(ready_items)} publicações movidas para fila principal"
                )

        except Exception as error:
            logger.error(f"❌ Erro ao processar fila com delay: {error}")

    def get_queue_stats(self) -> Dict[str, int]:
        """
        Obtém estatísticas da fila

        Returns:
            Estatísticas da fila
        """
        try:
            queue_key = self.settings.queue_name
            delay_queue_key = f"{self.settings.queue_name}:delayed"

            stats = {
                "queue_size": self.redis_client.llen(queue_key),
                "delayed_queue_size": self.redis_client.zcard(delay_queue_key),
                "total_pending": 0,
            }

            stats["total_pending"] = stats["queue_size"] + stats["delayed_queue_size"]

            return stats

        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas da fila: {error}")
            return {"queue_size": 0, "delayed_queue_size": 0, "total_pending": 0}

    def clear_queue(self):
        """
        Limpa todas as filas (usar apenas em desenvolvimento/testes)
        """
        try:
            queue_key = self.settings.queue_name
            delay_queue_key = f"{self.settings.queue_name}:delayed"

            deleted_main = self.redis_client.delete(queue_key)
            deleted_delay = self.redis_client.delete(delay_queue_key)

            logger.warning(
                f"🧹 Filas limpas: {deleted_main + deleted_delay} chaves removidas"
            )

        except Exception as error:
            logger.error(f"❌ Erro ao limpar filas: {error}")

    def close(self):
        """Fecha conexão com Redis"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("🔌 Conexão Redis fechada")
            except Exception as error:
                logger.error(f"❌ Erro ao fechar conexão Redis: {error}")
