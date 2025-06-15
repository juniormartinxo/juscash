#!/usr/bin/env python3
"""
Debug da estrutura da página para encontrar os elementos corretos
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def debug_page_structure():
    """Debug completo da estrutura da página"""

    print("🔍 Debug da Estrutura da Página DJE")
    print("=" * 50)

    scraper = DJEScraperAdapter()

    try:
        # Inicializar
        await scraper.initialize()

        # Navegar
        print("📍 Navegando para consulta avançada...")
        await scraper._navigate_to_advanced_search()

        # Preencher formulário com termos mais amplos
        print("📝 Preenchendo formulário com termos amplos...")
        search_terms = ["INSS"]  # Termo mais amplo
        await scraper._fill_advanced_search_form(search_terms)

        # Aguardar resultados
        await asyncio.sleep(3)

        # Debug: título da página
        title = await scraper.page.title()
        print(f"📄 Título da página: {title}")

        # Debug: URL atual
        url = scraper.page.url
        print(f"🌐 URL atual: {url}")

        # Verificar se há resultados
        print("\n🔍 ANÁLISE DE ELEMENTOS:")
        print("-" * 30)

        # 1. Buscar tr.ementaClass
        ementa_elements = await scraper.page.query_selector_all("tr.ementaClass")
        print(f"📋 tr.ementaClass: {len(ementa_elements)} encontrados")

        # 2. Buscar variações de class
        class_variations = [
            'tr[class*="ementa"]',
            'tr[class*="Ementa"]',
            'tr[class*="resultado"]',
            'tr[class*="publicacao"]',
            'tr[class*="linha"]',
        ]

        for selector in class_variations:
            elements = await scraper.page.query_selector_all(selector)
            print(f"📋 {selector}: {len(elements)} encontrados")

        # 3. Buscar todos os tr com class
        all_tr_with_class = await scraper.page.query_selector_all("tr[class]")
        print(f"📋 tr[class] (todos): {len(all_tr_with_class)} encontrados")

        # Mostrar as primeiras 10 classes
        if all_tr_with_class:
            print("   📝 Primeiras classes encontradas:")
            for i, tr in enumerate(all_tr_with_class[:10]):
                class_name = await tr.get_attribute("class")
                print(f"      {i+1}. class='{class_name}'")

        # 4. Buscar elementos com onclick
        onclick_elements = await scraper.page.query_selector_all('[onclick*="popup"]')
        print(f"🔗 Elementos com onclick popup: {len(onclick_elements)} encontrados")

        if onclick_elements:
            print("   📝 Primeiros onclick encontrados:")
            for i, element in enumerate(onclick_elements[:5]):
                onclick_attr = await element.get_attribute("onclick")
                tag_name = await element.evaluate("el => el.tagName")
                print(
                    f"      {i+1}. <{tag_name.lower()}> onclick='{onclick_attr[:100]}...'"
                )

        # 5. Buscar por consultaSimples.do
        consulta_elements = await scraper.page.query_selector_all(
            '[onclick*="consultaSimples.do"]'
        )
        print(
            f"📄 Elementos com consultaSimples.do: {len(consulta_elements)} encontrados"
        )

        # 6. Verificar se há mensagem de "nenhum resultado"
        no_results_selectors = [
            ':text("Nenhum resultado")',
            ':text("Não foram encontrados")',
            ':text("sem resultados")',
            ".mensagem",
            ".aviso",
            ".erro",
        ]

        for selector in no_results_selectors:
            elements = await scraper.page.query_selector_all(selector)
            if elements:
                for element in elements:
                    text = await element.inner_text()
                    print(f"⚠️ Mensagem encontrada: '{text}'")

        # 7. Capturar screenshot para análise
        screenshot_path = "debug_page_structure.png"
        await scraper.page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot salvo: {screenshot_path}")

        # 8. Salvar HTML da página
        html_content = await scraper.page.content()
        html_path = "debug_page_content.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"💾 HTML salvo: {html_path}")

        # 9. Buscar tabelas
        tables = await scraper.page.query_selector_all("table")
        print(f"📊 Tabelas encontradas: {len(tables)}")

        if tables:
            for i, table in enumerate(tables[:3]):
                rows = await table.query_selector_all("tr")
                print(f"   Tabela {i+1}: {len(rows)} linhas")

        return True

    except Exception as error:
        print(f"❌ Erro durante debug: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    print("🚀 Debug da Estrutura da Página DJE")
    print("💡 Vamos descobrir a estrutura real da página")
    print()

    success = asyncio.run(debug_page_structure())

    if success:
        print("\n✅ DEBUG CONCLUÍDO")
        print("📋 Verifique os arquivos gerados:")
        print("   • debug_page_structure.png - Screenshot da página")
        print("   • debug_page_content.html - HTML completo")
        print("💡 Use essas informações para ajustar os seletores")
    else:
        print("\n❌ DEBUG FALHOU")

    sys.exit(0 if success else 1)
