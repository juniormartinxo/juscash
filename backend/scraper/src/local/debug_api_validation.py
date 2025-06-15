#!/usr/bin/env python3
"""
Debug de validação da API - Descobrir por que a validação está falhando
"""

import sys
import json
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.content_parser import DJEContentParser
from infrastructure.api.api_client_adapter import ApiClientAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)

# Conteúdo de teste real do DJE-SP
REAL_DJE_CONTENT = """
Processo 0112165-20.2012.8.26.0050

Publicado em 13 de novembro de 2024

Acidentário - CLAUDIO LUIZ BUENO DE MIRANDA - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS

Condenar o Instituto Nacional do Seguro Social - INSS ao pagamento de:
- Juros monetários: R$ 43.545,51
- Honorários advocatícios: R$ 11.578,51

ADV. MARIA JOSE DA SILVA OLIVEIRA (OAB 123456/SP)

Trata-se de ação previdenciária para concessão de auxílio-doença e aposentadoria.
"""


async def debug_api_validation():
    """Debug da validação da API"""

    print("🔍 Iniciando debug de validação da API")
    print("=" * 60)

    try:
        # 1. Criar publicação com parser
        print("\n📋 Etapa 1: Parsing dos dados")
        parser = DJEContentParser()
        publications = parser.parse_multiple_publications(REAL_DJE_CONTENT)

        if not publications:
            print("❌ Nenhuma publicação extraída")
            return

        publication = publications[0]

        # 2. Verificar dados da publicação
        print(f"✅ Publicação extraída:")
        print(f"   - Processo: {publication.process_number}")
        print(f"   - Data pub: {publication.publication_date}")
        print(f"   - Data disp: {publication.availability_date}")
        print(f"   - Autores: {publication.authors}")
        print(f"   - Advogados: {len(publication.lawyers)}")
        print(f"   - Content length: {len(publication.content)}")

        # 3. Converter para formato da API
        print(f"\n🔄 Etapa 2: Conversão para formato da API")
        api_data = publication.to_api_dict()

        print(f"📤 Dados que serão enviados:")
        print(json.dumps(api_data, indent=2, ensure_ascii=False, default=str))

        # 4. Validar campos obrigatórios específicos
        print(f"\n✅ Etapa 3: Validação de campos obrigatórios")

        required_fields = {
            "processNumber": api_data.get("processNumber"),
            "availabilityDate": api_data.get("availabilityDate"),
            "authors": api_data.get("authors"),
            "content": api_data.get("content"),
        }

        print(f"📋 Campos obrigatórios:")
        for field, value in required_fields.items():
            status = "✅" if value else "❌"
            print(f"   {status} {field}: {value}")

        # 5. Verificar tipos específicos
        print(f"\n🔍 Etapa 4: Validação de tipos")

        validations = []

        # processNumber deve ser string não vazia
        if (
            isinstance(api_data.get("processNumber"), str)
            and api_data.get("processNumber").strip()
        ):
            validations.append("✅ processNumber: string válida")
        else:
            validations.append(
                f"❌ processNumber: {type(api_data.get('processNumber'))} - {api_data.get('processNumber')}"
            )

        # availabilityDate deve ser string datetime
        availability_date = api_data.get("availabilityDate")
        if isinstance(availability_date, str) and availability_date.endswith("Z"):
            validations.append("✅ availabilityDate: formato ISO válido")
        else:
            validations.append(
                f"❌ availabilityDate: {type(availability_date)} - {availability_date}"
            )

        # authors deve ser array não vazio
        authors = api_data.get("authors")
        if (
            isinstance(authors, list)
            and len(authors) > 0
            and all(isinstance(a, str) and a.strip() for a in authors)
        ):
            validations.append(f"✅ authors: array válido com {len(authors)} itens")
        else:
            validations.append(f"❌ authors: {type(authors)} - {authors}")

        # content deve ser string não vazia
        content = api_data.get("content")
        if isinstance(content, str) and content.strip():
            validations.append(f"✅ content: string válida ({len(content)} chars)")
        else:
            validations.append(
                f"❌ content: {type(content)} - {len(content) if content else 'None'}"
            )

        # Verificar valores monetários
        monetary_fields = ["grossValue", "netValue", "interestValue", "attorneyFees"]
        for field in monetary_fields:
            value = api_data.get(field)
            if value is not None:
                if isinstance(value, int) and value > 0:
                    validations.append(f"✅ {field}: {value} (válido)")
                else:
                    validations.append(f"❌ {field}: {type(value)} - {value}")

        # Verificar lawyers
        lawyers = api_data.get("lawyers")
        if lawyers is not None:
            if isinstance(lawyers, list):
                valid_lawyers = True
                for lawyer in lawyers:
                    if (
                        not isinstance(lawyer, dict)
                        or "name" not in lawyer
                        or "oab" not in lawyer
                    ):
                        valid_lawyers = False
                        break
                if valid_lawyers:
                    validations.append(
                        f"✅ lawyers: array válido com {len(lawyers)} itens"
                    )
                else:
                    validations.append(f"❌ lawyers: formato inválido - {lawyers}")
            else:
                validations.append(f"❌ lawyers: deve ser array - {type(lawyers)}")

        for validation in validations:
            print(f"   {validation}")

        # 6. Tentar identificar o problema específico
        print(f"\n🎯 Etapa 5: Identificação do problema")

        # Verificar se há campos com valores None/null quando não deveriam
        problematic_fields = []
        for key, value in api_data.items():
            if value is None and key in required_fields:
                problematic_fields.append(f"{key}: None")
            elif (
                isinstance(value, str) and not value.strip() and key in required_fields
            ):
                problematic_fields.append(f"{key}: string vazia")

        if problematic_fields:
            print(f"❌ Problemas encontrados:")
            for problem in problematic_fields:
                print(f"   - {problem}")
        else:
            print(f"✅ Dados parecem válidos para os campos obrigatórios")

        # 7. Teste de conexão real (opcional)
        print(f"\n🌐 Etapa 6: Teste de conectividade")
        try:
            api_client = ApiClientAdapter()
            exists = await api_client.check_publication_exists("TEST-DEBUG-12345")
            print(f"✅ Conexão com API: OK")
        except Exception as e:
            print(f"⚠️ Problema de conectividade: {e}")

        print(f"\n📊 Resumo:")
        print(f"   - Parser funcionando: ✅")
        print(f"   - Dados extraídos: ✅")
        print(f"   - Conversão API: {'✅' if not problematic_fields else '⚠️'}")
        print(
            f"   - Campos obrigatórios: {'✅' if all(required_fields.values()) else '❌'}"
        )

        return api_data

    except Exception as error:
        print(f"❌ Erro durante debug: {error}")
        logger.error(f"Erro no debug: {error}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(debug_api_validation())
    if result:
        print(f"\n💾 Para teste manual da API, use este JSON:")
        print("-" * 40)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
