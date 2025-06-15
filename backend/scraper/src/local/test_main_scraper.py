#!/usr/bin/env python3
"""
Teste do scraper principal com critérios corretos
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_main_scraper():
    """Testa o scraper principal com critérios específicos"""

    print("🚀 Teste do Scraper Principal")
    print("=" * 40)
    print("📋 Critérios:")
    print("   📅 Data: 13/11/2024")
    print("   📋 Caderno: 3 - Judicial - 1ª Instância - Capital - Parte I")
    print('   🔍 Palavras: "RPV" e "pagamento pelo INSS"')
    print()

    scraper = DJEScraperAdapter()
    publications_found = 0

    try:
        # Inicializar
        await scraper.initialize()

        # Executar scraping
        print("🔍 Iniciando scraping...")

        async for publication in scraper.scrape_publications(
            search_terms=["RPV", "pagamento pelo INSS"], max_pages=2
        ):
            publications_found += 1
            print(f"\n📄 PUBLICAÇÃO {publications_found}:")
            print(f"   📅 Data Publicação: {publication.publication_date}")
            print(f"   📅 Data Disponibilização: {publication.availability_date}")
            print(f"   📋 Processo: {publication.process_number}")
            print(f"   👤 Autores: {', '.join(publication.authors)}")
            print(f"   ⚖️ Advogados: {len(publication.lawyers)} advogado(s)")
            print(
                f"   💰 Valor Bruto: {publication.gross_value.to_real() if publication.gross_value else 'N/A'}"
            )
            print(
                f"   💰 Valor Líquido: {publication.net_value.to_real() if publication.net_value else 'N/A'}"
            )
            print(f"   📝 Conteúdo: {publication.content[:200]}...")

            # Limitar para não sobrecarregar
            if publications_found >= 5:
                print("\n⚠️ Limitando a 5 publicações para teste")
                break

        return publications_found > 0

    except Exception as error:
        print(f"❌ Erro durante scraping: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    print("🎯 Teste do Scraper Principal com Critérios Específicos")
    print("💡 Usando data 13/11/2024 e termos específicos")
    print()

    success = asyncio.run(test_main_scraper())

    if success:
        print("\n🎉 TESTE PASSOU!")
        print("✅ Publicações encontradas e processadas")
    else:
        print("\n⚠️ TESTE FALHOU")
        print("❌ Nenhuma publicação encontrada ou erro no processamento")

    sys.exit(0 if success else 1)
