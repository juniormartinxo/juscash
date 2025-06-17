import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.adapters.secondary.playwright_scraper import PlaywrightScraperAdapter
from src.adapters.secondary.sqlalchemy_repository import SQLAlchemyRepository, PublicationModel
from src.shared.value_objects import DJEUrl, ScrapingCriteria


@pytest.mark.unit
class TestPlaywrightScraperAdapter:
    """Testes unitários para o adaptador Playwright."""

    @patch('src.adapters.secondary.playwright_scraper.async_playwright')
    async def test_initialize_success(self, mock_playwright):
        """Testa inicialização bem-sucedida do Playwright."""
        # Configurar mocks
        mock_pw = AsyncMock()
        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = AsyncMock()

        # Executar
        scraper = PlaywrightScraperAdapter()
        await scraper.initialize()

        # Verificar
        assert scraper.playwright is not None
        mock_pw.chromium.launch.assert_called_once()

    async def test_navigate_to_dje(self, mock_playwright_page):
        """Testa navegação para DJE."""
        scraper = PlaywrightScraperAdapter()
        scraper.page = mock_playwright_page

        # Configurar mock
        mock_playwright_page.goto.return_value = MagicMock(status=200)
        mock_playwright_page.title.return_value = "DJE - Diário da Justiça"

        # Executar
        dje_url = DJEUrl()
        result = await scraper.navigate_to_dje(dje_url)

        # Verificar
        assert result is True
        mock_playwright_page.goto.assert_called_once_with(
            dje_url.get_main_url(),
            wait_until='networkidle'
        )

    async def test_extract_basic_info_from_content(self):
        """Testa extração de informações básicas do conteúdo."""
        scraper = PlaywrightScraperAdapter()

        content = """
        Processo nº 1234567-89.2024.8.26.0100
        Data de disponibilização: 15/03/2024
        Autor: João da Silva
        Advogado: Dr. Carlos Alberto - OAB/SP 123456
        Valor principal: R$ 15.000,50
        Juros moratórios: R$ 2.500,25
        """

        publication = Publication()
        await scraper._extract_basic_info(publication, content)

        # Verificar extrações
        assert str(publication.process_number) == "1234567-89.2024.8.26.0100"
        assert publication.availability_date.date() == datetime(2024, 3, 15).date()
        assert "João da Silva" in publication.authors
        assert "Dr. Carlos Alberto - OAB/SP 123456" in publication.lawyers


@pytest.mark.unit  
class TestSQLAlchemyRepository:
    """Testes unitários para o repositório SQLAlchemy."""
    
    def test_publication_model_to_entity(self, sample_publication):
        """Testa conversão de modelo para entidade."""
        # Criar modelo
        model = PublicationModel.from_entity(sample_publication)
        
        # Converter de volta para entidade
        entity = model.to_entity()
        
        # Verificar
        assert entity.id == sample_publication.id
        assert str(entity.process_number) == str(sample_publication.process_number)
        assert entity.status == sample_publication.status
        assert entity.defendant == sample_publication.defendant
    
    def test_publication_model_from_entity(self, sample_publication):
        """Testa conversão de entidade para modelo."""
        model = PublicationModel.from_entity(sample_publication)
        
        assert model.id == sample_publication.id
        assert model.process_number == str(sample_publication.process_number)
        assert model.status == sample_publication.status.value
        assert model.defendant == sample_publication.defendant
        assert model.authors == sample_publication.authors
        assert model.gross_value == sample_publication.gross_value
