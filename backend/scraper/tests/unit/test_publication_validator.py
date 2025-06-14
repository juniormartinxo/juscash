"""
Testes unitários para PublicationValidator
"""

import pytest

from src.domain.services.publication_validator import PublicationValidator


class TestPublicationValidator:
    """Testes para validador de publicações"""

    @pytest.fixture
    def validator(self):
        return PublicationValidator()

    def test_validate_process_number_valid(self, validator):
        """Testa validação de número de processo válido"""
        valid_numbers = [
            "1234567-89.2024.8.26.0100",
            "0001234-12.2023.1.26.0001",
            "9999999-99.2024.5.01.9999",
        ]

        for number in valid_numbers:
            assert validator.validate_process_number(number)

    def test_validate_process_number_invalid(self, validator):
        """Testa validação de número de processo inválido"""
        invalid_numbers = [
            "123456-89.2024.8.26.0100",  # 6 dígitos em vez de 7
            "1234567-9.2024.8.26.0100",  # 1 dígito em vez de 2
            "1234567-89.24.8.26.0100",  # 2 dígitos em vez de 4
            "1234567-89.2024.8.260.0100",  # 3 dígitos em vez de 2
            "abcdefg-89.2024.8.26.0100",  # Letras em vez de números
            "1234567-89.2024.8.26",  # Formato incompleto
        ]

        for number in invalid_numbers:
            assert not validator.validate_process_number(number)

    def test_contains_required_terms(self, validator):
        """Testa verificação de termos obrigatórios"""
        content = (
            "Este processo trata de aposentadoria por invalidez do benefício do INSS"
        )
        required_terms = ["aposentadoria", "benefício"]

        assert validator.contains_required_terms(content, required_terms)

    def test_contains_required_terms_missing(self, validator):
        """Testa verificação com termos faltando"""
        content = "Este processo trata de aposentadoria"
        required_terms = ["aposentadoria", "benefício"]

        assert not validator.contains_required_terms(content, required_terms)

    def test_validate_publication_complete(self, validator, sample_publication):
        """Testa validação completa de publicação"""
        required_terms = ["aposentadoria", "benefício"]

        # Adicionar termos ao conteúdo para passar na validação
        sample_publication.content += " aposentadoria benefício"

        assert validator.validate_publication(sample_publication, required_terms)
