"""
Adapter - Agendador de tarefas
"""

import asyncio
from datetime import datetime, time
from typing import Callable, Awaitable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class SchedulerAdapter:
    """
    Adapter para agendamento de tarefas usando APScheduler
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("📅 Scheduler inicializado")

    def schedule_twice_daily_scraping(
        self,
        start_date: str,
        morning_hour: int,
        morning_minute: int,
        afternoon_hour: int,
        afternoon_minute: int,
        scraping_function: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Agenda execução de scraping duas vezes por dia

        Args:
            start_date: Data de início no formato YYYY-MM-DD
            morning_hour: Hora da execução matinal (0-23)
            morning_minute: Minuto da execução matinal (0-59)
            afternoon_hour: Hora da execução vespertina (0-23)
            afternoon_minute: Minuto da execução vespertina (0-59)
            scraping_function: Função assíncrona a ser executada
        """
        logger.info(
            f"📅 Agendando scraping duas vezes por dia a partir de {start_date}"
        )
        logger.info(f"🌅 Manhã: {morning_hour:02d}:{morning_minute:02d}")
        logger.info(f"🌇 Tarde: {afternoon_hour:02d}:{afternoon_minute:02d}")

        # Configurar trigger cron para execução matinal
        morning_trigger = CronTrigger(
            hour=morning_hour, minute=morning_minute, start_date=start_date
        )

        self.scheduler.add_job(
            func=scraping_function,
            trigger=morning_trigger,
            id="morning_scraping",
            name="Scraping Matinal DJE-SP",
            replace_existing=True,
            max_instances=1,  # Evitar execuções simultâneas
            misfire_grace_time=3600,  # Tolerar 1 hora de atraso
        )

        # Configurar trigger cron para execução vespertina
        afternoon_trigger = CronTrigger(
            hour=afternoon_hour, minute=afternoon_minute, start_date=start_date
        )

        self.scheduler.add_job(
            func=scraping_function,
            trigger=afternoon_trigger,
            id="afternoon_scraping",
            name="Scraping Vespertino DJE-SP",
            replace_existing=True,
            max_instances=1,  # Evitar execuções simultâneas
            misfire_grace_time=3600,  # Tolerar 1 hora de atraso
        )

        logger.info("✅ Scraping duas vezes por dia agendado com sucesso")

    def schedule_daily_scraping(
        self,
        start_date: str,
        hour: int,
        minute: int,
        scraping_function: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Agenda execução diária do scraping (método legado para compatibilidade)

        Args:
            start_date: Data de início no formato YYYY-MM-DD
            hour: Hora da execução (0-23)
            minute: Minuto da execução (0-59)
            scraping_function: Função assíncrona a ser executada
        """
        logger.info(
            f"📅 Agendando scraping diário a partir de {start_date} às {hour:02d}:{minute:02d}"
        )

        # Configurar trigger cron para execução diária
        trigger = CronTrigger(hour=hour, minute=minute, start_date=start_date)

        self.scheduler.add_job(
            func=scraping_function,
            trigger=trigger,
            id="daily_scraping",
            name="Scraping Diário DJE-SP",
            replace_existing=True,
            max_instances=1,  # Evitar execuções simultâneas
            misfire_grace_time=3600,  # Tolerar 1 hora de atraso
        )

        logger.info("✅ Scraping diário agendado com sucesso")

    async def shutdown(self) -> None:
        """Para o scheduler"""
        logger.info("🛑 Parando scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("✅ Scheduler parado")
