"""
Orquestrador principal do processo de scraping
"""

from typing import List
from datetime import datetime
from uuid import uuid4

from application.usecases.extract_publications import ExtractPublicationsUseCase
from application.usecases.save_publications_to_files import SavePublicationsToFilesUseCase
from domain.entities.scraping_execution import ScrapingExecution, ExecutionType
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ScrapingOrchestrator:
    """
    Orquestra todo o processo de scraping diário
    """

    def __init__(self, container):
        self.container = container
        self.extract_usecase = ExtractPublicationsUseCase(container.web_scraper)
        self.save_usecase = SavePublicationsToFilesUseCase()  # Agora salva em arquivos locais

    async def execute_daily_scraping(self) -> ScrapingExecution:
        """
        Executa o processo completo de scraping diário
        """
        execution = ScrapingExecution(
            execution_id=str(uuid4()),
            execution_type=ExecutionType.SCHEDULED,
            criteria_used={
                "search_terms": [
                    "RPV",
                    "pagamento pelo INSS",
                ],  # Termos corretos para RPV
                "caderno": "3",
                "instancia": "1",
                "local": "Capital",
                "parte": "1",
            },
        )

        try:
            logger.info(f"🚀 Iniciando execução {execution.execution_id}")

            # Termos de busca obrigatórios (podem vir de configuração)
            search_terms = ["RPV", "pagamento pelo INSS"]  # Configurável

            # Extrair publicações
            publications = []
            async for publication in self.extract_usecase.execute(
                search_terms, max_pages=20
            ):
                publications.append(publication)
                execution.publications_found += 1

            # Salvar publicações em arquivos locais (TXT e JSON)
            if publications:
                save_stats = await self.save_usecase.execute(publications)
                execution.publications_new = save_stats["saved"]
                execution.publications_failed = save_stats["failed"]
                execution.publications_saved = save_stats["saved"]
                execution.publications_duplicated = 0  # Não há verificação de duplicação local

                # Log das estatísticas dos arquivos
                file_stats = self.save_usecase.get_file_stats()
                logger.info(f"📊 Estatísticas dos arquivos: {file_stats}")

            execution.mark_as_completed()
            logger.info(f"✅ Execução {execution.execution_id} concluída com sucesso")
            logger.info(f"📤 {execution.publications_found} publicações extraídas")
            logger.info(f"💾 {execution.publications_saved} publicações salvas em arquivos")

        except Exception as error:
            logger.error(f"❌ Erro na execução {execution.execution_id}: {error}")
            execution.mark_as_failed(
                {"error": str(error), "type": type(error).__name__}
            )

        # Salvar informações da execução (logs locais)
        if hasattr(self.container, "scraping_repository"):
            await self.container.scraping_repository.save_scraping_execution(execution)

        return execution
