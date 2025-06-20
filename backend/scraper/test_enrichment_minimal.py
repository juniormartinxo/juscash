#!/usr/bin/env python3
"""
Teste mínimo de enriquecimento - apenas um processo
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append("src")

from infrastructure.web.esaj_process_scraper import ESAJProcessScraper
from infrastructure.logging.logger import setup_logger
from playwright.async_api import async_playwright

logger = setup_logger(__name__)


async def test_minimal():
    """
    Testa enriquecimento de um único processo
    """
    logger.info("🧪 TESTE MÍNIMO DE ENRIQUECIMENTO")
    logger.info("=" * 50)

    # Processo de teste
    process_number = "0009027-08.2024.8.26.0053"
    logger.info(f"📋 Processo: {process_number}")

    # Criar browser e scraper
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    scraper = ESAJProcessScraper(browser)

    try:
        logger.info("🔍 Buscando dados no e-SAJ...")
        data = await scraper.scrape_process(process_number)

        if data:
            logger.info("✅ Dados obtidos com sucesso!")

            # Mostrar valores monetários
            if data.get("movements", {}).get("homologation_details"):
                homolog = data["movements"]["homologation_details"]
                logger.info("\n💰 VALORES MONETÁRIOS:")
                logger.info(f"   Valor bruto: {homolog.get('gross_value', 'N/A')}")
                logger.info(f"   Juros: {homolog.get('interest_value', 'N/A')}")
                logger.info(f"   Honorários: {homolog.get('attorney_fees', 'N/A')}")

            # Mostrar advogados
            if data.get("parties", {}).get("lawyers"):
                lawyers = data["parties"]["lawyers"]
                logger.info(f"\n👨‍💼 ADVOGADOS ({len(lawyers)}):")
                for lawyer in lawyers[:3]:
                    logger.info(
                        f"   - {lawyer.get('name')} - OAB: {lawyer.get('oab', 'N/A')}"
                    )

            # Mostrar data de disponibilidade
            if data.get("movements", {}).get("availability_date"):
                logger.info(
                    f"\n📅 Data disponibilidade: {data['movements']['availability_date']}"
                )

        else:
            logger.warning("❌ Nenhum dado retornado")

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_minimal())
