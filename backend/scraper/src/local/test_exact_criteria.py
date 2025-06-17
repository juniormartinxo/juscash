#!/usr/bin/env python3
"""
Teste com os critérios EXATOS da imagem fornecida
Data: 13/11/2024
Caderno: caderno 3 - Judicial - 1ª Instância - Capital - Parte I
Palavras-chave: "RPV" e "pagamento pelo INSS"
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_exact_image_criteria():
    """Testa com os critérios EXATOS da imagem"""

    print("🎯 Teste com Critérios EXATOS da Imagem")
    print("=" * 50)
    print("📅 Data: 13/11/2024")
    print("📋 Caderno: caderno 3 - Judicial - 1ª Instância - Capital - Parte I")
    print('🔍 Palavras-chave: "RPV" e "pagamento pelo INSS"')
    print()

    scraper = DJEScraperAdapter()

    try:
        # Inicializar
        await scraper.initialize()

        # Navegar para consulta avançada
        print("📍 Navegando para consulta avançada...")
        await scraper._navigate_to_advanced_search()
        await asyncio.sleep(3)

        print("🔧 PREENCHENDO FORMULÁRIO MANUALMENTE:")
        print("-" * 40)

        # 1. FORÇAR DATA ESPECÍFICA (mesmo que readonly)
        print("📅 1. Configurando datas para 13/11/2024...")

        # Tentar remover readonly e forçar data
        data_inicio_script = """
        const dataInicio = document.querySelector('#dtInicioString');
        if (dataInicio) {
            dataInicio.removeAttribute('readonly');
            dataInicio.disabled = false;
            dataInicio.value = '13/11/2024';
            console.log('Data início forçada:', dataInicio.value);
        }
        """

        data_fim_script = """
        const dataFim = document.querySelector('#dtFimString');
        if (dataFim) {
            dataFim.removeAttribute('readonly');
            dataFim.disabled = false;
            dataFim.value = '13/11/2024';
            console.log('Data fim forçada:', dataFim.value);
        }
        """

        try:
            await scraper.page.evaluate(data_inicio_script)
            await scraper.page.evaluate(data_fim_script)
            print("   ✅ Datas forçadas para 13/11/2024")
        except Exception as e:
            print(f"   ⚠️ Erro ao forçar datas: {e}")

        # 2. SELECIONAR CADERNO 3
        print("📋 2. Selecionando Caderno 3...")
        caderno_selector = 'select[name="dadosConsulta.cdCaderno"]'

        try:
            await scraper.page.select_option(caderno_selector, value="12")

            # Verificar seleção
            selected_option = await scraper.page.evaluate(
                """
                const select = document.querySelector('select[name="dadosConsulta.cdCaderno"]');
                const selectedOption = select.options[select.selectedIndex];
                return {
                    value: select.value,
                    text: selectedOption.text
                };
            """
            )

            print(
                f"   ✅ Caderno selecionado: {selected_option['text']} (value: {selected_option['value']})"
            )
        except Exception as e:
            print(f"   ❌ Erro ao selecionar caderno: {e}")

        # 3. PREENCHER PALAVRAS-CHAVE EXATAS
        print("🔍 3. Preenchendo palavras-chave...")
        palavras_exatas = '"RPV" e "pagamento pelo INSS"'

        try:
            # Usar JavaScript para garantir preenchimento
            palavras_script = f"""
            const campo = document.querySelector('#procura');
            if (campo) {{
                campo.value = '{palavras_exatas}';
                campo.dispatchEvent(new Event('input', {{ bubbles: true }}));
                campo.dispatchEvent(new Event('change', {{ bubbles: true }}));
                console.log('Palavras-chave definidas:', campo.value);
            }}
            """

            await scraper.page.evaluate(palavras_script)

            # Verificar se foi preenchido
            valor_campo = await scraper.page.evaluate(
                "document.querySelector('#procura')?.value || ''"
            )
            print(f"   ✅ Palavras-chave preenchidas: '{valor_campo}'")

        except Exception as e:
            print(f"   ❌ Erro ao preencher palavras-chave: {e}")

        # 4. CAPTURAR SCREENSHOT DO FORMULÁRIO PREENCHIDO
        print("📸 4. Capturando screenshot do formulário...")
        debug_dir = Path("logs/debug_images")
        debug_dir.mkdir(parents=True, exist_ok=True)
        form_screenshot_path = debug_dir / "exact_criteria_form.png"
        await scraper.page.screenshot(path=str(form_screenshot_path), full_page=True)
        print(f"   ✅ Screenshot salvo: {form_screenshot_path}")

        # 5. SUBMETER PESQUISA
        print("🔍 5. Executando pesquisa...")

        try:
            submit_button = await scraper.page.query_selector(
                'input[value="Pesquisar"]'
            )
            if submit_button:
                await submit_button.click()
                await scraper.page.wait_for_load_state("networkidle")
                await asyncio.sleep(5)  # Aguardar resultados

                print("   ✅ Pesquisa executada")

                # Verificar URL final
                final_url = scraper.page.url
                print(f"   🌐 URL final: {final_url}")

                # Capturar screenshot dos resultados
                results_screenshot_path = debug_dir / "exact_criteria_results.png"
                await scraper.page.screenshot(
                    path=str(results_screenshot_path), full_page=True
                )
                print(f"   ✅ Screenshot dos resultados: {results_screenshot_path}")

            else:
                print("   ❌ Botão Pesquisar não encontrado")

        except Exception as e:
            print(f"   ❌ Erro ao executar pesquisa: {e}")

        # 6. ANALISAR RESULTADOS
        print("\n📊 ANÁLISE DOS RESULTADOS:")
        print("-" * 30)

        # Verificar elementos encontrados
        ementa_elements = await scraper.page.query_selector_all("tr.ementaClass")
        onclick_elements = await scraper.page.query_selector_all(
            '[onclick*="consultaSimples.do"]'
        )
        all_tr = await scraper.page.query_selector_all("tr")

        print(f"📋 Elementos tr.ementaClass: {len(ementa_elements)}")
        print(f"🔗 Elementos com consultaSimples.do: {len(onclick_elements)}")
        print(f"📄 Total de elementos tr: {len(all_tr)}")

        # Mostrar alguns links se encontrados
        if onclick_elements:
            print("\n📄 Primeiros links encontrados:")
            for i, element in enumerate(onclick_elements[:5]):
                onclick_attr = await element.get_attribute("onclick")
                if onclick_attr and "consultaSimples.do" in onclick_attr:
                    print(f"   {i + 1}. {onclick_attr[:100]}...")

        # Verificar se há mensagens de erro ou "nenhum resultado"
        page_text = await scraper.page.inner_text("body")
        if (
            "nenhum resultado" in page_text.lower()
            or "não foram encontrados" in page_text.lower()
        ):
            print("⚠️ Mensagem de 'nenhum resultado' encontrada")

        return len(onclick_elements) > 0

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    print("🚀 Teste com Critérios Exatos da Imagem")
    print("💡 Replicando exatamente os critérios mostrados na imagem")
    print()

    success = asyncio.run(test_exact_image_criteria())

    if success:
        print("\n🎉 TESTE PASSOU!")
        print("✅ Links de PDF encontrados com os critérios exatos")
        print("📋 Verifique os screenshots em logs/debug_images/:")
        print("   • exact_criteria_form.png - Formulário preenchido")
        print("   • exact_criteria_results.png - Resultados da pesquisa")
    else:
        print("\n⚠️ TESTE NÃO ENCONTROU RESULTADOS")
        print("💡 Isso pode significar:")
        print("   • Não há publicações para 13/11/2024 com esses critérios")
        print("   • Os critérios precisam ser ajustados")
        print("   • A data específica não tem dados disponíveis")

    sys.exit(0 if success else 1)
