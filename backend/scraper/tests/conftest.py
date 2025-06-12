import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from decimal import Decimal

from src.core.entities.publication import Publication
from src.shared.value_objects import ProcessNumber, Status, ScrapingCriteria
from src.config.settings import Settings
from src.adapters.secondary.sqlalchemy_repository import SQLAlchemyRepository
from src.adapters.secondary.redis_cache import RedisCacheAdapter
from src.adapters.secondary.playwright_scraper import PlaywrightScraperAdapter


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Cria loop de eventos para testes assíncronos."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Configurações para testes."""
    settings = Settings()
    settings.database.url = "sqlite+aiosqlite:///:memory:"
    settings.redis.url = "redis://localhost:6379/15"  # DB 15 para testes
    settings.scraping.headless = True
    settings.scraping.timeout = 10000
    settings.logging.level = "DEBUG"
    return settings


@pytest.fixture
def sample_publication() -> Publication:
    """Publicação de exemplo para testes."""
    return Publication(
        process_number=ProcessNumber("1234567-89.2024.8.26.0100"),
        publication_date=datetime(2024, 3, 15),
        availability_date=datetime(2024, 3, 15),
        authors=["João da Silva", "Maria Santos"],
        defendant="Instituto Nacional do Seguro Social - INSS",
        lawyers=["Dr. Carlos Alberto - OAB/SP 123456"],
        gross_value=Decimal("15000.50"),
        net_value=Decimal("12000.00"),
        interest_value=Decimal("2500.25"),
        attorney_fees=Decimal("3000.00"),
        content="Processo nº 1234567-89.2024.8.26.0100. Autor: João da Silva. INSS condenado ao pagamento...",
        status=Status.NEW
    )


@pytest.fixture
def sample_criteria() -> ScrapingCriteria:
    """Critérios de scraping para testes."""
    return ScrapingCriteria(
        required_terms=("Instituto Nacional do Seguro Social", "INSS"),
        caderno="3",
        instancia="1",
        local="Capital",
        parte="1"
    )


@pytest.fixture
def mock_scraper() -> AsyncMock:
    """Mock do scraper para testes."""
    scraper = AsyncMock(spec=PlaywrightScraperAdapter)
    
    # Configurar métodos principais
    scraper.initialize.return_value = None
    scraper.navigate_to_dje.return_value = True
    scraper.navigate_to_caderno.return_value = True
    scraper.close.return_value = None
    
    return scraper


@pytest.fixture
def mock_database() -> AsyncMock:
    """Mock do banco de dados para testes."""
    database = AsyncMock(spec=SQLAlchemyRepository)
    
    # Configurar métodos principais
    database.save_publication.return_value = None
    database.exists_by_process_number.return_value = False
    database.find_by_process_number.return_value = None
    
    return database


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Mock do cache para testes."""
    cache = AsyncMock(spec=RedisCacheAdapter)
    
    # Configurar métodos principais
    cache.get.return_value = None
    cache.set.return_value = True
    cache.exists.return_value = False
    cache.delete.return_value = True
    
    return cache


@pytest.fixture
async def test_database(test_settings) -> AsyncGenerator[SQLAlchemyRepository, None]:
    """Banco de dados real para testes de integração."""
    db = SQLAlchemyRepository(test_settings.database.url)
    
    # Criar tabelas
    await db.create_tables()
    
    yield db
    
    # Limpeza após teste
    await db.close()


@pytest.fixture
def mock_playwright_page():
    """Mock da página do Playwright."""
    page = AsyncMock()
    
    # Configurar métodos comuns
    page.goto.return_value = MagicMock(status=200)
    page.wait_for_load_state.return_value = None
    page.wait_for_selector.return_value = MagicMock()
    page.query_selector_all.return_value = []
    page.title.return_value = "DJE - Diário da Justiça Eletrônico"
    page.url = "https://dje.tjsp.jus.br"
    
    return page


@pytest.fixture
def sample_html_content() -> str:
    """Conteúdo HTML de exemplo para testes de parsing."""
    return """
    <div class="publicacao">
        <p>Processo nº 1234567-89.2024.8.26.0100</p>
        <p>Data de disponibilização: 15/03/2024</p>
        <p>Autor: João da Silva</p>
        <p>Réu: Instituto Nacional do Seguro Social - INSS</p>
        <p>Advogado: Dr. Carlos Alberto - OAB/SP 123456</p>
        <p>Valor principal: R$ 15.000,50</p>
        <p>Juros moratórios: R$ 2.500,25</p>
        <p>Honorários advocatícios: R$ 3.000,00</p>
        <p>Conteúdo da decisão judicial...</p>
    </div>
    """