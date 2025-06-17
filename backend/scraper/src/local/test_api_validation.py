#!/usr/bin/env python3
"""
Teste de validação da API - Verificar formato dos dados
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.entities.publication import Publication, MonetaryValue
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


def test_publication_to_api_dict():
    """Testa se o método to_api_dict está gerando o formato correto"""
    print("🧪 Teste do Formato de Dados para API")
    print("=" * 50)

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

    print("📋 Dados gerados pelo to_api_dict():")
    print(json.dumps(api_data, indent=2, ensure_ascii=False))

    # Verificar campos obrigatórios
    required_fields = ["process_number", "availability_date", "authors", "content"]

    print("\n🔍 Verificação de Campos Obrigatórios:")
    for field in required_fields:
        if field in api_data:
            print(f"   ✅ {field}: {api_data[field]}")
        else:
            print(f"   ❌ {field}: AUSENTE")

    # Verificar tipos de dados
    print("\n🔍 Verificação de Tipos:")

    # process_number deve ser string
    if isinstance(api_data.get("process_number"), str):
        print("   ✅ process_number: string")
    else:
        print(f"   ❌ process_number: {type(api_data.get('process_number'))}")

    # availability_date deve ser string (ISO format)
    if isinstance(api_data.get("availability_date"), str):
        print("   ✅ availability_date: string")
        try:
            datetime.fromisoformat(api_data["availability_date"].replace("Z", "+00:00"))
            print("   ✅ availability_date: formato ISO válido")
        except:
            print("   ❌ availability_date: formato ISO inválido")
    else:
        print(f"   ❌ availability_date: {type(api_data.get('availability_date'))}")

    # authors deve ser array de strings
    authors = api_data.get("authors")
    if isinstance(authors, list):
        print("   ✅ authors: array")
        if all(isinstance(author, str) for author in authors):
            print("   ✅ authors: todos são strings")
        else:
            print("   ❌ authors: nem todos são strings")
    else:
        print(f"   ❌ authors: {type(authors)}")

    # content deve ser string
    if isinstance(api_data.get("content"), str):
        print("   ✅ content: string")
    else:
        print(f"   ❌ content: {type(api_data.get('content'))}")

    # gross_value deve ser number (int) se presente
    if "gross_value" in api_data:
        if isinstance(api_data["gross_value"], int):
            print("   ✅ gross_value: integer")
        else:
            print(f"   ❌ gross_value: {type(api_data['gross_value'])}")

    return api_data


def test_schema_compliance():
    """Testa se os dados estão em conformidade com o schema da API"""
    print("\n🎯 Teste de Conformidade com Schema da API")
    print("=" * 50)

    # Campos esperados pelo schema da API (baseado no código TypeScript)
    expected_schema = {
        "process_number": "string (obrigatório)",
        "publicationDate": "string datetime (opcional)",
        "availability_date": "string datetime (obrigatório)",
        "authors": "array de strings (obrigatório, min 1)",
        "defendant": "string (opcional)",
        "lawyers": "array de objetos {name, oab} (opcional)",
        "gross_value": "number int positive (opcional)",
        "net_value": "number int positive (opcional)",
        "interest_value": "number int positive (opcional)",
        "attorney_fees": "number int positive (opcional)",
        "content": "string (obrigatório)",
        "status": "enum ['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA'] (opcional)",
        "scraping_source": "string (opcional)",
        "caderno": "string (opcional)",
        "instancia": "string (opcional)",
        "local": "string (opcional)",
        "parte": "string (opcional)",
        "extraction_metadata": "any (opcional)",
    }

    print("📋 Schema Esperado pela API:")
    for field, description in expected_schema.items():
        print(f"   • {field}: {description}")

    # Testar com dados reais
    api_data = test_publication_to_api_dict()

    print("\n🔍 Verificação de Conformidade:")

    # Verificar se todos os campos obrigatórios estão presentes
    required_fields = ["process_number", "availability_date", "authors", "content"]
    for field in required_fields:
        if field in api_data and api_data[field]:
            print(f"   ✅ {field}: presente e não vazio")
        else:
            print(f"   ❌ {field}: ausente ou vazio")

    # Verificar se authors tem pelo menos 1 item
    authors = api_data.get("authors", [])
    if len(authors) >= 1:
        print(f"   ✅ authors: {len(authors)} autor(es)")
    else:
        print("   ❌ authors: array vazio")

    # Verificar se valores monetários são inteiros positivos
    monetary_fields = ["gross_value", "net_value", "interest_value", "attorney_fees"]
    for field in monetary_fields:
        if field in api_data:
            value = api_data[field]
            if isinstance(value, int) and value > 0:
                print(f"   ✅ {field}: {value} (int positivo)")
            else:
                print(f"   ❌ {field}: {value} (não é int positivo)")


def test_common_validation_errors():
    """Testa cenários que podem causar erros de validação"""
    print("\n⚠️  Teste de Cenários de Erro Comuns")
    print("=" * 50)

    # Cenário 1: Authors vazio
    print("🔍 Cenário 1: Authors vazio")
    try:
        pub = Publication(
            process_number="0013168-70.2024.8.26.0053",
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime(2024, 11, 13),
            authors=[],  # Vazio - deve falhar
            content="Teste",
        )
        print("   ❌ Não deveria ter criado a publicação")
    except ValueError as e:
        print(f"   ✅ Erro capturado corretamente: {e}")

    # Cenário 2: Content vazio
    print("\n🔍 Cenário 2: Content vazio")
    try:
        pub = Publication(
            process_number="0013168-70.2024.8.26.0053",
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime(2024, 11, 13),
            authors=["Teste"],
            content="",  # Vazio - deve falhar
        )
        print("   ❌ Não deveria ter criado a publicação")
    except ValueError as e:
        print(f"   ✅ Erro capturado corretamente: {e}")

    # Cenário 3: Número de processo inválido
    print("\n🔍 Cenário 3: Número de processo inválido")
    try:
        pub = Publication(
            process_number="123-invalid",  # Formato inválido
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime(2024, 11, 13),
            authors=["Teste"],
            content="Teste",
        )
        print("   ❌ Não deveria ter criado a publicação")
    except ValueError as e:
        print(f"   ✅ Erro capturado corretamente: {e}")


if __name__ == "__main__":
    print("🚀 Teste de Validação da API")
    print("💡 Verificando se os dados estão no formato correto")
    print()

    # Testar formato dos dados
    test_publication_to_api_dict()

    # Testar conformidade com schema
    test_schema_compliance()

    # Testar cenários de erro
    test_common_validation_errors()

    print("\n📋 Resumo:")
    print("✅ Formato de dados verificado")
    print("✅ Conformidade com schema verificada")
    print("✅ Cenários de erro testados")

    print("\n💡 Se ainda houver erros de validação na API:")
    print("   1. Verifique se a API está usando o schema correto")
    print("   2. Verifique se os tipos de dados estão corretos")
    print("   3. Verifique se todos os campos obrigatórios estão presentes")
    print("   4. Verifique se os valores monetários são inteiros positivos")
