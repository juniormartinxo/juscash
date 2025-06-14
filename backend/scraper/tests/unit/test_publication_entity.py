"""
Testes unitários para entidade Publication
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.domain.entities.publication import Publication, Lawyer, MonetaryValue


class TestMonetaryValue:
    """Testes para MonetaryValue"""

    def test_from_real_conversion(self):
        """Testa conversão de real para centavos"""
        value = MonetaryValue.from_real(Decimal("1500.50"))
        assert value.amount_cents == 150050

    def test_to_real_conversion(self):
        """Testa conversão de centavos para real"""
        value = MonetaryValue(amount_cents=150050)
        assert value.to_real() == Decimal("1500.50")

    def test_zero_value(self):
        """Testa valor zero"""
        value = MonetaryValue.from_real(Decimal("0"))
        assert value.amount_cents == 0
        assert value.to_real() == Decimal("0")


class TestPublication:
    """Testes para Publication"""

    def test_publication_creation(self, sample_publication):
        """Testa criação de publicação válida"""
        assert sample_publication.process_number == "1234567-89.2024.8.26.0100"
        assert len(sample_publication.authors) == 2
        assert (
            sample_publication.defendant == "Instituto Nacional do Seguro Social - INSS"
        )

    def test_publication_validation_empty_process_number(self):
        """Testa validação com número de processo vazio"""
        with pytest.raises(ValueError, match="Número do processo é obrigatório"):
            Publication(
                process_number="",
                availability_date=datetime.now(),
                authors=["Test Author"],
                content="Test content",
            )

    def test_publication_validation_empty_authors(self):
        """Testa validação com lista de autores vazia"""
        with pytest.raises(ValueError, match="Pelo menos um autor é obrigatório"):
            Publication(
                process_number="1234567-89.2024.8.26.0100",
                availability_date=datetime.now(),
                authors=[],
                content="Test content",
            )

    def test_publication_validation_empty_content(self):
        """Testa validação com conteúdo vazio"""
        with pytest.raises(ValueError, match="Conteúdo da publicação é obrigatório"):
            Publication(
                process_number="1234567-89.2024.8.26.0100",
                availability_date=datetime.now(),
                authors=["Test Author"],
                content="",
            )

    def test_to_api_dict(self, sample_publication):
        """Testa conversão para dicionário da API"""
        api_dict = sample_publication.to_api_dict()

        assert api_dict["processNumber"] == sample_publication.process_number
        assert api_dict["authors"] == sample_publication.authors
        assert api_dict["defendant"] == sample_publication.defendant
        assert api_dict["grossValue"] == 150000  # R$ 1500.00 em centavos
        assert len(api_dict["lawyers"]) == 2
        assert api_dict["lawyers"][0]["name"] == "Dr. Carlos Advogado"
