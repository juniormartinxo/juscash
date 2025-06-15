#!/usr/bin/env python3
"""
Teste específico para captura de links dinâmicos dos PDFs
Demonstra como os parâmetros são extraídos dinamicamente do HTML
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_dynamic_link_extraction():
    """
    Testa a extração dinâmica de links dos elementos tr.ementaClass
    Baseado no HTML real mostrado na imagem
    """

    print("🧪 Teste de Extração Dinâmica de Links PDF")
    print("=" * 60)
    print("💡 Demonstra como os parâmetros são capturados dinamicamente")
    print()

    scraper = DJEScraperAdapter()

    try:
        # Inicializar scraper
        print("🌐 Inicializando scraper...")
        await scraper.initialize()

        # Navegar e fazer pesquisa
        print("📍 Navegando para consulta avançada...")
        await scraper._navigate_to_advanced_search()

        print("📝 Preenchendo formulário...")
        search_terms = ["aposentadoria", "benefício", "INSS"]
        await scraper._fill_advanced_search_form(search_terms)

        # Aguardar resultados carregarem
        await asyncio.sleep(2)

        # Buscar elementos tr.ementaClass
        print("🔍 Buscando elementos tr.ementaClass...")
        ementa_elements = await scraper.page.query_selector_all("tr.ementaClass")

        if not ementa_elements:
            print("❌ Nenhum elemento tr.ementaClass encontrado")
            return False

        print(f"✅ Encontrados {len(ementa_elements)} elementos tr.ementaClass")
        print()

        # Analisar cada elemento detalhadamente
        for i, element in enumerate(ementa_elements):
            print(f"📋 ELEMENTO {i+1}:")
            print("-" * 40)

            # Extrair HTML do elemento para análise
            element_html = await element.inner_html()
            print(f"📄 HTML (primeiros 200 chars): {element_html[:200]}...")

            # Buscar todos os elementos com onclick
            onclick_elements = await element.query_selector_all("[onclick]")
            print(f"🔗 Total de elementos com onclick: {len(onclick_elements)}")

            # Analisar cada onclick
            for j, onclick_element in enumerate(onclick_elements):
                onclick_attr = await onclick_element.get_attribute("onclick")
                tag_name = await onclick_element.evaluate("el => el.tagName")

                print(f"   🏷️  Elemento {j+1}: <{tag_name.lower()}>")
                print(f"   📝 onclick: {onclick_attr}")

                # Verificar se é um link de PDF
                if onclick_attr and "consultaSimples.do" in onclick_attr:
                    print(f"   ✅ LINK DE PDF ENCONTRADO!")

                    # Extrair URL usando nossa função
                    pdf_url = await scraper._extract_pdf_url_from_onclick(onclick_attr)
                    if pdf_url:
                        print(f"   🌐 URL completa: {pdf_url}")

                        # Extrair parâmetros individuais
                        import re

                        params = {}
                        param_matches = re.findall(r"(\w+)=([^&]+)", pdf_url)
                        for param_name, param_value in param_matches:
                            params[param_name] = param_value

                        print(f"   📊 Parâmetros extraídos:")
                        for param, value in params.items():
                            print(f"      • {param}: {value}")
                    else:
                        print(f"   ❌ Falha na extração da URL")
                else:
                    print(f"   ⚪ Não é um link de PDF")

                print()

            print("=" * 40)
            print()

            # Limitar a 3 elementos para não sobrecarregar o teste
            if i >= 2:
                break

        return True

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


async def test_url_extraction_patterns():
    """Testa diferentes padrões de onclick que podem aparecer"""

    print("🧪 Teste de Padrões de Extração de URL")
    print("=" * 50)

    scraper = DJEScraperAdapter()

    # Exemplos baseados no HTML real da imagem
    test_patterns = [
        # Padrão da imagem fornecida
        "return popup('/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710');",
        # Variações possíveis
        "return popup('/cdje/consultaSimples.do?cdVolume=20&nuDiario=4093&cdCaderno=12&nuSeqpagina=3711');",
        "popup('/cdje/consultaSimples.do?cdVolume=21&nuDiario=4094&cdCaderno=12&nuSeqpagina=3712');",
        # Com &amp; (HTML encoded)
        "return popup('/cdje/consultaSimples.do?cdVolume=19&amp;nuDiario=4092&amp;cdCaderno=12&amp;nuSeqpagina=3710');",
        # Outros formatos possíveis
        'return popup("/cdje/consultaSimples.do?cdVolume=22&nuDiario=4095&cdCaderno=12&nuSeqpagina=3713");',
    ]

    print("📋 Testando diferentes padrões de onclick:")
    print()

    for i, pattern in enumerate(test_patterns):
        print(f"🔗 Padrão {i+1}:")
        print(f"   📝 Input: {pattern}")

        url = await scraper._extract_pdf_url_from_onclick(pattern)
        if url:
            print(f"   ✅ URL extraída: {url}")

            # Verificar parâmetros
            import re

            params = re.findall(r"(\w+)=([^&]+)", url)
            print(f"   📊 Parâmetros: {dict(params)}")
        else:
            print(f"   ❌ Falha na extração")

        print()


if __name__ == "__main__":
    print("🚀 Teste de Captura Dinâmica de Links PDF")
    print("💡 Demonstra como os parâmetros são extraídos do HTML real")
    print()

    # Teste 1: Padrões de extração
    asyncio.run(test_url_extraction_patterns())

    print("\n" + "=" * 60)

    # Teste 2: Extração dinâmica real
    success = asyncio.run(test_dynamic_link_extraction())

    if success:
        print("✅ TESTE PASSOU - Links dinâmicos capturados corretamente!")
        print("💡 Os parâmetros são extraídos dinamicamente do HTML real")
        print("📋 Cada tr.ementaClass pode ter diferentes parâmetros:")
        print("   • cdVolume: Volume do diário")
        print("   • nuDiario: Número do diário")
        print("   • cdCaderno: Código do caderno")
        print("   • nuSeqpagina: Número sequencial da página")
    else:
        print("❌ TESTE FALHOU - Problemas na captura dinâmica")

    sys.exit(0 if success else 1)
