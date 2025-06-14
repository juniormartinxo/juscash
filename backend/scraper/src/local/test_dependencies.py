"""Teste rápido de dependências"""


def test_dependencies():
    try:
        import playwright

        print("✅ Playwright OK")

        import httpx

        print("✅ HTTPX OK")

        import loguru

        print("✅ Loguru OK")

        import pydantic

        print("✅ Pydantic OK")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        print("✅ Chromium browser OK")

        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    test_dependencies()
