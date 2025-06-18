"""
Use Case - Salvamento de publicações em arquivos locais
"""

from typing import List, Dict
from domain.entities.publication import Publication
from infrastructure.files.report_json_saver import ReportJsonSaver
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class SavePublicationsToFilesUseCase:
    """
    Use case responsável pelo salvamento de publicações em arquivos JSON
    """

    def __init__(self):
        self.json_saver = ReportJsonSaver()

    async def execute(self, publications: List[Publication]) -> Dict[str, int]:
        """
        Salva publicações em arquivos JSON

        Args:
            publications: Lista de publicações para salvar

        Returns:
            Dict com estatísticas de salvamento
        """
        logger.info(
            f"📝 Iniciando salvamento de {len(publications)} publicações em JSON"
        )

        if not publications:
            logger.warning("📝 Nenhuma publicação para salvar")
            return {"total": 0, "saved": 0, "failed": 0}

        saved_count = 0
        failed_count = 0

        try:
            for publication in publications:
                try:
                    json_path = await self.json_saver.save_publication_json(publication)

                    if json_path:
                        saved_count += 1
                        logger.info(
                            f"✅ Publicação salva: {publication.process_number}"
                        )
                        logger.debug(f"   📋 JSON: {json_path}")
                    else:
                        failed_count += 1
                        logger.warning(
                            f"⚠️ Falha ao salvar: {publication.process_number}"
                        )

                except Exception as error:
                    failed_count += 1
                    logger.error(
                        f"❌ Erro ao salvar publicação {publication.process_number}: {error}"
                    )

            stats = {
                "total": len(publications),
                "saved": saved_count,
                "failed": failed_count,
            }

            logger.info(f"📊 Salvamento concluído: {stats}")

            json_stats = self.json_saver.get_json_stats()
            logger.info(
                f"📈 Arquivos JSON do dia: {json_stats.get('total_json_files', 0)}"
            )

            return stats

        except Exception as error:
            logger.error(f"❌ Erro durante salvamento: {error}")

            return {
                "total": len(publications),
                "saved": saved_count,
                "failed": len(publications) - saved_count,
            }

    def get_file_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Obtém estatísticas dos arquivos salvos

        Returns:
            Estatísticas dos arquivos JSON
        """
        try:
            return {"json": self.json_saver.get_json_stats()}
        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas dos arquivos: {error}")
            return {"json": {}}
