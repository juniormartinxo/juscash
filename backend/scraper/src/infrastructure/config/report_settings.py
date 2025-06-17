"""
Configurações para diretórios de relatórios
"""

import os
from pathlib import Path
from pydantic import BaseSettings, Field


class ReportSettings(BaseSettings):
    """Configurações dos diretórios de relatórios"""

    # Diretório base para relatórios
    base_dir: Path = Field(default=Path("/app/reports"), env="REPORTS_BASE_DIR")

    # Subdiretórios específicos
    json_dir: Path = Field(default=None)
    log_dir: Path = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Configurar subdiretórios
        self.json_dir = self.base_dir / "json"
        self.log_dir = self.base_dir / "log"

        # Criar diretórios se não existirem
        for dir_path in [self.base_dir, self.json_dir, self.log_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"


def get_report_settings() -> ReportSettings:
    """Retorna uma instância das configurações de relatórios"""
    return ReportSettings()
