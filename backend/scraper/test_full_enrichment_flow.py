#!/usr/bin/env python3
"""
Teste completo do fluxo de scraping + enriquecimento
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.append("src")

from infrastructure.logging.logger import setup_logger
from application.services.scraping_orchestrator import ScrapingOrchestrator
from application.services.process_enrichment_service import ProcessEnrichmentService
from application.usecases.extract_publications import ExtractPublicationsUseCase
from application.usecases.save_publications_to_files import (
    SavePublicationsToFilesUseCase,
)
from shared.container import Container
from domain.entities.publication import MonetaryValue, Lawyer

logger = setup_logger(__name__)


async def test_full_flow():
    """
    Testa o fluxo completo: scraping + enriquecimento + salvamento
    """
    logger.info("🧪 TESTE COMPLETO: SCRAPING + ENRIQUECIMENTO")
    logger.info("=" * 60)

    # Data de teste (hoje)
    test_date = datetime.now().strftime("%d/%m/%Y")
    logger.info(f"📅 Data de teste: {test_date}")

    # Inicializar container
    container = Container(use_optimized_scraper=False)

    try:
        orchestrator = ScrapingOrchestrator(container)

        # Configurar scraper para data específica
        if hasattr(container.web_scraper, "_target_date"):
            container.web_scraper._target_date = test_date
        else:
            setattr(container.web_scraper, "_target_date", test_date)

        # 1. EXTRAIR PUBLICAÇÕES
        logger.info("\n📄 FASE 1: EXTRAÇÃO DAS PUBLICAÇÕES")
        logger.info("-" * 40)

        extract_usecase = ExtractPublicationsUseCase(container.web_scraper)
        publications = []
        search_terms = ["RPV", "pagamento pelo INSS"]

        async for publication in extract_usecase.execute(search_terms, max_pages=1):
            publications.append(publication)
            logger.info(f"   ✅ Extraída: {publication.process_number}")

            # Limitar a 3 publicações para teste rápido
            if len(publications) >= 3:
                break

        logger.info(f"📊 Total extraído: {len(publications)} publicações")

        if not publications:
            logger.warning("⚠️ Nenhuma publicação encontrada!")
            return

        # 2. ENRIQUECER PUBLICAÇÕES
        logger.info("\n🔍 FASE 2: ENRIQUECIMENTO COM E-SAJ")
        logger.info("-" * 40)

        enriched_mapping = {}
        enrichment_stats = {"success": 0, "failed": 0}

        async with ProcessEnrichmentService() as enrichment_service:
            logger.info("✅ ProcessEnrichmentService inicializado")

            enriched_data_list = await enrichment_service.enrich_publications(
                publications
            )

            for enriched_data in enriched_data_list:
                if enriched_data and enriched_data.get("esaj_data"):
                    process_number = enriched_data.get("process_number")
                    enriched_mapping[process_number] = enriched_data
                    enrichment_stats["success"] += 1

                    # Mostrar alguns dados enriquecidos
                    esaj_data = enriched_data["esaj_data"]
                    logger.info(f"\n   ✅ Enriquecido: {process_number}")

                    if (
                        esaj_data.get("movements", {})
                        .get("homologation_details", {})
                        .get("gross_value")
                    ):
                        logger.info(
                            f"      💰 Valor e-SAJ: {esaj_data['movements']['homologation_details']['gross_value']}"
                        )

                    if esaj_data.get("parties", {}).get("lawyers"):
                        logger.info(
                            f"      👨‍💼 Advogados e-SAJ: {len(esaj_data['parties']['lawyers'])}"
                        )
                else:
                    enrichment_stats["failed"] += 1

        logger.info(f"\n📊 Estatísticas de enriquecimento:")
        logger.info(f"   ✅ Sucesso: {enrichment_stats['success']}")
        logger.info(f"   ❌ Falha: {enrichment_stats['failed']}")

        # 3. ATUALIZAR PUBLICAÇÕES COM DADOS ENRIQUECIDOS
        logger.info("\n📝 FASE 3: ATUALIZAÇÃO DAS PUBLICAÇÕES")
        logger.info("-" * 40)

        for publication in publications:
            if publication.process_number in enriched_mapping:
                enriched_data = enriched_mapping[publication.process_number]
                esaj_data = enriched_data.get("esaj_data", {})

                # Atualizar valores monetários
                if esaj_data.get("movements", {}).get("homologation_details"):
                    homolog = esaj_data["movements"]["homologation_details"]

                    if homolog.get("gross_value"):
                        try:
                            value_str = (
                                homolog["gross_value"]
                                .replace("R$", "")
                                .replace(".", "")
                                .replace(",", ".")
                                .strip()
                            )
                            old_value = (
                                publication.gross_value.to_real()
                                if publication.gross_value
                                else 0
                            )
                            publication.gross_value = MonetaryValue.from_real(
                                float(value_str)
                            )
                            new_value = publication.gross_value.to_real()
                            logger.info(
                                f"   💰 {publication.process_number}: R$ {old_value:,.2f} → R$ {new_value:,.2f}"
                            )
                        except:
                            pass

                # Atualizar advogados
                if esaj_data.get("parties", {}).get("lawyers"):
                    old_count = len(publication.lawyers)
                    publication.lawyers = [
                        Lawyer(name=lawyer.get("name", ""), oab=lawyer.get("oab", ""))
                        for lawyer in esaj_data["parties"]["lawyers"]
                    ]
                    new_count = len(publication.lawyers)
                    logger.info(
                        f"   👨‍💼 {publication.process_number}: {old_count} → {new_count} advogados"
                    )

        # 4. SALVAR PUBLICAÇÕES ENRIQUECIDAS
        logger.info("\n💾 FASE 4: SALVAMENTO DAS PUBLICAÇÕES")
        logger.info("-" * 40)

        save_usecase = SavePublicationsToFilesUseCase()
        save_stats = await save_usecase.execute(publications)

        logger.info(f"📊 Estatísticas de salvamento:")
        logger.info(f"   ✅ Salvas: {save_stats['saved']}")
        logger.info(f"   ❌ Falhas: {save_stats['failed']}")

        # Verificar arquivos salvos
        json_dir = Path("reports/json")
        json_files = list(json_dir.glob("*.json"))
        logger.info(f"\n📁 Arquivos JSON em {json_dir}: {len(json_files)}")

        if json_files:
            # Verificar conteúdo do primeiro arquivo
            with open(json_files[0], "r") as f:
                data = json.load(f)

            logger.info(f"\n🔎 Verificando arquivo: {json_files[0].name}")
            logger.info(f"   Processo: {data.get('process_number')}")
            logger.info(f"   Valor bruto: {data.get('gross_value', 0)}")
            logger.info(f"   Advogados: {len(data.get('lawyers', []))}")

            if data.get("lawyers"):
                logger.info(
                    f"   Primeiro advogado: {data['lawyers'][0].get('name')} - OAB: {data['lawyers'][0].get('oab', 'N/A')}"
                )

        logger.info("\n✅ TESTE COMPLETO FINALIZADO!")

    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await container.cleanup()


if __name__ == "__main__":
    # Parar o monitor temporariamente
    import subprocess

    logger.info("⏸️  Parando monitor temporariamente...")
    subprocess.run(["supervisorctl", "stop", "monitoring_service"], capture_output=True)

    # Executar teste
    asyncio.run(test_full_flow())

    # Reiniciar monitor
    logger.info("▶️  Reiniciando monitor...")
    subprocess.run(
        ["supervisorctl", "start", "monitoring_service"], capture_output=True
    )
