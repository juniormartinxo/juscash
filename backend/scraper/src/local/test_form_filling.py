#!/usr/bin/env python3
"""
Teste específico para verificar o preenchimento do formulário
Baseado na imagem fornecida pelo usuário
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_form_filling_detailed():
    """Testa o preenchimento detalhado do formulário"""

    print("🧪 Teste Detalhado do Preenchimento do Formulário")
    print("=" * 60)
    print("💡 Baseado na imagem fornecida pelo usuário")
    print()

    scraper = DJEScraperAdapter()

    try:
        # Inicializar
        await scraper.initialize()

        # Navegar para consulta avançada
        print("📍 Navegando para consulta avançada...")
        await scraper._navigate_to_advanced_search()

        # Aguardar carregamento
        await asyncio.sleep(3)

        print("🔍 ANÁLISE DO FORMULÁRIO:")
        print("-" * 40)

        # 1. Verificar campos de data
        print("📅 CAMPOS DE DATA:")
        data_inicio_selector = 'input[name="dadosConsulta.dtInicioString"]'
        data_fim_selector = 'input[name="dadosConsulta.dtFimString"]'

        data_inicio_element = await scraper.page.query_selector(data_inicio_selector)
        data_fim_element = await scraper.page.query_selector(data_fim_selector)

        if data_inicio_element:
            current_value = await data_inicio_element.get_attribute("value")
            print(f"   📅 Data início atual: '{current_value}'")

            # Verificar se está preenchido com data de hoje
            hoje = datetime.now().strftime("%d/%m/%Y")
            print(f"   📅 Data de hoje: '{hoje}'")

            # Preencher com data específica (conforme imagem: 13/11/2024)
            await data_inicio_element.fill("13/11/2024")
            new_value = await data_inicio_element.get_attribute("value")
            print(f"   ✅ Data início preenchida: '{new_value}'")
        else:
            print("   ❌ Campo data início não encontrado")

        if data_fim_element:
            current_value = await data_fim_element.get_attribute("value")
            print(f"   📅 Data fim atual: '{current_value}'")

            await data_fim_element.fill("13/11/2024")
            new_value = await data_fim_element.get_attribute("value")
            print(f"   ✅ Data fim preenchida: '{new_value}'")
        else:
            print("   ❌ Campo data fim não encontrado")

        # 2. Verificar campo Caderno
        print("\n📋 CAMPO CADERNO:")
        caderno_selector = 'select[name="dadosConsulta.cdCaderno"]'
        caderno_element = await scraper.page.query_selector(caderno_selector)

        if caderno_element:
            # Listar todas as opções disponíveis
            options = await caderno_element.query_selector_all("option")
            print(f"   📋 Opções disponíveis ({len(options)}):")

            for i, option in enumerate(options[:10]):  # Mostrar primeiras 10
                value = await option.get_attribute("value")
                text = await option.inner_text()
                print(f"      {i + 1}. value='{value}' text='{text}'")

            # Verificar valor atual
            current_value = await caderno_element.get_attribute("value")
            print(f"   📋 Valor atual selecionado: '{current_value}'")

            # Tentar selecionar Caderno 3
            try:
                await caderno_element.select_option("12")
                new_value = await caderno_element.get_attribute("value")
                print(f"   ✅ Caderno selecionado: '{new_value}'")
            except Exception as e:
                print(f"   ❌ Erro ao selecionar caderno: {e}")
        else:
            print("   ❌ Campo caderno não encontrado")

        # 3. Verificar campo Palavras-chave
        print("\n🔍 CAMPO PALAVRAS-CHAVE:")
        palavras_chave_selector = 'input[name="dadosConsulta.pesquisaLivre"]'
        palavras_element = await scraper.page.query_selector(palavras_chave_selector)

        if palavras_element:
            current_value = await palavras_element.get_attribute("value")
            print(f"   🔍 Valor atual: '{current_value}'")

            # Preencher conforme imagem: "RPV" e "pagamento pelo INSS"
            test_query = '"RPV" e "pagamento pelo INSS"'
            await palavras_element.fill(test_query)
            new_value = await palavras_element.get_attribute("value")
            print(f"   ✅ Palavras-chave preenchidas: '{new_value}'")
        else:
            print("   ❌ Campo palavras-chave não encontrado")

        # 4. Capturar screenshot do formulário preenchido
        print("\n📸 Capturando screenshot do formulário...")
        debug_dir = Path("logs/debug_images")
        debug_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = debug_dir / "form_filled_debug.png"
        await scraper.page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"   ✅ Screenshot salvo: {screenshot_path}")

        # 5. Executar pesquisa
        print("\n🔍 EXECUTANDO PESQUISA:")
        submit_button = 'input[value="Pesquisar"]'
        submit_element = await scraper.page.query_selector(submit_button)

        if submit_element:
            print("   🔘 Clicando em Pesquisar...")
            await submit_element.click()
            await scraper.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Verificar URL após pesquisa
            current_url = scraper.page.url
            print(f"   🌐 URL após pesquisa: {current_url}")

            # Capturar screenshot dos resultados
            results_screenshot_path = debug_dir / "results_debug.png"
            await scraper.page.screenshot(
                path=str(results_screenshot_path), full_page=True
            )
            print(f"   ✅ Screenshot dos resultados: {results_screenshot_path}")

            # Verificar elementos encontrados
            ementa_elements = await scraper.page.query_selector_all("tr.ementaClass")
            onclick_elements = await scraper.page.query_selector_all(
                '[onclick*="consultaSimples.do"]'
            )

            print(f"   📋 Elementos tr.ementaClass: {len(ementa_elements)}")
            print(f"   🔗 Elementos com consultaSimples.do: {len(onclick_elements)}")

            # Mostrar alguns links encontrados
            if onclick_elements:
                print("   📄 Primeiros links encontrados:")
                for i, element in enumerate(onclick_elements[:5]):
                    onclick_attr = await element.get_attribute("onclick")
                    if onclick_attr and "consultaSimples.do" in onclick_attr:
                        print(f"      {i + 1}. {onclick_attr[:100]}...")
        else:
            print("   ❌ Botão Pesquisar não encontrado")

        return True

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    print("🚀 Teste de Preenchimento do Formulário")
    print("💡 Verificando se o formulário está sendo preenchido conforme a imagem")
    print()

    success = asyncio.run(test_form_filling_detailed())

    if success:
        print("\n✅ TESTE CONCLUÍDO")
        print("📋 Verifique os screenshots gerados em logs/debug_images/:")
        print("   • form_filled_debug.png - Formulário preenchido")
        print("   • results_debug.png - Resultados da pesquisa")
        print("💡 Compare com os critérios que você está usando manualmente")
    else:
        print("\n❌ TESTE FALHOU")

    sys.exit(0 if success else 1)
