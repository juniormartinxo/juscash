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

            # Verificar se o diretório é gravável
            if not os.access(dir_path, os.W_OK):
                try:
                    # Tentar alterar permissões se necessário
                    import stat

                    dir_path.chmod(
                        stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH
                    )
                except PermissionError:
                    print(f"⚠️ Aviso: Sem permissão de escrita em {dir_path}")

        return self

    class Config:
        env_file = ".env"


def get_report_settings() -> ReportSettings:
    """Retorna uma instância das configurações de relatórios"""
    return ReportSettings()
