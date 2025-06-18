"""
Configurações para diretórios de relatórios
"""

import os
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from typing import Optional


class ReportSettings(BaseSettings):
    """Configurações dos diretórios de relatórios"""

    # Diretório base para relatórios
    base_dir: Path = Field(default=Path("/app/reports"), env="REPORTS_BASE_DIR")

    # Subdiretórios específicos - serão calculados automaticamente
    json_dir: Optional[Path] = Field(default=None, exclude=True)
    log_dir: Optional[Path] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def setup_directories(self):
        """Configura subdiretórios e cria se necessário"""
        # Configurar subdiretórios
        self.json_dir = self.base_dir / "json"
        self.log_dir = self.base_dir / "log"

        for dir_path in [self.base_dir, self.json_dir, self.log_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        return self

    class Config:
        env_file = ".env"


def get_report_settings() -> ReportSettings:
    """Retorna uma instância das configurações de relatórios"""
    return ReportSettings()
