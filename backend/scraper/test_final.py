#!/usr/bin/env python3
"""
Teste final para verificar se o scraper pode ser executado.
"""
import asyncio
import os
from datetime import datetime

# Configurar variáveis de ambiente para teste
os.environ['ENVIRONMENT'] = 'test'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['POSTGRES_URL_ASYNC'] = 'postgresql+asyncpg://juscash_user:juscash_pass@localhost:5432/juscash_db'
os.environ['REDIS_URL'] = 'redis://localhost:6388'

from src.main import main as scraper_main
from src.shared.logger import get_logger

logger = get_logger(__name__)


async def test_scraper():
    """Testa a execução do scraper."""
    logger.info("=== Teste Final do Scraper ===")
    logger.info(f"Horário: {datetime.now()}")
    
    try:
        # Tentar executar o scraper
        logger.info("Iniciando scraper...")
        await scraper_main()
        logger.info("✅ Scraper executado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao executar scraper: {str(e)}")
        logger.exception("Detalhes do erro:")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    exit(0 if success else 1)