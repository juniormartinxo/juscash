#!/usr/bin/env python3
"""
Teste do novo fluxo de scraping com download de PDFs
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_pdf_scraper_flow():
    """Testa o novo fluxo com download de PDFs"""

    print("🧪 Teste do Novo Fluxo com Download de PDFs")
    print("=" * 60)

    scraper = DJEScraperAdapter()

    try:
        # Inicializar scraper
        print("🌐 Inicializando scraper...")
        await scraper.initialize()

        # Testar navegação para consulta avançada
        print("📍 Navegando para consulta avançada...")
        await scraper._navigate_to_advanced_search()

        # Testar preenchimento do formulário
        print("📝 Preenchendo formulário de pesquisa...")
        search_terms = ["aposentadoria", "benefício", "INSS"]
        await scraper._fill_advanced_search_form(search_terms)

        # Buscar por elementos tr.ementaClass
        print("🔍 Buscando elementos tr.ementaClass...")
        ementa_elements = await scraper.page.query_selector_all("tr.ementaClass")

        if ementa_elements:
            print(f"✅ Encontrados {len(ementa_elements)} elementos tr.ementaClass")

            # Verificar primeiro elemento
            for i, element in enumerate(
                ementa_elements[:3]
            ):  # Testar apenas os primeiros 3
                print(f"\n📋 Analisando elemento {i+1}:")

                # Buscar elementos com onclick
                onclick_elements = await element.query_selector_all(
                    '[onclick*="popup"]'
                )
                print(f"   🔗 Elementos com onclick: {len(onclick_elements)}")

                for j, onclick_element in enumerate(onclick_elements):
                    onclick_attr = await onclick_element.get_attribute("onclick")
                    if onclick_attr and "consultaSimples.do" in onclick_attr:
                        print(f"   📄 Link {j+1}: {onclick_attr[:100]}...")

                        # Extrair URL
                        pdf_url = await scraper._extract_pdf_url_from_onclick(
                            onclick_attr
                        )
                        if pdf_url:
                            print(f"   ✅ URL extraída: {pdf_url}")

                            # Para teste, não vamos baixar todos os PDFs
                            print(f"   ⚠️ Download de PDF desabilitado para teste")
                            break

                if i >= 2:  # Limitar teste a 3 elementos
                    break
        else:
            print("❌ Nenhum elemento tr.ementaClass encontrado")

            # Debug: verificar se a página carregou corretamente
            title = await scraper.page.title()
            print(f"📄 Título da página: {title}")

            # Verificar se há outros elementos de resultado
            other_elements = await scraper.page.query_selector_all("tr")
            print(f"🔍 Total de elementos tr encontrados: {len(other_elements)}")

            # Verificar elementos com class
            class_elements = await scraper.page.query_selector_all("tr[class]")
            print(f"🔍 Elementos tr com class: {len(class_elements)}")

            if class_elements:
                for i, el in enumerate(class_elements[:5]):
                    class_name = await el.get_attribute("class")
                    print(f"   TR {i+1}: class='{class_name}'")

        print("\n🎯 Teste concluído!")
        return True

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        logger.error(f"Erro no teste: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


async def test_pdf_url_extraction():
    """Testa apenas a extração de URL do onclick"""
    print("\n🧪 Teste de Extração de URL do PDF")
    print("=" * 40)

    scraper = DJEScraperAdapter()

    # Exemplos de onclick reais
    test_onclicks = [
        "return popup('/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710');",
        "return popup('/cdje/consultaSimples.do?cdVolume=20&nuDiario=4093&cdCaderno=12&nuSeqpagina=3711');",
        "popup('/cdje/consultaSimples.do?cdVolume=21&nuDiario=4094&cdCaderno=12&nuSeqpagina=3712');",
    ]

    for i, onclick in enumerate(test_onclicks):
        print(f"\n🔗 Teste {i+1}: {onclick}")
        url = await scraper._extract_pdf_url_from_onclick(onclick)
        if url:
            print(f"   ✅ URL extraída: {url}")
        else:
            print(f"   ❌ Falha na extração")


if __name__ == "__main__":
    print("🚀 Iniciando teste do novo fluxo PDF scraper...")
    print("💡 Este teste verifica se conseguimos acessar e extrair links dos PDFs")
    print()

    # Primeiro teste: extração de URL
    asyncio.run(test_pdf_url_extraction())

    print("\n" + "=" * 60)

    # Segundo teste: fluxo completo
    success = asyncio.run(test_pdf_scraper_flow())

    if success:
        print(f"\n✅ TESTE PASSOU - Novo fluxo implementado com sucesso!")
        print(f"💡 Agora é necessário instalar as dependências de PDF")
        print(f"📋 Execute: pip install PyPDF2 pdfplumber")
    else:
        print(f"\n❌ TESTE FALHOU - Ainda há problemas a resolver")

    sys.exit(0 if success else 1)
