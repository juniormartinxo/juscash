import pytest
from datetime import datetime
from decimal import Decimal

from src.core.entities.publication import Publication
from src.shared.value_objects import process_number, Status


class TestPublication:
    """Testes unitários para a entidade Publication."""

    def test_create_publication_with_valid_data(self, sample_publication):
        """Testa criação de publicação com dados válidos."""
        assert sample_publication.id is not None
        assert sample_publication.status == Status.NEW
        assert sample_publication.defendant == "Instituto Nacional do Seguro Social - INSS"
        assert len(sample_publication.authors) == 2
        assert sample_publication.gross_value == Decimal("15000.50")

    def test_publication_validation_removes_empty_authors(self):
        """Testa que autores vazios são removidos."""
        publication = Publication(
            authors=["João Silva", "", "   ", "Maria Santos", "João Silva"],  # Duplicata e vazios
            content="Teste"
        )

        assert len(publication.authors) == 2
        assert "João Silva" in publication.authors
        assert "Maria Santos" in publication.authors
        assert "" not in publication.authors

    def test_publication_validation_removes_negative_values(self):
        """Testa que valores negativos são convertidos para None."""
        publication = Publication(
            gross_value=Decimal("-1000.00"),
            net_value=Decimal("2000.00"),
            interest_value=Decimal("-500.00")
        )

        assert publication.gross_value is None
        assert publication.net_value == Decimal("2000.00")
        assert publication.interest_value is None

    def test_update_status(self, sample_publication):
        """Testa atualização de status."""
        old_updated_at = sample_publication.updated_at

        sample_publication.update_status(Status.READ)

        assert sample_publication.status == Status.READ
        assert sample_publication.updated_at > old_updated_at

    def test_has_required_search_terms(self, sample_publication):
        """Testa verificação de termos obrigatórios."""
        assert sample_publication.has_required_search_terms(["INSS", "Instituto"])
        assert not sample_publication.has_required_search_terms(["termo_inexistente"])
        assert not sample_publication.has_required_search_terms([])

    def test_is_valid_for_processing(self):
        """Testa validação para processamento."""
        # Publicação válida
        valid_pub = Publication(
            process_number=process_number("1234567-89.2024.8.26.0100"),
            content="Conteúdo válido com texto suficiente",
        )
        assert valid_pub.is_valid_for_processing()

        # Publicação inválida - sem número do processo
        invalid_pub1 = Publication(content="Conteúdo")
        assert not invalid_pub1.is_valid_for_processing()

        # Publicação inválida - sem conteúdo
        invalid_pub2 = Publication(
            process_number=process_number("1234567-89.2024.8.26.0100")
        )
        assert not invalid_pub2.is_valid_for_processing()

    def test_to_dict(self, sample_publication):
        """Testa conversão para dicionário."""
        data = sample_publication.to_dict()

        assert isinstance(data, dict)
        assert data['status'] == 'nova'
        assert data['defendant'] == 'Instituto Nacional do Seguro Social - INSS'
        assert len(data['authors']) == 2
        assert data['gross_value'] == '15000.50'
