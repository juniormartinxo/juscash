"""
Sistema de logging configurável
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(name: str):
    """
    Configura o sistema de logging usando Loguru
    """

    # Remover handler padrão
    logger.remove()

    # Configurar formato de log
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Handler para console
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Handler para arquivo (se configurado)
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "scraper_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Log de erros separado
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    return logger
