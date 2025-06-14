"""
Entry point do scraper DJE-SP
Execução diária a partir de 17/03/2025
"""

import asyncio
import signal
import sys
from pathlib import Path

# Adicionar o diretório src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logging.logger import setup_logger
from infrastructure.scheduler.scheduler_adapter import SchedulerAdapter
from infrastructure.config.settings import get_settings
from application.services.scraping_orchestrator import ScrapingOrchestrator
from shared.container import Container

logger = setup_logger(__name__)


class ScraperApplication:
    """Aplicação principal do scraper DJE-SP"""

    def __init__(self):
        self.settings = get_settings()
        self.container = Container()
        self.scheduler = SchedulerAdapter()
        self.orchestrator = ScrapingOrchestrator(self.container)
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Inicia a aplicação do scraper"""
        try:
            logger.info("🚀 Iniciando DJE Scraper Application")
            logger.info("📅 Execução programada diária a partir de 17/03/2025")
            logger.info(f"🎯 Target: {self.settings.scraper.target_url}")

            # Registrar handlers de shutdown graceful
            self._register_signal_handlers()

            # Configurar e iniciar scheduler
            await self._setup_scheduler()

            # Manter aplicação rodando
            await self._shutdown_event.wait()

        except Exception as error:
            logger.error(f"❌ Erro fatal na aplicação: {error}")
            raise
        finally:
            await self._cleanup()

    async def _setup_scheduler(self):
        """Configura o agendamento diário do scraper"""
        # Agendar execução diária
        self.scheduler.schedule_daily_scraping(
            start_date="2025-03-17",
            hour=8,  # 08:00 da manhã
            minute=0,
            scraping_function=self._execute_scraping,
        )

        # Permitir execução manual para testes
        if self.settings.environment == "development":
            logger.info("🧪 Modo desenvolvimento: permitindo execução imediata")
            # Executar uma vez para teste
            await self._execute_scraping()

    async def _execute_scraping(self):
        """Executa o processo de scraping"""
        try:
            logger.info("🕷️  Iniciando processo de scraping DJE-SP")

            result = await self.orchestrator.execute_daily_scraping()

            logger.info(
                f"✅ Scraping concluído: {result.publications_found} publicações encontradas"
            )
            logger.info(
                f"📊 Novas: {result.publications_new}, Duplicadas: {result.publications_duplicated}"
            )

        except Exception as error:
            logger.error(f"❌ Erro durante scraping: {error}")
            raise

    def _register_signal_handlers(self):
        """Registra handlers para shutdown graceful"""

        def signal_handler(signum, frame):
            logger.info(f"📡 Sinal {signum} recebido, iniciando shutdown graceful...")
            asyncio.create_task(self._shutdown_event.set())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _cleanup(self):
        """Limpeza de recursos"""
        logger.info("🧹 Executando limpeza de recursos...")
        await self.container.cleanup()
        logger.info("✅ Aplicação finalizada")


async def main():
    """Função principal"""
    app = ScraperApplication()
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("⚠️  Interrupção pelo usuário")
    except Exception as error:
        logger.error(f"❌ Erro não tratado: {error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
