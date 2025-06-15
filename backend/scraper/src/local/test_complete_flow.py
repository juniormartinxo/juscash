#!/usr/bin/env python3
"""
Teste do fluxo completo: encontrar links, baixar PDFs, processar conteúdo
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_complete_pdf_flow():
    """Testa o fluxo completo com download real de PDFs"""

    print("🧪 Teste do Fluxo Completo com PDFs")
    print("=" * 50)
    print("💡 Vai baixar e processar PDFs reais!")
    print()

    scraper = DJEScraperAdapter()
    publications_found = 0

    try:
        # Inicializar
        await scraper.initialize()

        print("🔍 Executando scraping completo...")
        search_terms = ["INSS"]
        max_pages = 1  # Limitar a 1 página para teste

        # Usar o método principal do scraper
        async for publication in scraper.scrape_publications(search_terms, max_pages):
            publications_found += 1

            print(f"\n📄 PUBLICAÇÃO {publications_found}:")
            print(f"   🔢 Processo: {publication.process_number}")
            print(f"   📅 Data: {publication.publication_date}")
            print(
                f"   👥 Autores: {len(publication.authors)} ({', '.join(publication.authors[:2])}...)"
            )
            print(f"   ⚖️ Advogados: {len(publication.lawyers)}")
            print(
                f"   💰 Valores: {len([v for v in [publication.gross_value, publication.net_value, publication.interest_value, publication.attorney_fees] if v])}"
            )
            print(f"   📝 Conteúdo: {len(publication.content)} chars")

            # Mostrar alguns valores se existirem
            if publication.interest_value:
                print(f"   💵 Juros: R$ {publication.interest_value.amount}")
            if publication.attorney_fees:
                print(f"   💼 Honorários: R$ {publication.attorney_fees.amount}")

            # Limitar teste a 3 publicações
            if publications_found >= 3:
                print(f"\n⚠️ Limitando teste a {publications_found} publicações")
                break

        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   ✅ {publications_found} publicações processadas com sucesso")

        return publications_found > 0

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    print("🚀 Teste Completo do Fluxo PDF")
    print("💡 Este teste vai:")
    print("   1. Acessar a consulta avançada")
    print("   2. Encontrar elementos tr.ementaClass")
    print("   3. Extrair URLs dinâmicas dos PDFs")
    print("   4. Baixar PDFs reais")
    print("   5. Processar conteúdo com o parser aprimorado")
    print("   6. Extrair publicações estruturadas")
    print()

    success = asyncio.run(test_complete_pdf_flow())

    if success:
        print("\n🎉 TESTE COMPLETO PASSOU!")
        print("✅ O fluxo de PDFs dinâmicos está funcionando perfeitamente")
        print("💡 Agora você pode executar: py scraper_cli.py run")
    else:
        print("\n❌ TESTE FALHOU")
        print("⚠️ Verifique os logs para mais detalhes")

    sys.exit(0 if success else 1)
