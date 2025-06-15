"""
Use Case - Salvamento de publicações via fila Redis
"""

from typing import List, Dict
from domain.entities.publication import Publication
from infrastructure.queue.redis_queue_adapter import RedisQueueAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class SavePublicationsUseCase:
    """
    Use case responsável pelo enfileiramento de publicações para processamento assíncrono
    """

    def __init__(self):
        self.queue = RedisQueueAdapter()

    async def execute(self, publications: List[Publication]) -> Dict[str, int]:
        """
        Enfileira publicações para processamento assíncrono via Redis

        Args:
            publications: Lista de publicações para enfileirar

        Returns:
            Dict com estatísticas de enfileiramento
        """
        logger.info(f"📝 Iniciando enfileiramento de {len(publications)} publicações")

        if not publications:
            logger.warning("📝 Nenhuma publicação para enfileirar")
            return {"total": 0, "enqueued": 0, "failed": 0}

        try:
            # Enfileirar todas as publicações
            enqueued_count = await self.queue.enqueue_publications(publications)
            failed_count = len(publications) - enqueued_count

            stats = {
                "total": len(publications),
                "enqueued": enqueued_count,
                "failed": failed_count,
            }

            logger.info(f"📊 Enfileiramento concluído: {stats}")

            # Obter estatísticas da fila
            queue_stats = self.queue.get_queue_stats()
            logger.info(
                f"📈 Estado da fila: {queue_stats['total_pending']} publicações pendentes"
            )

            return stats

        except Exception as error:
            logger.error(f"❌ Erro durante enfileiramento: {error}")

            # Retornar estatísticas de falha
            return {
                "total": len(publications),
                "enqueued": 0,
                "failed": len(publications),
            }

    def get_queue_stats(self) -> Dict[str, int]:
        """
        Obtém estatísticas da fila Redis

        Returns:
            Estatísticas da fila
        """
        try:
            return self.queue.get_queue_stats()
        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas da fila: {error}")
            return {"queue_size": 0, "delayed_queue_size": 0, "total_pending": 0}

    def clear_queue_if_development(self):
        """
        Limpa a fila apenas em ambiente de desenvolvimento
        """
        from infrastructure.config.settings import get_settings

        settings = get_settings()
        if settings.environment == "development":
            logger.warning("🧹 Limpando fila Redis (ambiente de desenvolvimento)")
            self.queue.clear_queue()
        else:
            logger.warning("⚠️  Limpeza de fila não permitida em produção")
