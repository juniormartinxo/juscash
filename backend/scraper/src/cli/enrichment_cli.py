"""
CLI para enriquecimento de processos com dados do e-SAJ
Permite testar a consulta individual de processos
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent))

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from application.services.process_enrichment_service import ProcessEnrichmentService
from infrastructure.logging.logger import setup_logger
from datetime import datetime
from decimal import Decimal

logger = setup_logger(__name__)


class EnrichmentCLI:
    """
    CLI para testar enriquecimento de processos
    """

    def __init__(self):
        # Mock do repository para testes
        self.publication_repository = None

    async def test_single_process(self, process_number: str) -> None:
        """
        Testa enriquecimento de um único processo
        """
        logger.info(f"🧪 Testando enriquecimento do processo: {process_number}")

        # Criar publicação mock para teste
        test_publication = self._create_mock_publication(process_number)

        async with ProcessEnrichmentService(
            self.publication_repository
        ) as enrichment_service:
            enriched_data = await enrichment_service.enrich_single_publication(
                test_publication
            )

            if enriched_data:
                logger.info("✅ Teste concluído com sucesso!")
                self._display_enriched_data(enriched_data)
            else:
                logger.error("❌ Falha no enriquecimento")

    async def test_multiple_processes(self, process_numbers: List[str]) -> None:
        """
        Testa enriquecimento de múltiplos processos
        """
        logger.info(
            f"🧪 Testando enriquecimento de {len(process_numbers)} processos..."
        )

        # Criar publicações mock para teste
        test_publications = [
            self._create_mock_publication(pn) for pn in process_numbers
        ]

        async with ProcessEnrichmentService(
            self.publication_repository
        ) as enrichment_service:
            enriched_data_list = await enrichment_service.enrich_publications(
                test_publications
            )

            logger.info(
                f"✅ Teste concluído: {len(enriched_data_list)}/{len(process_numbers)} processos enriquecidos"
            )

            for enriched_data in enriched_data_list:
                self._display_enriched_data(enriched_data)

    def _create_mock_publication(self, process_number: str) -> Publication:
        """
        Cria uma publicação mock para testes
        """
        return Publication(
            process_number=process_number,
            authors=["Autor Mock"],
            content=f"Conteúdo mock para processo {process_number}",
            publication_date=datetime.now(),
            availability_date=datetime.now(),
            gross_value=MonetaryValue.from_real(Decimal("1000.00")),
            interest_value=MonetaryValue.from_real(Decimal("100.00")),
            attorney_fees=MonetaryValue.from_real(Decimal("200.00")),
            lawyers=[Lawyer(name="Advogado Mock", oab="123456/SP")],
        )

    def _display_enriched_data(self, enriched_data: dict) -> None:
        """
        Exibe dados enriquecidos de forma organizada
        """
        print("\n" + "=" * 80)
        print(f"📋 DADOS ENRIQUECIDOS - PROCESSO: {enriched_data['process_number']}")
        print("=" * 80)

        # Dados consolidados
        consolidated = enriched_data.get("consolidated_data", {})

        print("\n📊 DADOS CONSOLIDADOS:")
        print(f"   📅 Data Publicação: {consolidated.get('publication_date', 'N/A')}")
        print(
            f"   📅 Data Disponibilidade: {consolidated.get('availability_date', 'N/A')}"
        )
        print(f"   💰 Valor Bruto: R$ {consolidated.get('gross_value', 0):,.2f}")
        print(f"   💰 Juros: R$ {consolidated.get('interest_value', 0):,.2f}")
        print(f"   💰 Honorários: R$ {consolidated.get('attorney_fees', 0):,.2f}")

        # Partes
        parties = consolidated.get("parties", {})
        print(f"\n👥 PARTES DO PROCESSO:")
        print(f"   Autores: {len(parties.get('authors', []))}")
        for i, author in enumerate(parties.get("authors", []), 1):
            print(f"     {i}. {author}")

        print(f"   Advogados: {len(parties.get('lawyers', []))}")
        for i, lawyer in enumerate(parties.get("lawyers", []), 1):
            if isinstance(lawyer, dict):
                print(
                    f"     {i}. {lawyer.get('name', 'N/A')} - {lawyer.get('oab', 'N/A')}"
                )
            else:
                print(f"     {i}. {lawyer}")

        # Fontes dos dados
        sources = consolidated.get("data_sources", {})
        print(f"\n🔍 FONTES DOS DADOS:")
        print(f"   DJE Disponível: {'✅' if sources.get('dje_available') else '❌'}")
        print(f"   e-SAJ Disponível: {'✅' if sources.get('esaj_available') else '❌'}")
        print(f"   Estratégia: {sources.get('consolidation_strategy', 'N/A')}")
        print(f"   Data Publicação: {sources.get('publication_date_source', 'N/A')}")
        print(
            f"   Data Disponibilidade: {sources.get('availability_date_source', 'N/A')}"
        )
        print(f"   Valores Monetários: {sources.get('monetary_values_source', 'N/A')}")
        print(f"   Partes: {sources.get('parties_source', 'N/A')}")

        # Dados brutos do e-SAJ (resumo)
        esaj_data = enriched_data.get("esaj_data", {})
        if esaj_data:
            print(f"\n🌐 DADOS e-SAJ (RESUMO):")
            print(f"   Timestamp: {esaj_data.get('extraction_timestamp', 'N/A')}")

            movements = esaj_data.get("movements", {})
            if movements:
                print(f"   Movimentações:")
                print(
                    f"     - Data Publicação: {movements.get('publication_date', 'N/A')}"
                )
                print(
                    f"     - Data Disponibilidade: {movements.get('availability_date', 'N/A')}"
                )

                homolog = movements.get("homologation_details")
                if homolog:
                    print(f"     - Detalhes Homologação: ✅ Disponível")
                    print(
                        f"       * Valor Bruto: R$ {homolog.get('gross_value', 0):,.2f}"
                    )
                    print(f"       * Juros: R$ {homolog.get('interest_value', 0):,.2f}")
                    print(
                        f"       * Honorários: R$ {homolog.get('attorney_fees', 0):,.2f}"
                    )

        print("\n" + "=" * 80)


async def main():
    """
    Função principal do CLI
    """
    cli = EnrichmentCLI()

    if len(sys.argv) < 2:
        print(
            "❌ Uso: python enrichment_cli.py <numero_processo> [numero_processo2] ..."
        )
        print("📋 Exemplo: python enrichment_cli.py 0009027-08.2024.8.26.0053")
        sys.exit(1)

    process_numbers = sys.argv[1:]

    logger.info(f"🚀 Iniciando teste de enriquecimento...")
    logger.info(f"📋 Processos para testar: {', '.join(process_numbers)}")

    try:
        if len(process_numbers) == 1:
            await cli.test_single_process(process_numbers[0])
        else:
            await cli.test_multiple_processes(process_numbers)
    except KeyboardInterrupt:
        logger.info("⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
