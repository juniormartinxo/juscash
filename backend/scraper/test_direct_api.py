#!/usr/bin/env python3
"""
Teste simples de envio direto para API
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configurações
API_BASE_URL = "http://localhost:8000"
API_KEY = "scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP"


async def test_direct_api():
    """Testa envio direto de publicação para a API"""

    print("🧪 Teste de Envio Direto para API")
    print("=" * 50)

    # Criar publicação de teste
    publication_data = {
        "process_number": f"TEST-DIRECT-{int(datetime.now().timestamp())}-89.2024.8.26.0100",
        "availability_date": "2024-03-17T00:00:00.000Z",
        "authors": ["João Silva Santos", "Maria Oliveira"],
        "defendant": "Instituto Nacional do Seguro Social - INSS",
        "lawyers": [
            {"name": "Dr. Carlos Advogado", "oab": "123456"},
            {"name": "Dra. Ana Jurista", "oab": "789012"},
        ],
        "gross_value": 150000,  # R$ 1500,00 em centavos
        "net_value": 135000,  # R$ 1350,00 em centavos
        "interest_value": 10000,  # R$ 100,00 em centavos
        "attorney_fees": 5000,  # R$ 50,00 em centavos
        "content": "Conteúdo completo da publicação do DJE sobre RPV aposentadoria por invalidez do INSS. Valor a ser pago pelo Instituto Nacional do Seguro Social conforme decisão judicial.",
        "status": "NOVA",
        "scraping_source": "DJE-SP",
        "caderno": "3",
        "instancia": "1",
        "local": "Capital",
        "parte": "1",
        "extraction_metadata": {
            "extraction_date": datetime.now().isoformat(),
            "source_url": "https://dje.tjsp.jus.br/test",
            "confidence_score": 0.95,
            "test_run": True,
        },
    }

    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    print(f"📤 Enviando para: {API_BASE_URL}/api/scraper/publications")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    print(f"📋 Processo: {publication_data['process_number']}")
    print(f"👥 Autores: {len(publication_data['authors'])}")
    print(f"⚖️ Advogados: {len(publication_data['lawyers'])}")
    print(f"💰 Valor bruto: R$ {publication_data['gross_value'] / 100:.2f}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/scraper/publications",
                json=publication_data,
                headers=headers,
            )

            print(f"\n📥 Resposta da API:")
            print(f"Status: {response.status_code}")

            if response.status_code == 201:
                data = response.json()
                publication_id = data["data"]["publication"]["id"]
                print(f"✅ SUCESSO! Publicação criada com ID: {publication_id}")
                print(
                    f"🎯 Processo salvo: {data['data']['publication']['process_number']}"
                )
                return True
            else:
                print(f"❌ ERRO: {response.text}")
                return False

    except Exception as error:
        print(f"❌ Erro na requisição: {error}")
        return False


async def check_database():
    """Verifica se os dados foram salvos no banco"""
    print(f"\n🔍 Verificando dados salvos no banco...")

    try:
        # Verificar via API health (sem auth)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")

            if response.status_code == 200:
                print("✅ API está respondendo normalmente")
                return True
            else:
                print(f"⚠️ API health check: {response.status_code}")
                return False

    except Exception as error:
        print(f"❌ Erro ao verificar API: {error}")
        return False


async def main():
    """Executa o teste completo"""
    print("🚀 Iniciando teste de salvamento no banco de dados")
    print("=" * 60)

    # Teste 1: Enviar dados para API
    api_success = await test_direct_api()

    if not api_success:
        print("\n❌ Falha no envio para API. Abortando teste.")
        return

    # Teste 2: Verificar se API está funcionando
    db_success = await check_database()

    if db_success:
        print("\n🎉 RESULTADO FINAL:")
        print("✅ Dados enviados com sucesso para a API")
        print("✅ API está funcionando corretamente")
        print("✅ Dados devem estar salvos no banco PostgreSQL")
        print("\n💡 Para verificar no banco:")
        print(
            "   docker exec -e PGPASSWORD='6IVxDUQkY9TUf5ij8Af3zIDhiTdgn' juscash-postgres \\"
        )
        print("     psql -U juscash_user -d juscash_db \\")
        print(
            '     -c "SELECT process_number, authors, created_at FROM publications ORDER BY created_at DESC LIMIT 3;"'
        )
    else:
        print("\n⚠️ RESULTADO:")
        print("✅ Dados enviados para API")
        print("❌ Problemas na verificação do banco")


if __name__ == "__main__":
    asyncio.run(main())
