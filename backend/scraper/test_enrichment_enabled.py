#!/usr/bin/env python3
"""
Teste para verificar se o enriquecimento está habilitado
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.append("src")

from application.services.process_enrichment_service import ProcessEnrichmentService
from domain.entities.publication import Publication, MonetaryValue
from infrastructure.logging.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


async def test_enrichment():
    """
    Testa se o enriquecimento está funcionando
    """
    logger.info("🧪 TESTE DE ENRIQUECIMENTO")
    logger.info("=" * 50)

    # Verificar configuração
    enable_enrichment = os.getenv("ENABLE_ENRICHMENT", "true").lower() == "true"
    logger.info(f"📊 ENABLE_ENRICHMENT = {enable_enrichment}")

    if not enable_enrichment:
        logger.warning("⚠️ Enriquecimento está DESABILITADO por configuração!")
        return

    # Criar publicação de teste
    publication = Publication(
        process_number="0009027-08.2024.8.26.0053",
        publication_date=datetime.now(),
        availability_date=datetime.now(),
        authors=["Teste"],
        lawyers=[],
        gross_value=MonetaryValue.from_real(0),
        interest_value=MonetaryValue.from_real(0),
        attorney_fees=MonetaryValue.from_real(0),
        content="Teste de enriquecimento",
    )

    logger.info(f"📋 Testando processo: {publication.process_number}")

    try:
        logger.info("🔍 Iniciando ProcessEnrichmentService...")
        async with ProcessEnrichmentService() as service:
            logger.info("✅ Service inicializado com sucesso")

            # Testar enriquecimento
            result = await service.enrich_single_publication(publication)

            if result:
                logger.info("✅ Enriquecimento retornou dados!")
                esaj_data = result.get("esaj_data", {})
                if esaj_data:
                    logger.info("✅ Dados e-SAJ presentes")
                else:
                    logger.warning("⚠️ Sem dados e-SAJ")
            else:
                logger.warning("❌ Enriquecimento retornou None")

    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enrichment())
