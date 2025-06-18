"""
Testes unitários para PublicationValidator
"""

import pytest

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from domain.services.publication_validator import PublicationValidator


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
        """Testa verificação de termos obrigatórios (pelo menos um)"""
        content = (
            "Este processo trata de aposentadoria por invalidez do benefício do INSS"
        )
        required_terms = ["aposentadoria", "benefício"]

        assert validator.contains_required_terms(content, required_terms)

    def test_contains_required_terms_partial(self, validator):
        """Testa verificação com apenas um termo presente"""
        content = "Este processo trata de aposentadoria"
        required_terms = ["aposentadoria", "benefício"]

        # Agora deve retornar True pois pelo menos um termo está presente
        assert validator.contains_required_terms(content, required_terms)

    def test_contains_required_terms_none_present(self, validator):
        """Testa verificação quando nenhum termo está presente"""
        content = "Este processo trata de outras questões jurídicas"
        required_terms = ["aposentadoria", "benefício"]

        # Deve retornar False pois nenhum termo está presente
        assert not validator.contains_required_terms(content, required_terms)

    def test_validate_publication_complete(self, validator, sample_publication):
        """Testa validação completa de publicação"""
        required_terms = ["aposentadoria", "benefício"]

        from domain.entities.publication import Publication, MonetaryValue
        from datetime import datetime

        valid_publication = Publication(
            process_number=sample_publication.process_number,
            publication_date=sample_publication.publication_date,
            availability_date=sample_publication.availability_date,
            authors=sample_publication.authors,
            content=sample_publication.content
            + " aposentadoria",  # Apenas um termo é suficiente agora
            gross_value=sample_publication.gross_value,
        )

        is_valid, error_message = validator.validate_publication(
            valid_publication, required_terms
        )
        assert is_valid, f"Validação falhou: {error_message}"

    def test_validate_publication_invalid_process_number(
        self, validator, sample_publication
    ):
        """Testa validação com número de processo inválido"""
        # Como a entidade Publication também valida o número do processo na criação,
        # usamos um mock para testar o validador
        from unittest.mock import Mock

        mock_publication = Mock()
        mock_publication.process_number = "123-invalid"
        mock_publication.publication_date = sample_publication.publication_date
        mock_publication.availability_date = sample_publication.availability_date
        mock_publication.authors = sample_publication.authors
        mock_publication.content = sample_publication.content
        mock_publication.gross_value = sample_publication.gross_value

        required_terms = ["aposentadoria"]

        is_valid, error_message = validator.validate_publication(
            mock_publication, required_terms
        )
        assert not is_valid
        assert "Número do processo inválido" in error_message

    def test_validate_publication_missing_terms(self, validator, sample_publication):
        """Testa validação com termos obrigatórios ausentes"""
        required_terms = ["termo_inexistente", "outro_termo"]

        is_valid, error_message = validator.validate_publication(
            sample_publication, required_terms
        )
        assert not is_valid
        assert "Nenhum dos termos obrigatórios encontrado" in error_message

    def test_validate_publication_empty_authors(self, validator, sample_publication):
        """Testa validação com autores vazios"""
        # Como a entidade Publication não permite autores vazios na criação,
        # este teste verifica se o validador detectaria o problema
        # se uma publicação com autores vazios chegasse até ele

        # Simular uma publicação que de alguma forma passou pela validação da entidade
        # mas tem autores vazios (cenário hipotético para teste do validador)
        from unittest.mock import Mock

        mock_publication = Mock()
        mock_publication.process_number = sample_publication.process_number
        mock_publication.publication_date = sample_publication.publication_date
        mock_publication.availability_date = sample_publication.availability_date
        mock_publication.authors = []
        mock_publication.content = sample_publication.content
        mock_publication.gross_value = sample_publication.gross_value

        required_terms = []

        is_valid, error_message = validator.validate_publication(
            mock_publication, required_terms
        )
        assert not is_valid
        assert "Campo 'authors' está vazio" in error_message

    def test_validate_publication_empty_content(self, validator, sample_publication):
        """Testa validação com conteúdo vazio"""
        # Como a entidade Publication não permite conteúdo vazio na criação,
        # usamos um mock para testar o validador
        from unittest.mock import Mock

        mock_publication = Mock()
        mock_publication.process_number = sample_publication.process_number
        mock_publication.publication_date = sample_publication.publication_date
        mock_publication.availability_date = sample_publication.availability_date
        mock_publication.authors = sample_publication.authors
        mock_publication.content = ""
        mock_publication.gross_value = sample_publication.gross_value

        required_terms = []

        is_valid, error_message = validator.validate_publication(
            mock_publication, required_terms
        )
        assert not is_valid
        assert "Campo 'content' está vazio" in error_message
