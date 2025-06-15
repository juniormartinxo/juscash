#!/usr/bin/env python3
"""
Teste rápido do scraper
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter


async def test_quick():
    """Teste rápido"""

    print("🚀 Teste Rápido do Scraper")
    print("=" * 30)

    scraper = DJEScraperAdapter()
    count = 0

    try:
        await scraper.initialize()

        async for publication in scraper.scrape_publications(
            search_terms=["RPV"], max_pages=1
        ):
            count += 1
            print(f"✅ Publicação {count}: {publication.process_number}")

            if count >= 3:  # Limitar a 3
                break

        print(f"\n🎉 Encontradas {count} publicações!")
        return count > 0

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    success = asyncio.run(test_quick())
    print("✅ SUCESSO!" if success else "❌ FALHOU")
