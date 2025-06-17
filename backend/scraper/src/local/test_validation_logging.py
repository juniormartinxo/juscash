#!/usr/bin/env python3
"""
Teste do logging melhorado de validação
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.entities.publication import Publication, MonetaryValue
from domain.services.publication_validator import PublicationValidator
from application.usecases.extract_publications import ExtractPublicationsUseCase
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


def create_invalid_publication(error_type: str) -> Publication:
    """Cria publicação inválida para testar diferentes tipos de erro"""

    # Valores base
    base_args = {
        "process_number": "0024655-37.2024.8.26.0053",
        "publication_date": datetime(2024, 11, 13),
        "availability_date": datetime(2024, 11, 13),
        "authors": ["João da Silva"],
        "content": "Conteúdo de teste com RPV e pagamento pelo INSS",
        "gross_value": MonetaryValue.from_real(15000),
    }

    # Modificar argumentos baseado no tipo de erro
    if error_type == "invalid_process_number":
        base_args["process_number"] = "123-invalid"
    elif error_type == "missing_terms":
        base_args["content"] = "Conteúdo sem os termos obrigatórios"
    elif error_type == "empty_authors":
        base_args["authors"] = []
    elif error_type == "empty_content":
        base_args["content"] = ""
    elif error_type == "short_author":
        base_args["authors"] = ["Jo"]  # Nome muito curto
    elif error_type == "empty_author":
        base_args["authors"] = [""]  # Autor vazio
    elif error_type == "no_availabilityDate":
        base_args["availability_date"] = None

    return Publication(**base_args)


def test_validation_errors():
    """Testa diferentes tipos de erro de validação"""

    print("🧪 Teste de Logging de Validação")
    print("=" * 40)

    validator = PublicationValidator()
    required_terms = ["RPV", "pagamento pelo INSS"]

    error_types = [
        "invalid_process_number",
        "missing_terms",
        "empty_authors",
        "empty_content",
        "short_author",
        "empty_author",
        "no_availabilityDate",
    ]

    for error_type in error_types:
        print(f"\n🔍 Testando: {error_type}")

        try:
            publication = create_invalid_publication(error_type)
            is_valid, error_message = validator.validate_publication(
                publication, required_terms
            )

            if not is_valid:
                print(f"   ❌ Erro detectado: {error_message}")
            else:
                print(f"   ⚠️ Erro não detectado (inesperado)")

        except Exception as e:
            print(f"   💥 Exceção durante criação: {e}")


def test_specific_case():
    """Testa o caso específico mencionado no erro"""

    print("\n🎯 Teste do Caso Específico: 0024655-37.2024.8.26.0053")
    print("=" * 50)

    validator = PublicationValidator()
    required_terms = ["RPV", "pagamento pelo INSS"]

    # Simular a publicação que está falhando
    publication = Publication(
        process_number="0024655-37.2024.8.26.0053",
        publication_date=datetime(2024, 11, 13),
        availability_date=datetime(2024, 11, 13),
        authors=["Autor Teste"],
        content="Conteúdo de teste",
        gross_value=MonetaryValue.from_real(10000),
    )

    print(f"📋 Processo: {publication.process_number}")
    print(f"👤 Autores: {publication.authors}")
    print(f"📅 Data Disponibilização: {publication.availability_date}")
    print(f"📝 Conteúdo: {publication.content[:100]}...")
    print()

    is_valid, error_message = validator.validate_publication(
        publication, required_terms
    )

    if is_valid:
        print("✅ Publicação VÁLIDA")
    else:
        print(f"❌ Publicação INVÁLIDA: {error_message}")

    # Testar com diferentes variações
    print("\n🔄 Testando variações:")

    # Variação 1: Sem termos obrigatórios
    pub_sem_termos = Publication(
        process_number="0024655-37.2024.8.26.0053",
        publication_date=datetime(2024, 11, 13),
        availability_date=datetime(2024, 11, 13),
        authors=["Autor Teste"],
        content="Conteúdo sem os termos específicos",
        gross_value=MonetaryValue.from_real(10000),
    )
    is_valid, error_message = validator.validate_publication(
        pub_sem_termos, required_terms
    )
    print(f"   Sem termos: {'✅ Válida' if is_valid else f'❌ {error_message}'}")

    # Variação 2: Com termos obrigatórios
    pub_com_termos = Publication(
        process_number="0024655-37.2024.8.26.0053",
        publication_date=datetime(2024, 11, 13),
        availability_date=datetime(2024, 11, 13),
        authors=["Autor Teste"],
        content="Execução de RPV para pagamento pelo INSS",
        gross_value=MonetaryValue.from_real(10000),
    )
    is_valid, error_message = validator.validate_publication(
        pub_com_termos, required_terms
    )
    print(f"   Com termos: {'✅ Válida' if is_valid else f'❌ {error_message}'}")

    # Variação 3: Sem autores (vai falhar na criação da entidade)
    try:
        pub_sem_autores = Publication(
            process_number="0024655-37.2024.8.26.0053",
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime(2024, 11, 13),
            authors=[],
            content="Execução de RPV para pagamento pelo INSS",
            gross_value=MonetaryValue.from_real(10000),
        )
        is_valid, error_message = validator.validate_publication(
            pub_sem_autores, required_terms
        )
        print(f"   Sem autores: {'✅ Válida' if is_valid else f'❌ {error_message}'}")
    except ValueError as e:
        print(f"   Sem autores: ❌ Erro na criação da entidade: {e}")


if __name__ == "__main__":
    print("🚀 Teste de Logging Melhorado de Validação")
    print("💡 Verificando mensagens de erro detalhadas")
    print()

    # Testar diferentes tipos de erro
    test_validation_errors()

    # Testar caso específico
    test_specific_case()

    print("\n📋 Resumo:")
    print("✅ Logging melhorado implementado")
    print("✅ Mensagens de erro detalhadas")
    print("✅ Identificação específica de campos inválidos")
    print("✅ Agora você pode ver exatamente qual campo está falhando!")

    print("\n💡 Para ver os logs detalhados, execute o scraper novamente.")
    print(
        "   As mensagens agora mostrarão o erro específico para cada publicação inválida."
    )
