"""
Entry point do scraper DJE-SP
Execução diária a partir de 17/03/2025
"""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime

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
            logger.info(
                f"📅 Execução programada diária a partir de {self.settings.scheduler.start_date}"
            )
            logger.info(f"🎯 Target: {self.settings.scraper.target_url}")
            logger.info("💾 Salvando publicações em arquivos locais (TXT e JSON)")

            # Registrar handlers de shutdown graceful
            self._register_signal_handlers()

            # Configurar e iniciar scheduler
            await self._setup_scheduler()

            # Aguardar shutdown
            await self._shutdown_event.wait()

        except Exception as error:
            logger.error(f"❌ Erro fatal na aplicação: {error}")
            raise

    async def _setup_scheduler(self):
        """Configura o scheduler para execução duas vezes por dia"""
        # Agendar execução duas vezes por dia
        self.scheduler.schedule_twice_daily_scraping(
            start_date=self.settings.scheduler.start_date,
            morning_hour=self.settings.scheduler.morning_execution_hour,
            morning_minute=self.settings.scheduler.morning_execution_minute,
            afternoon_hour=self.settings.scheduler.afternoon_execution_hour,
            afternoon_minute=self.settings.scheduler.afternoon_execution_minute,
            scraping_function=self._run_daily_scraping,
        )

        logger.info("⏰ Scheduler configurado para execução duas vezes por dia:")
        logger.info(
            f"🌅 Manhã: {self.settings.scheduler.morning_execution_hour:02d}:"
            f"{self.settings.scheduler.morning_execution_minute:02d}"
        )
        logger.info(
            f"🌇 Tarde: {self.settings.scheduler.afternoon_execution_hour:02d}:"
            f"{self.settings.scheduler.afternoon_execution_minute:02d}"
        )

    async def _run_daily_scraping(self):
        """Executa o scraping (manhã ou tarde)"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            logger.info(f"🔄 Iniciando execução do scraping às {current_time}")
            result = await self.orchestrator.execute_daily_scraping()

            logger.info(f"✅ Execução concluída: {result.execution_id}")
            logger.info(f"📊 Publicações encontradas: {result.publications_found}")
            logger.info(f"💾 Publicações salvas: {result.publications_saved}")

        except Exception as error:
            logger.error(f"❌ Erro na execução: {error}")

    def _register_signal_handlers(self):
        """Registra handlers para shutdown graceful"""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handler para shutdown graceful"""
        logger.info(f"🛑 Sinal de shutdown recebido: {signum}")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Shutdown graceful da aplicação"""
        logger.info("🔄 Iniciando shutdown graceful...")

        # Parar scheduler
        await self.scheduler.shutdown()

        # Cleanup do container
        await self.container.cleanup()

        # Sinalizar shutdown completo
        self._shutdown_event.set()

        logger.info("✅ Shutdown graceful concluído")

        logger.info("✅ Shutdown graceful concluído")


async def main():
    """Função principal"""
    app = ScraperApplication()

    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupção por teclado detectada")
    except Exception as error:
        logger.error(f"❌ Erro não tratado: {error}")
        raise
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
