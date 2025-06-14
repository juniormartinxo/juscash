"""
Sistema de configuração dinâmica para o scraper
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel, Field

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ScrapingConfig(BaseModel):
    """Configuração dinâmica do scraping"""

    # Configurações de busca
    search_terms: List[str] = Field(default=["aposentadoria", "benefício"])
    max_pages: int = Field(default=20, ge=1, le=100)
    max_publications_per_page: int = Field(default=50, ge=1, le=200)

    # Configurações de retry
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay_seconds: float = Field(default=5.0, ge=1.0, le=60.0)

    # Configurações de timeout
    page_timeout_seconds: int = Field(default=30, ge=5, le=120)
    element_timeout_seconds: int = Field(default=10, ge=1, le=60)

    # Configurações de qualidade
    min_confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    min_content_length: int = Field(default=50, ge=10, le=1000)

    # Configurações de rate limiting
    delay_between_pages_seconds: float = Field(default=2.0, ge=0.5, le=10.0)
    delay_between_requests_seconds: float = Field(default=1.0, ge=0.1, le=5.0)

    # Configurações de seletores CSS (podem ser atualizados dinamicamente)
    selectors: Dict[str, str] = Field(
        default={
            "publications": ".publicacao, .conteudo, .texto",
            "next_page": 'a:text("Próxima"), a:text(">"), .pagination .next',
            "caderno_link": 'a[href*="cdCaderno=3"]',
            "search_input": 'input[name="search"], input[type="search"]',
            "date_input": 'input[type="date"], input[name="data"]',
        }
    )

    # Configurações de backup
    enable_backup: bool = Field(default=True)
    backup_retention_days: int = Field(default=30, ge=1, le=365)

    # Configurações de debugging
    enable_debug: bool = Field(default=False)
    debug_screenshot_on_error: bool = Field(default=True)
    debug_save_html: bool = Field(default=False)


class DynamicConfigManager:
    """
    Gerenciador de configuração dinâmica
    """

    def __init__(self, config_file: str = "./config/scraping_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)

        self._config: Optional[ScrapingConfig] = None
        self._config_watchers: List[Callable[[ScrapingConfig], None]] = []
        self._last_modified: Optional[float] = None

        # Carregar configuração inicial
        self._load_config()

    def _load_config(self) -> None:
        """Carrega configuração do arquivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                self._config = ScrapingConfig(**config_data)
                self._last_modified = self.config_file.stat().st_mtime
                logger.info(f"⚙️  Configuração carregada: {self.config_file}")
            else:
                # Criar configuração padrão
                self._config = ScrapingConfig()
                self._save_config()
                logger.info("⚙️  Configuração padrão criada")

        except Exception as error:
            logger.error(f"❌ Erro ao carregar configuração: {error}")
            self._config = ScrapingConfig()  # Fallback para configuração padrão

    def _save_config(self) -> None:
        """Salva configuração no arquivo"""
        try:
            config_data = self._config.dict()

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self._last_modified = self.config_file.stat().st_mtime
            logger.debug(f"⚙️  Configuração salva: {self.config_file}")

        except Exception as error:
            logger.error(f"❌ Erro ao salvar configuração: {error}")

    def get_config(self) -> ScrapingConfig:
        """Obtém configuração atual"""
        return self._config

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Atualiza configuração com novos valores

        Args:
            updates: Dicionário com atualizações

        Returns:
            True se atualizada com sucesso
        """
        try:
            # Aplicar atualizações
            current_data = self._config.dict()
            current_data.update(updates)

            # Validar nova configuração
            new_config = ScrapingConfig(**current_data)

            # Salvar se válida
            old_config = self._config
            self._config = new_config
            self._save_config()

            # Notificar watchers
            self._notify_watchers(old_config, new_config)

            logger.info(f"⚙️  Configuração atualizada: {list(updates.keys())}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro ao atualizar configuração: {error}")
            return False

    def add_config_watcher(self, callback: Callable[[ScrapingConfig], None]) -> None:
        """Adiciona callback para mudanças de configuração"""
        self._config_watchers.append(callback)

    def _notify_watchers(
        self, old_config: ScrapingConfig, new_config: ScrapingConfig
    ) -> None:
        """Notifica watchers sobre mudanças"""
        for callback in self._config_watchers:
            try:
                callback(new_config)
            except Exception as error:
                logger.error(f"❌ Erro em watcher de configuração: {error}")

    async def watch_config_file(self, check_interval: float = 10.0) -> None:
        """
        Monitora arquivo de configuração por mudanças

        Args:
            check_interval: Intervalo de verificação em segundos
        """
        logger.info(f"👁️  Monitorando configuração: {self.config_file}")

        while True:
            try:
                await asyncio.sleep(check_interval)

                if self.config_file.exists():
                    current_modified = self.config_file.stat().st_mtime

                    if current_modified != self._last_modified:
                        logger.info(
                            "🔄 Arquivo de configuração modificado, recarregando..."
                        )
                        old_config = self._config
                        self._load_config()

                        if self._config != old_config:
                            self._notify_watchers(old_config, self._config)

            except Exception as error:
                logger.error(f"❌ Erro no monitoramento de configuração: {error}")

    def reset_to_defaults(self) -> bool:
        """Reseta configuração para padrões"""
        try:
            old_config = self._config
            self._config = ScrapingConfig()
            self._save_config()

            self._notify_watchers(old_config, self._config)

            logger.info("⚙️  Configuração resetada para padrões")
            return True

        except Exception as error:
            logger.error(f"❌ Erro ao resetar configuração: {error}")
            return False

    def export_config(self, export_path: str) -> bool:
        """Exporta configuração atual"""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "config": self._config.dict(),
                "metadata": {"scraper_version": "1.0.0", "config_version": "1.0"},
            }

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"📤 Configuração exportada: {export_path}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro ao exportar configuração: {error}")
            return False

    def import_config(self, import_path: str) -> bool:
        """Importa configuração de arquivo"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            # Validar e aplicar configuração importada
            config_data = import_data.get("config", import_data)
            new_config = ScrapingConfig(**config_data)

            old_config = self._config
            self._config = new_config
            self._save_config()

            self._notify_watchers(old_config, new_config)

            logger.info(f"📥 Configuração importada: {import_path}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro ao importar configuração: {error}")
            return False
