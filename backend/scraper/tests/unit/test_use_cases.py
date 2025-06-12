import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.core.usecases.scrape_publications import ScrapePublicationsUseCase
from src.core.usecases.schedule_scraping import ScheduleScrapingUseCase
from src.shared.exceptions import DJEScrapingException


@pytest.mark.unit
class TestScrapePublicationsUseCase:
    """Testes unitários para o caso de uso de scraping."""
    
    async def test_execute_success(self, mock_scraper, mock_database, sample_criteria, sample_publication):
        """Testa execução bem-sucedida do scraping."""
        # Configurar mocks
        mock_scraper.extract_publications.return_value = [sample_publication]
        mock_scraper.extract_publication_details.return_value = sample_publication
        mock_database.exists_by_process_number.return_value = False
        mock_database.save_publication.return_value = sample_publication
        
        # Executar
        use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )
        
        stats = await use_case.execute(criteria=sample_criteria)
        
        # Verificar resultado
        assert stats['publications_found'] == 1
        assert stats['publications_new'] == 1
        assert stats['publications_duplicated'] == 0
        assert stats['publications_failed'] == 0
        assert 'started_at' in stats
        assert 'finished_at' in stats
    
    async def test_execute_with_duplicates(self, mock_scraper, mock_database, sample_criteria, sample_publication):
        """Testa execução com publicações duplicadas."""
        # Configurar mocks para detectar duplicata
        mock_scraper.extract_publications.return_value = [sample_publication]
        mock_scraper.extract_publication_details.return_value = sample_publication
        mock_database.exists_by_process_number.return_value = True  # Já existe
        
        # Executar
        use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )
        
        stats = await use_case.execute(criteria=sample_criteria, skip_duplicates=True)
        
        # Verificar que duplicata foi ignorada
        assert stats['publications_found'] == 1
        assert stats['publications_new'] == 0
        assert stats['publications_duplicated'] == 1
        mock_database.save_publication.assert_not_called()
    
    async def test_execute_handles_scraper_error(self, mock_scraper, mock_database, sample_criteria):
        """Testa tratamento de erro no scraper."""
        # Configurar mock para falhar
        mock_scraper.navigate_to_dje.side_effect = DJEScrapingException("Erro de navegação")
        
        # Executar e verificar que erro é propagado
        use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )
        
        with pytest.raises(DJEScrapingException):
            await use_case.execute(criteria=sample_criteria)
        
        # Verificar que scraper foi fechado mesmo com erro
        mock_scraper.close.assert_called_once()


@pytest.mark.unit
class TestScheduleScrapingUseCase:
    """Testes unitários para o caso de uso de agendamento."""
    
    async def test_setup_daily_execution(self, mock_database, mock_scraper):
        """Testa configuração de execução diária."""
        # Criar mocks
        mock_scheduler = AsyncMock()
        mock_scheduler.schedule_daily_scraping.return_value = "job_123"
        
        scrape_use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )
        
        # Executar
        schedule_use_case = ScheduleScrapingUseCase(
            scheduler=mock_scheduler,
            scrape_use_case=scrape_use_case
        )
        
        job_id = await schedule_use_case.setup_daily_execution()
        
        # Verificar
        assert job_id == "job_123"
        mock_scheduler.initialize.assert_called_once()
        mock_scheduler.schedule_daily_scraping.assert_called_once()
    
    async def test_schedule_immediate_execution(self, mock_database, mock_scraper):
        """Testa agendamento de execução imediata."""
        # Criar mocks
        mock_scheduler = AsyncMock()
        mock_scheduler.schedule_one_time_execution.return_value = "immediate_job_456"
        
        scrape_use_case = ScrapePublicationsUseCase(
            scraper=mock_scraper,
            database=mock_database
        )
        
        # Executar
        schedule_use_case = ScheduleScrapingUseCase(
            scheduler=mock_scheduler,
            scrape_use_case=scrape_use_case
        )
        
        job_id = await schedule_use_case.schedule_immediate_execution()
        
        # Verificar
        assert job_id == "immediate_job_456"
        mock_scheduler.schedule_one_time_execution.assert_called_once()