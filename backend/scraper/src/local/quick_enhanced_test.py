#!/usr/bin/env python3
"""
Teste rápido do parser aprimorado
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser


async def quick_test():
    """Teste rápido"""

    print("🧪 Teste Rápido do Parser Aprimorado")

    # Conteúdo simples de teste
    content = """
    Processo 0013168-70.2024.8.26.0053
    - MARIA DA SILVA - Vistos
    Execução de RPV no valor de R$ 15.000,00.
    """

    parser = EnhancedDJEContentParser()

    try:
        publications = await parser.parse_multiple_publications_enhanced(
            content, "test.pdf"
        )

        print(f"📊 Encontradas: {len(publications)} publicações")

        for pub in publications:
            print(f"✅ Processo: {pub.process_number}")
            print(f"✅ Autores: {', '.join(pub.authors)}")
            print(f"✅ Método: {pub.extraction_metadata.get('extraction_method')}")

        return len(publications) > 0

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print("✅ SUCESSO!" if success else "❌ FALHOU")
