"""
Script para teste manual do scraper (sem agendamento)
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from application.services.scraping_orchestrator import ScrapingOrchestrator
from shared.container import Container
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def run_manual_scraping():
    """Executa scraping manual para testes"""
    logger.info("🕷️  Iniciando teste manual do scraper DJE-SP")

    try:
        # Inicializar container e orquestrador
        container = Container()
        orchestrator = ScrapingOrchestrator(container)

        # Executar scraping
        execution_result = await orchestrator.execute_daily_scraping()

        # Mostrar resultados
        logger.info("📊 Resultados do scraping manual:")
        logger.info(
            f"   🔍 Publicações encontradas: {execution_result.publications_found}"
        )
        logger.info(f"   ✨ Novas publicações: {execution_result.publications_new}")
        logger.info(
            f"   🔄 Publicações duplicadas: {execution_result.publications_duplicated}"
        )
        logger.info(
            f"   ❌ Publicações com falha: {execution_result.publications_failed}"
        )
        logger.info(f"   💾 Publicações salvas: {execution_result.publications_saved}")
        logger.info(f"   ⏱️  Status final: {execution_result.status.value}")

        if execution_result.execution_time_seconds:
            logger.info(
                f"   🕐 Tempo de execução: {execution_result.execution_time_seconds}s"
            )

        # Cleanup
        await container.cleanup()

        logger.info("✅ Teste manual concluído")

    except Exception as error:
        logger.error(f"❌ Erro durante teste manual: {error}")
        raise


if __name__ == "__main__":
    asyncio.run(run_manual_scraping())
