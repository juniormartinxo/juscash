"""
Script para debugar requisição HTTP enviada para a API
"""

import asyncio
import json
import httpx
from datetime import datetime
from src.domain.entities.publication import Publication, Lawyer, MonetaryValue
from src.infrastructure.config.settings import get_settings


async def debug_http_request():
    """Debug da requisição HTTP enviada para a API"""

    # Configurações
    settings = get_settings()
    base_url = settings.api.base_url
    api_key = settings.api.scraper_api_key

    print(f"🌐 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}...")

    # Criar publicação de teste
    test_publication = Publication(
        process_number=f"TEST-{int(datetime.now().timestamp())}-89.2024.8.26.0100",
        publication_date=datetime(2024, 3, 15),
        availability_date=datetime.now(),
        authors=["João Silva Santos - TESTE", "Maria Oliveira - TESTE"],
        lawyers=[
            Lawyer(name="Dr. Carlos Advogado - TESTE", oab="123456"),
            Lawyer(name="Dra. Ana Jurista - TESTE", oab="789012"),
        ],
        gross_value=MonetaryValue.from_real(1500.00),
        net_value=MonetaryValue.from_real(1350.00),
        interest_value=MonetaryValue.from_real(100.00),
        attorney_fees=MonetaryValue.from_real(50.00),
        content="Conteúdo de teste da publicação do DJE sobre aposentadoria por invalidez do INSS. Este é um teste automatizado da conexão entre o scraper e a API.",
        extraction_metadata={
            "extraction_date": datetime.now().isoformat(),
            "source_url": "https://dje.tjsp.jus.br/test",
            "confidence_score": 1.0,
            "test_run": True,
        },
    )

    # Converter para formato da API
    api_data = test_publication.to_api_dict()

    print("\n🔍 DEBUG: Dados que serão enviados")
    print("=" * 60)
    print(json.dumps(api_data, indent=2, ensure_ascii=False, default=str))
    print("=" * 60)

    # Fazer requisição HTTP com debug
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n📤 Enviando POST para: {base_url}/api/scraper/publications")
            print(
                f"🔑 Headers: Content-Type: application/json, X-API-Key: {api_key[:8]}..."
            )

            response = await client.post(
                f"{base_url}/api/scraper/publications",
                json=api_data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
            )

            print(f"\n📥 Resposta HTTP:")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")

            if response.status_code == 201:
                print("✅ Sucesso!")
                return True
            else:
                print("❌ Falha na requisição")

                # Tentar parsear resposta JSON para mais detalhes
                try:
                    error_data = response.json()
                    print(f"📋 Detalhes do erro: {json.dumps(error_data, indent=2)}")
                except:
                    print("📋 Não foi possível parsear resposta como JSON")

                return False

    except Exception as error:
        print(f"❌ Erro na requisição: {error}")
        print(f"🔧 Tipo do erro: {type(error).__name__}")
        return False


if __name__ == "__main__":
    asyncio.run(debug_http_request())
