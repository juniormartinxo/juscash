"""
Use Case - Salvamento de publicações em arquivos locais
"""

from typing import List, Dict
from domain.entities.publication import Publication
from infrastructure.files.report_txt_saver import ReportTxtSaver
from infrastructure.files.report_json_saver import ReportJsonSaver
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class SavePublicationsToFilesUseCase:
    """
    Use case responsável pelo salvamento de publicações em arquivos locais (TXT e JSON)
    """

    def __init__(self):
        # Inicializar os salvadores de arquivos
        self.txt_saver = ReportTxtSaver()
        self.json_saver = ReportJsonSaver()

    async def execute(self, publications: List[Publication]) -> Dict[str, int]:
        """
        Salva publicações em arquivos locais (TXT e JSON)

        Args:
            publications: Lista de publicações para salvar

        Returns:
            Dict com estatísticas de salvamento
        """
        logger.info(f"📝 Iniciando salvamento de {len(publications)} publicações em arquivos")

        if not publications:
            logger.warning("📝 Nenhuma publicação para salvar")
            return {"total": 0, "saved": 0, "failed": 0}

        saved_count = 0
        failed_count = 0

        try:
            for publication in publications:
                try:
                    # Salvar como TXT (mantendo funcionalidade existente)
                    txt_path = await self.txt_saver.save_publication_report(publication)
                    
                    # Salvar como JSON (nova funcionalidade)
                    json_path = await self.json_saver.save_publication_json(publication)
                    
                    if txt_path and json_path:
                        saved_count += 1
                        logger.info(f"✅ Publicação salva: {publication.process_number}")
                        logger.debug(f"   📄 TXT: {txt_path}")
                        logger.debug(f"   📋 JSON: {json_path}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Falha parcial ao salvar: {publication.process_number}")
                        
                except Exception as error:
                    failed_count += 1
                    logger.error(f"❌ Erro ao salvar publicação {publication.process_number}: {error}")

            stats = {
                "total": len(publications),
                "saved": saved_count,
                "failed": failed_count,
            }

            logger.info(f"📊 Salvamento concluído: {stats}")

            # Obter estatísticas dos arquivos
            txt_stats = self.txt_saver.get_daily_stats()
            json_stats = self.json_saver.get_json_stats()
            
            logger.info(f"📈 Arquivos TXT do dia: {txt_stats.get('total_files', 0)}")
            logger.info(f"📈 Arquivos JSON do dia: {json_stats.get('total_json_files', 0)}")

            return stats

        except Exception as error:
            logger.error(f"❌ Erro durante salvamento: {error}")

            # Retornar estatísticas de falha
            return {
                "total": len(publications),
                "saved": saved_count,
                "failed": len(publications) - saved_count,
            }

    def get_file_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Obtém estatísticas dos arquivos salvos

        Returns:
            Estatísticas dos arquivos TXT e JSON
        """
        try:
            return {
                "txt": self.txt_saver.get_daily_stats(),
                "json": self.json_saver.get_json_stats()
            }
        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas dos arquivos: {error}")
            return {"txt": {}, "json": {}}