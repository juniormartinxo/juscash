#!/usr/bin/env python3
"""
Teste de chamada real para a API
"""

import sys
import json
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.entities.publication import Publication, MonetaryValue
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_real_api_call():
    """Faz uma chamada real para a API para ver o erro específico"""
    print("🌐 Teste de Chamada Real para a API")
    print("=" * 50)

    # Obter configurações
    settings = get_settings()
    base_url = settings.api.base_url
    api_key = settings.api.scraper_api_key

    print(f"🔗 URL da API: {base_url}")
    print(f"🔑 API Key: {'***' + api_key[-4:] if api_key else 'NÃO CONFIGURADA'}")

    # Criar publicação de teste
    publication = Publication(
        process_number="0013168-70.2024.8.26.0053",
        publication_date=datetime(2024, 11, 13),
        availability_date=datetime(2024, 11, 13),
        authors=["Maria da Silva"],
        content="Execução de RPV para pagamento pelo INSS no valor de R$ 15.000,00",
        gross_value=MonetaryValue.from_real(15000),
    )

    # Converter para formato da API
    api_data = publication.to_api_dict()

    print("\n📤 Dados que serão enviados:")
    print(json.dumps(api_data, indent=2, ensure_ascii=False))

    # Fazer chamada para a API
    print(f"\n🚀 Fazendo POST para: {base_url}/api/scraper/publications")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/api/scraper/publications",
                json=api_data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
            )

            print(f"\n📊 Resposta da API:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")

            try:
                response_data = response.json()
                print(f"   Body (JSON):")
                print(json.dumps(response_data, indent=4, ensure_ascii=False))

                # Analisar erro específico
                if response.status_code == 400:
                    print(f"\n🔍 Análise do Erro de Validação:")

                    if isinstance(response_data, dict):
                        if "error" in response_data:
                            print(f"   ❌ Erro: {response_data['error']}")

                        if "details" in response_data:
                            print(f"   📋 Detalhes:")
                            for detail in response_data["details"]:
                                print(f"      • Campo: {detail.get('field', 'N/A')}")
                                print(
                                    f"        Mensagem: {detail.get('message', 'N/A')}"
                                )

                        if "success" in response_data:
                            print(f"   ✅ Success: {response_data['success']}")

            except Exception as e:
                print(f"   Body (Text): {response.text}")
                print(f"   Erro ao parsear JSON: {e}")

            if response.status_code == 201:
                print("\n✅ Publicação criada com sucesso!")
            elif response.status_code == 400:
                print("\n❌ Erro de validação - veja detalhes acima")
            elif response.status_code == 401:
                print("\n🔐 Erro de autenticação - verifique a API Key")
            elif response.status_code == 429:
                print("\n⏰ Rate limit atingido")
            else:
                print(f"\n⚠️ Erro inesperado: {response.status_code}")

    except httpx.ConnectError as e:
        print(f"\n🔌 Erro de conexão: {e}")
        print("   Verifique se a API está rodando")
    except httpx.TimeoutException:
        print(f"\n⏰ Timeout na requisição")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")


async def test_api_health():
    """Testa se a API está respondendo"""
    print("\n🏥 Teste de Saúde da API")
    print("=" * 30)

    settings = get_settings()
    base_url = settings.api.base_url

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Tentar endpoint de health/status
            health_endpoints = [
                f"{base_url}/health",
                f"{base_url}/api/health",
                f"{base_url}/status",
                f"{base_url}/api/status",
                f"{base_url}/",
            ]

            for endpoint in health_endpoints:
                try:
                    print(f"   Testando: {endpoint}")
                    response = await client.get(endpoint)
                    print(f"   ✅ {response.status_code}: {endpoint}")
                    if response.status_code == 200:
                        break
                except:
                    print(f"   ❌ Falhou: {endpoint}")

    except Exception as e:
        print(f"   💥 Erro geral: {e}")


if __name__ == "__main__":
    print("🚀 Teste de Chamada Real para a API")
    print("💡 Verificando erro específico de validação")
    print()

    # Testar saúde da API
    asyncio.run(test_api_health())

    # Fazer chamada real
    asyncio.run(test_real_api_call())

    print("\n📋 Resumo:")
    print("✅ Teste de chamada real executado")
    print("💡 Verifique os detalhes do erro acima")
    print("🔧 Se necessário, ajuste o formato dos dados ou configurações")
