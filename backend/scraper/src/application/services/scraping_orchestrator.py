"""
Orquestrador principal do processo de scraping
"""

from typing import List
from datetime import datetime
from uuid import uuid4

from application.usecases.extract_publications import ExtractPublicationsUseCase
from application.usecases.save_publications import SavePublicationsUseCase
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
        self.save_usecase = SavePublicationsUseCase()  # Agora usa fila Redis

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

            # Enfileirar publicações para processamento assíncrono
            if publications:
                save_stats = await self.save_usecase.execute(publications)
                execution.publications_new = save_stats[
                    "enqueued"
                ]  # Mudança: agora são enfileiradas
                execution.publications_failed = save_stats["failed"]
                execution.publications_saved = save_stats[
                    "enqueued"
                ]  # Serão processadas pelo worker
                execution.publications_duplicated = (
                    0  # Duplicação será verificada pelo worker
                )

                # Log das estatísticas da fila
                queue_stats = self.save_usecase.get_queue_stats()
                logger.info(f"📊 Estatísticas da fila Redis: {queue_stats}")

            execution.mark_as_completed()
            logger.info(f"✅ Execução {execution.execution_id} concluída com sucesso")
            logger.info(f"📤 {execution.publications_found} publicações extraídas")
            logger.info(f"📝 {execution.publications_new} publicações enfileiradas")

        except Exception as error:
            logger.error(f"❌ Erro na execução {execution.execution_id}: {error}")
            execution.mark_as_failed(
                {"error": str(error), "type": type(error).__name__}
            )

        # Salvar informações da execução (logs locais)
        if hasattr(self.container, "scraping_repository"):
            await self.container.scraping_repository.save_scraping_execution(execution)

        return execution
