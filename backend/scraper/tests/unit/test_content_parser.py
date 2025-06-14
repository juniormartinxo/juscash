"""
Testes unitários para DJEContentParser
"""

import pytest
from datetime import datetime

from src.infrastructure.web.content_parser import DJEContentParser


class TestDJEContentParser:
    """Testes para parser de conteúdo"""

    @pytest.fixture
    def parser(self):
        return DJEContentParser()

    def test_extract_process_number(self, parser, sample_content_dje):
        """Testa extração de número do processo"""
        result = parser._extract_process_number(sample_content_dje)
        assert result == "1234567-89.2024.8.26.0100"

    def test_extract_authors(self, parser, sample_content_dje):
        """Testa extração de autores"""
        result = parser._extract_authors(sample_content_dje)
        assert "João Silva Santos" in result
        assert len(result) >= 1

    def test_extract_lawyers(self, parser, sample_content_dje):
        """Testa extração de advogados"""
        result = parser._extract_lawyers(sample_content_dje)
        assert len(result) >= 1
        assert result[0].name == "Dr. Carlos Advogado"
        assert result[0].oab == "123456"

    def test_extract_monetary_values(self, parser, sample_content_dje):
        """Testa extração de valores monetários"""
        result = parser._extract_all_monetary_values(sample_content_dje)

        assert result["gross"] is not None
        assert result["gross"].to_real() == 1500.00

        assert result["net"] is not None
        assert result["net"].to_real() == 1350.00

    def test_parse_publication_complete(self, parser, sample_content_dje):
        """Testa parsing completo de publicação"""
        result = parser.parse_publication(sample_content_dje, "https://test.url")

        assert result is not None
        assert result.process_number == "1234567-89.2024.8.26.0100"
        assert len(result.authors) >= 1
        assert result.gross_value is not None
        assert result.extraction_metadata["confidence_score"] > 0.7

    def test_parse_invalid_content(self, parser):
        """Testa parsing de conteúdo inválido"""
        invalid_content = "Conteúdo sem informações válidas"
        result = parser.parse_publication(invalid_content)

        assert result is None
