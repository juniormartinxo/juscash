"""
Teste usando exatamente o formato da documentação da API
"""

import asyncio
import httpx


async def test_exact_format():
    """Teste usando formato exato da documentação"""

    api_key = "scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP"
    base_url = "http://juscash-api:8000"

    # Dados exatos da documentação
    publication_data = {
        "process_number": "1234567-89.2024.8.26.0100",
        "publicationDate": "2024-03-15T00:00:00.000Z",
        "availability_date": "2024-03-17T00:00:00.000Z",
        "authors": ["João Silva Santos", "Maria Oliveira"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [{"name": "Dr. Carlos Advogado", "oab": "123456"}],
        "gross_value": 150000,
        "net_value": 135000,
        "interest_value": 10000,
        "attorney_fees": 5000,
        "content": "Conteúdo completo da publicação...",
        "status": "NOVA",
        "scraping_source": "DJE-SP",
        "extraction_metadata": {
            "extraction_date": "2024-03-17T10:30:00.000Z",
            "source_url": "https://dje.tjsp.jus.br/...",
            "confidence_score": 0.95,
        },
    }

    headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    print("🔍 Testando com dados exatos da documentação")
    print(f"🌐 URL: {base_url}/api/scraper/publications")
    print(f"🔑 API Key: {api_key[:20]}...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/scraper/publications",
                json=publication_data,
                headers=headers,
            )

            print(f"\n📥 Resposta:")
            print(f"  Status: {response.status_code}")
            print(f"  Body: {response.text}")

            if response.status_code == 201:
                print("✅ Sucesso!")
                return True
            else:
                print("❌ Falha")
                return False

    except Exception as error:
        print(f"❌ Erro: {error}")
        return False


if __name__ == "__main__":
    asyncio.run(test_exact_format())
