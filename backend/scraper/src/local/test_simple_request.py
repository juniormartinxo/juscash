"""
Teste simples para verificar headers HTTP
"""

import asyncio
import httpx
import os


async def test_simple_request():
    """Teste simples de requisição HTTP"""

    api_key = "scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP"
    base_url = "http://juscash-api:8000"

    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🌐 URL: {base_url}/api/scraper/publications")

    # Dados mínimos para teste - usando formato ISO mais simples
    test_data = {
        "process_number": "TEST-123",
        "availabilityDate": "2024-03-15T00:00:00.000Z",  # Formato UTC
        "authors": ["Teste"],
        "content": "Teste",
    }

    headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    print("\n📤 Headers enviados:")
    for key, value in headers.items():
        if key == "X-API-Key":
            print(f"  {key}: {value[:20]}...")
        else:
            print(f"  {key}: {value}")

    print("\n📋 Dados enviados:")
    print(f"  {test_data}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/scraper/publications", json=test_data, headers=headers
            )

            print("\n📥 Resposta:")
            print(f"  Status: {response.status_code}")
            print(f"  Body: {response.text}")

            return response.status_code == 201

    except Exception as error:
        print(f"❌ Erro: {error}")
        return False


if __name__ == "__main__":
    asyncio.run(test_simple_request())
