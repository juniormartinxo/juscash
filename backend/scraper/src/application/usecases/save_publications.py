"""
Use Case - Salvamento de publicações
"""

from typing import List, Dict
from domain.ports.scraping_repository import ScrapingRepositoryPort
from domain.entities.publication import Publication
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class SavePublicationsUseCase:
    """
    Use case responsável pelo salvamento de publicações via API
    """

    def __init__(self, repository: ScrapingRepositoryPort):
        self.repository = repository

    async def execute(self, publications: List[Publication]) -> Dict[str, int]:
        """
        Salva as publicações via API

        Args:
            publications: Lista de publicações para salvar

        Returns:
            Dict com estatísticas de salvamento
        """
        logger.info(f"💾 Iniciando salvamento de {len(publications)} publicações")

        stats = {"total": len(publications), "saved": 0, "duplicated": 0, "failed": 0}

        for publication in publications:
            try:
                # Verificar se já existe
                exists = await self.repository.check_publication_exists(
                    publication.process_number
                )

                if exists:
                    logger.debug(
                        f"📄 Publicação já existe: {publication.process_number}"
                    )
                    stats["duplicated"] += 1
                    continue

                # Salvar nova publicação
                success = await self.repository.save_publication(publication)

                if success:
                    logger.debug(f"✅ Publicação salva: {publication.process_number}")
                    stats["saved"] += 1
                else:
                    logger.warning(f"⚠️  Falha ao salvar: {publication.process_number}")
                    stats["failed"] += 1

            except Exception as error:
                logger.error(f"❌ Erro ao salvar {publication.process_number}: {error}")
                stats["failed"] += 1

        logger.info(f"📊 Salvamento concluído: {stats}")
        return stats
