import pytest
from unittest.mock import AsyncMock, patch

from src.core.usecases.scrape_publications import ScrapePublicationsUseCase
from src.shared.value_objects import ScrapingCriteria


@pytest.mark.integration
class TestScrapingIntegration:
    """Testes de integração para o sistema de scraping."""

    async def test_full_scraping_workflow(self, mock_scraper, mock_database, sample_criteria):
        """Testa workflow completo de scraping."""
        # Configurar mocks
        sample_publications = [
            {"process": "1234567-89.2024.8.26.0100", "content": "Teste INSS Instituto"},
            {"process": "7654321-98.2024.8.26.0100", "content": "Outro teste INSS Instituto"}
        ]

        mock_scraper.extract_publications.return_value = [
            Publication(
                process_number=process_number(pub["process"]), content=pub["content"]
            )
            for pub in sample_publications
        ]

        mock_scraper.extract_publication_details.side_effect = lambda pub: pub

        # Executar caso de uso
        use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )

        stats = await use_case.execute(criteria=sample_criteria)

        # Verificar chamadas
        mock_scraper.initialize.assert_called_once()
        mock_scraper.navigate_to_dje.assert_called_once()
        mock_scraper.navigate_to_caderno.assert_called_once_with(sample_criteria)
        mock_scraper.extract_publications.assert_called_once()
        mock_scraper.close.assert_called_once()

        # Verificar estatísticas
        assert stats['publications_found'] == 2
        assert stats['publications_saved'] == 2
        assert len(stats['errors']) == 0
