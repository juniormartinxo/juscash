#!/usr/bin/env python3
"""
Script de teste para verificar se o scraper está funcionando
"""

import sys
from pathlib import Path

# Adicionar o src ao path para imports
sys.path.append(str(Path(__file__).parent / "src"))


def test_imports():
    """Testa se todas as dependências estão instaladas"""
    print("🧪 Testando imports...")

    try:
        import playwright

        print("✅ Playwright instalado")
    except ImportError:
        print("❌ Playwright não encontrado - execute: pip install playwright")
        return False

    try:
        import PyPDF2

        print("✅ PyPDF2 instalado")
    except ImportError:
        print("❌ PyPDF2 não encontrado - execute: pip install PyPDF2")
        return False

    try:
        import click

        print("✅ Click instalado")
    except ImportError:
        print("❌ Click não encontrado - execute: pip install click")
        return False

    try:
        from domain.entities.publication import Publication

        print("✅ Entidades do domínio carregadas")
    except ImportError:
        print("❌ Erro ao carregar entidades - verifique estrutura src/")
        return False

    try:
        from infrastructure.files.report_json_saver import ReportJsonSaver

        print("✅ ReportJsonSaver carregado")
    except ImportError:
        print("❌ Erro ao carregar ReportJsonSaver")
        return False

    return True


def test_browser():
    """Testa se o browser do Playwright está instalado"""
    print("\n🌐 Testando browser...")

    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def check_browser():
            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(headless=True)
                print("✅ Browser Chromium disponível")
                await browser.close()
                return True
            except Exception as e:
                print(f"❌ Erro ao iniciar browser: {e}")
                print("Execute: playwright install chromium")
                return False
            finally:
                await playwright.stop()

        return asyncio.run(check_browser())

    except Exception as e:
        print(f"❌ Erro ao testar browser: {e}")
        return False


def main():
    print("🚀 Teste do DJE Scraper com Playwright")
    print("=" * 50)

    # Teste de imports
    imports_ok = test_imports()

    # Teste de browser
    browser_ok = test_browser()

    print("\n" + "=" * 50)

    if imports_ok and browser_ok:
        print("✅ Todos os testes passaram!")
        print("\nO scraper está pronto para uso.")
        print(
            "Execute: python scraping.py run --start-date YYYY-MM-DD --end-date YYYY-MM-DD"
        )
    else:
        print("❌ Alguns testes falharam!")
        print("\nExecute o script de instalação:")
        print("./install-scraper.sh")


if __name__ == "__main__":
    main()
