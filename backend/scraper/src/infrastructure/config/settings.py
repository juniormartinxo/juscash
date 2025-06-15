"""
Configurações da aplicação
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path


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


class LogSettings(BaseSettings):
    """Configurações de logging"""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    dir: Path = Field(default=Path("./logs"), env="LOG_DIR")
    rotation_days: int = Field(default=7, env="LOG_ROTATION_DAYS")
    max_size_mb: int = Field(default=10, env="LOG_MAX_SIZE_MB")


class Settings(BaseSettings):
    """Configurações principais"""

    environment: str = Field(default="development", env="WORK_MODE")

    browser: BrowserSettings = BrowserSettings()
    scraper: ScraperSettings = ScraperSettings()
    api: ApiSettings = ApiSettings()
    logging: LogSettings = LogSettings()

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


def get_settings() -> Settings:
    """Factory para obter configurações"""
    return Settings()
