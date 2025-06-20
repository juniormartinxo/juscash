"""
Configurações da aplicação
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

from .report_settings import ReportSettings


class BrowserSettings(BaseSettings):
    """Configurações do browser"""

    headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="BROWSER_USER_AGENT",
    )


class ScraperSettings(BaseSettings):
    """Configurações do scraper"""

    target_url: str = Field(
        default="https://esaj.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada",
        env="SCRAPER_TARGET_URL",
    )
    max_retries: int = Field(default=3, env="SCRAPER_MAX_RETRIES")
    retry_delay: int = Field(default=5, env="SCRAPER_RETRY_DELAY")
    max_pages: int = Field(default=20, env="SCRAPER_MAX_PAGES")
    search_terms: List[str] = Field(
        default=["RPV", "pagamento pelo INSS"], env="SCRAPER_SEARCH_TERMS"
    )


class ApiSettings(BaseSettings):
    """Configurações da API"""

    base_url: str = Field(default="http://juscash-api:8000", env="API_BASE_URL")
    scraper_api_key: str = Field(default="", env="SCRAPER_API_KEY")
    timeout: int = Field(default=30, env="API_TIMEOUT")


class RedisSettings:
    """Configurações do Redis"""

    def __init__(self):
        import os

        self.host = os.getenv("REDIS_HOST", "juscash-redis")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.password = os.getenv("REDIS_PASSWORD", "")
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.queue_name = os.getenv("REDIS_QUEUE_NAME", "publications_queue")
        self.max_retries = int(os.getenv("REDIS_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("REDIS_RETRY_DELAY", "60"))
        self.batch_size = int(os.getenv("REDIS_BATCH_SIZE", "10"))
        self.worker_timeout = int(os.getenv("REDIS_WORKER_TIMEOUT", "300"))

        # Add redis_url property
        self.url = os.getenv("REDIS_URL", f"redis://{self.host}:{self.port}/{self.db}")
        if self.password:
            self.url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


class LogSettings(BaseSettings):
    """Configurações de logging"""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    dir: Path = Field(default=Path("./logs"), env="LOG_DIR")
    rotation_days: int = Field(default=7, env="LOG_ROTATION_DAYS")
    max_size_mb: int = Field(default=10, env="LOG_MAX_SIZE_MB")


class SchedulerSettings(BaseSettings):
    """Configurações do scheduler"""

    # Horários de execução (duas vezes por dia)
    morning_execution_hour: int = Field(default=6, env="SCHEDULER_MORNING_HOUR")
    morning_execution_minute: int = Field(default=0, env="SCHEDULER_MORNING_MINUTE")
    afternoon_execution_hour: int = Field(default=14, env="SCHEDULER_AFTERNOON_HOUR")
    afternoon_execution_minute: int = Field(default=0, env="SCHEDULER_AFTERNOON_MINUTE")
    start_date: str = Field(default="2025-01-21", env="SCHEDULER_START_DATE")

    # Compatibilidade com configuração antiga
    daily_execution_hour: int = Field(default=6, env="SCHEDULER_DAILY_HOUR")
    daily_execution_minute: int = Field(default=0, env="SCHEDULER_DAILY_MINUTE")


class Settings(BaseSettings):
    """Configurações principais"""

    environment: str = Field(default="development", env="WORK_MODE")

    browser: BrowserSettings = BrowserSettings()
    scraper: ScraperSettings = ScraperSettings()
    api: ApiSettings = ApiSettings()
    redis: RedisSettings = RedisSettings()
    logging: LogSettings = LogSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    reports: ReportSettings = ReportSettings()

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}

    @property
    def redis_url(self) -> str:
        """Get Redis URL from redis settings"""
        return self.redis.url


def get_settings() -> Settings:
    """Factory para obter configurações"""
    return Settings()
