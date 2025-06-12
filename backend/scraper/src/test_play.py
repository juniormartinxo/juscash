import asyncio
from adapters.secondary.playwright_scraper import PlaywrightScraperAdapter

async def test_scraper():
    scraper = PlaywrightScraperAdapter(headless=False)
    
    try:
        print("🚀 Inicializando scraper...")
        await scraper.initialize()
        print("✅ Scraper inicializado!")
        
        print("🌐 Navegando para teste...")
        await scraper.page.goto('https://example.com')
        print("✅ Navegação concluída!")
        
        print("⏳ Aguardando 5 segundos...")
        await scraper.page.wait_for_timeout(5000)
        
        print("📸 Tirando screenshot...")
        await scraper.page.screenshot(path='test_scraper.png')
        print("✅ Screenshot salvo!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        print("🔒 Fechando scraper...")
        await scraper.close()
        print("✅ Teste concluído!")

if __name__ == '__main__':
    asyncio.run(test_scraper())