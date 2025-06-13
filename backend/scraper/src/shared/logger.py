import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional
from loguru._logger import Logger

from src.config.settings import get_settings

# Obter configurações
settings = get_settings()


def setup_logging(
    level: Optional[str] = None,
    log_dir: Optional[str] = None,
    rotation_days: Optional[int] = None,
    max_size_mb: Optional[int] = None,
) -> None:
    """
    Configura o sistema de logging da aplicação.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para arquivos de log
        rotation_days: Dias para rotação de logs
        max_size_mb: Tamanho máximo do arquivo em MB
    """
    # Usar configurações do settings se não fornecidas
    level = level or settings.logging.level
    log_dir = log_dir or settings.logging.dir
    rotation_days = rotation_days or settings.logging.rotation_days
    max_size_mb = max_size_mb or settings.logging.max_size_mb

    # Remover handlers padrão
    logger.remove()

    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configurar formato personalizado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Handler para console (stdout)
    logger.add(
        sys.stdout,
        format=log_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Handler para arquivo geral
    logger.add(
        log_path / "scraper.log",
        format=log_format,
        level=level,
        rotation=f"{max_size_mb} MB",
        retention=f"{rotation_days} days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Handler para erros (arquivo separado)
    logger.add(
        log_path / "errors.log",
        format=log_format,
        level="ERROR",
        rotation=f"{max_size_mb} MB",
        retention=f"{rotation_days} days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Handler para scraping específico
    logger.add(
        log_path / "scraping.log",
        format=log_format,
        level="INFO",
        rotation="1 day",
        retention=f"{rotation_days} days",
        compression="zip",
        filter=lambda record: "scraping" in record["name"].lower(),
    )

    logger.info(
        f"Sistema de logging configurado - Nível: {level}, Diretório: {log_dir}"
    )


def get_logger(name: str) -> "Logger":
    """
    Retorna logger configurado para um módulo específico.

    Args:
        name: Nome do módulo/classe

    Returns:
        Instância do logger configurada
    """
    return logger.bind(name=name)


# Configurar logging automaticamente na importação
if not logger._core.handlers:
    setup_logging()
