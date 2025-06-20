#!/usr/bin/env python3
"""
Teste de enriquecimento em arquivo existente
"""

import asyncio
import json
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append("src")

from application.services.process_enrichment_service import ProcessEnrichmentService
from domain.entities.publication import Publication, MonetaryValue, Lawyer
from infrastructure.logging.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


async def enrich_existing_json():
    """
    Enriquece um arquivo JSON existente
    """
    logger.info("🧪 TESTE DE ENRIQUECIMENTO EM ARQUIVO EXISTENTE")
    logger.info("=" * 50)

    # Buscar um arquivo JSON recente
    json_dir = Path("reports/json")
    json_files = list(json_dir.glob("*.json"))

    if not json_files:
        logger.error("❌ Nenhum arquivo JSON encontrado!")
        return

    # Pegar o primeiro arquivo
    json_file = json_files[0]
    logger.info(f"📄 Arquivo selecionado: {json_file}")

    # Ler dados do arquivo
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"📋 Processo: {data.get('process_number')}")
    logger.info(f"💰 Valor bruto atual: {data.get('gross_value', 0)}")
    logger.info(f"👨‍💼 Advogados atuais: {len(data.get('lawyers', []))}")

    # Converter para entidade Publication
    publication = Publication(
        process_number=data.get("process_number"),
        publication_date=datetime.fromisoformat(data.get("publication_date")),
        availability_date=datetime.fromisoformat(data.get("availability_date")),
        authors=data.get("authors", []),
        lawyers=[
            Lawyer(name=lawyer.get("name", ""), oab=lawyer.get("oab", ""))
            for lawyer in data.get("lawyers", [])
        ],
        gross_value=MonetaryValue.from_real(
            data.get("gross_value", 0) / 100
        ),  # Converter de centavos
        interest_value=MonetaryValue.from_real(data.get("interest_value", 0) / 100),
        attorney_fees=MonetaryValue.from_real(data.get("attorney_fees", 0) / 100),
        content=data.get("content", ""),
    )

    logger.info("\n🔍 Iniciando enriquecimento...")

    try:
        async with ProcessEnrichmentService() as service:
            logger.info("✅ ProcessEnrichmentService inicializado")

            # Enriquecer
            enriched_data = await service.enrich_single_publication(publication)

            if enriched_data:
                logger.info("✅ Enriquecimento retornou dados!")

                # Mostrar dados e-SAJ
                esaj_data = enriched_data.get("esaj_data", {})
                if esaj_data:
                    logger.info("\n📊 DADOS E-SAJ:")

                    # Valores monetários
                    if esaj_data.get("movements", {}).get("homologation_details"):
                        homolog = esaj_data["movements"]["homologation_details"]
                        logger.info(
                            f"💰 Valor bruto e-SAJ: {homolog.get('gross_value', 'N/A')}"
                        )
                        logger.info(
                            f"💵 Juros e-SAJ: {homolog.get('interest_value', 'N/A')}"
                        )
                        logger.info(
                            f"💼 Honorários e-SAJ: {homolog.get('attorney_fees', 'N/A')}"
                        )

                    # Advogados
                    if esaj_data.get("parties", {}).get("lawyers"):
                        lawyers = esaj_data["parties"]["lawyers"]
                        logger.info(f"\n👨‍💼 ADVOGADOS E-SAJ ({len(lawyers)}):")
                        for lawyer in lawyers[:3]:  # Mostrar apenas 3 primeiros
                            logger.info(
                                f"   - {lawyer.get('name')} - OAB: {lawyer.get('oab', 'N/A')}"
                            )

                    # Data disponibilidade
                    if esaj_data.get("movements", {}).get("availability_date"):
                        logger.info(
                            f"\n📅 Data disponibilidade e-SAJ: {esaj_data['movements']['availability_date']}"
                        )

                # Dados consolidados
                consolidated = enriched_data.get("consolidated_data", {})
                logger.info("\n📊 DADOS CONSOLIDADOS (DJE + e-SAJ):")
                logger.info(
                    f"💰 Valor bruto final: {consolidated.get('gross_value', 'N/A')}"
                )
                logger.info(
                    f"👨‍💼 Total advogados: {len(consolidated.get('lawyers', []))}"
                )

                # Salvar arquivo enriquecido
                enriched_file = json_file.with_stem(f"{json_file.stem}_ENRICHED")
                with open(enriched_file, "w", encoding="utf-8") as f:
                    json.dump(
                        enriched_data, f, indent=2, ensure_ascii=False, default=str
                    )

                logger.info(f"\n💾 Arquivo enriquecido salvo: {enriched_file}")

            else:
                logger.warning("❌ Enriquecimento retornou None")

    except Exception as e:
        logger.error(f"❌ Erro durante enriquecimento: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(enrich_existing_json())
