"""
Script para debugar dados enviados para a API
"""

import json
from datetime import datetime
from src.domain.entities.publication import Publication, Lawyer, MonetaryValue


def debug_api_data():
    """Debug dos dados enviados para a API"""

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

    print("🔍 DEBUG: Dados enviados para a API")
    print("=" * 50)
    print(json.dumps(api_data, indent=2, ensure_ascii=False, default=str))
    print("=" * 50)

    # Verificar tipos dos campos problemáticos
    print("\n🔍 DEBUG: Tipos dos campos")
    print(
        f"publicationDate: {type(api_data.get('publicationDate'))} = {api_data.get('publicationDate')}"
    )
    print(
        f"availability_date: {type(api_data.get('availability_date'))} = {api_data.get('availability_date')}"
    )
    print(f"authors: {type(api_data.get('authors'))} = {api_data.get('authors')}")
    print(f"lawyers: {type(api_data.get('lawyers'))} = {api_data.get('lawyers')}")

    # Verificar se as datas estão no formato ISO correto
    print("\n🔍 DEBUG: Formato das datas")
    if api_data.get("publicationDate"):
        try:
            datetime.fromisoformat(api_data["publicationDate"].replace("Z", "+00:00"))
            print("✅ publicationDate está em formato ISO válido")
        except Exception as e:
            print(f"❌ publicationDate formato inválido: {e}")

    if api_data.get("availability_date"):
        try:
            datetime.fromisoformat(api_data["availability_date"].replace("Z", "+00:00"))
            print("✅ availability_date está em formato ISO válido")
        except Exception as e:
            print(f"❌ availability_date formato inválido: {e}")


if __name__ == "__main__":
    debug_api_data()
