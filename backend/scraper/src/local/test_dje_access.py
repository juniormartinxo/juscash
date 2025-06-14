"""Teste de acesso visual ao DJE"""

import asyncio
from playwright.async_api import async_playwright


async def test_dje_visual():
    """Teste visual do DJE - você pode ver o que está acontecendo"""

    playwright = await async_playwright().start()

    # Browser NÃO headless para você ver
    browser = await playwright.chromium.launch(
        headless=False,  # Vai abrir janela do browser
        slow_mo=2000,  # Slow motion para ver melhor
    )

    page = await browser.new_page()

    try:
        print("🌐 Acessando DJE...")
        await page.goto("https://dje.tjsp.jus.br/cdje/index.do", timeout=30000)

        print("📄 Página carregada - você deve ver o DJE aberto")
        print("⏳ Aguardando 10 segundos para você ver...")
        await asyncio.sleep(10)

        # Tentar encontrar pesquisa avançada
        advanced_link = await page.query_selector('a:text("Pesquisa")')
        if advanced_link:
            print("✅ Link de pesquisa encontrado")
            await advanced_link.click()
            await asyncio.sleep(5)

        # Capturar screenshot
        await page.screenshot(path="debug/dje_screenshot.png")
        print("📸 Screenshot salvo em debug/dje_screenshot.png")

    except Exception as e:
        print(f"❌ Erro: {e}")

    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_dje_visual())
