#!/usr/bin/env python3
"""
Debug do problema de enriquecimento
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append("src")

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_imports():
    """
    Testa se todos os imports estão funcionando
    """
    logger.info("🧪 TESTE DE IMPORTS")
    logger.info("=" * 50)

    try:
        logger.info("1. Importando ProcessEnrichmentService...")
        from application.services.process_enrichment_service import (
            ProcessEnrichmentService,
        )

        logger.info("✅ ProcessEnrichmentService importado")
    except Exception as e:
        logger.error(f"❌ Erro ao importar ProcessEnrichmentService: {e}")
        return

    try:
        logger.info("2. Importando ESAJProcessScraper...")
        from infrastructure.web.esaj_process_scraper import ESAJProcessScraper

        logger.info("✅ ESAJProcessScraper importado")
    except Exception as e:
        logger.error(f"❌ Erro ao importar ESAJProcessScraper: {e}")
        return

    try:
        logger.info("3. Testando Playwright...")
        from playwright.async_api import async_playwright

        logger.info("✅ Playwright importado")

        # Testar se consegue inicializar
        playwright = await async_playwright().start()
        logger.info("✅ Playwright inicializado")
        browser = await playwright.chromium.launch(headless=True)
        logger.info("✅ Browser criado")
        await browser.close()
        logger.info("✅ Browser fechado")
    except Exception as e:
        logger.error(f"❌ Erro com Playwright: {e}")
        return

    logger.info("\n✅ TODOS OS COMPONENTES ESTÃO FUNCIONANDO!")


if __name__ == "__main__":
    asyncio.run(test_imports())
