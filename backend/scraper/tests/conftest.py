"""
Configuração compartilhada para testes do scraper
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from src.domain.entities.publication import Publication, Lawyer, MonetaryValue
from src.domain.entities.scraping_execution import (
    ScrapingExecution,
    ExecutionType,
    ExecutionStatus,
)
from src.infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Cria loop de eventos para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_publication():
    """Publicação de exemplo para testes"""
    return Publication(
        process_number="1234567-89.2024.8.26.0100",
        publication_date=datetime(2024, 3, 15),
        availability_date=datetime(2024, 3, 17),
        authors=["João Silva Santos", "Maria Oliveira Lima"],
        lawyers=[
            Lawyer(name="Dr. Carlos Advogado", oab="123456"),
            Lawyer(name="Dra. Ana Jurista", oab="789012"),
        ],
        gross_value=MonetaryValue.from_real(1500.00),
        net_value=MonetaryValue.from_real(1350.00),
        interest_value=MonetaryValue.from_real(100.00),
        attorney_fees=MonetaryValue.from_real(50.00),
        content="Conteúdo de teste sobre aposentadoria por invalidez do INSS. Benefício concedido após análise médica.",
        extraction_metadata={
            "extraction_date": datetime.now().isoformat(),
            "source_url": "https://dje.tjsp.jus.br/test",
            "confidence_score": 0.95,
            "test_data": True,
        },
    )


@pytest.fixture
def sample_execution():
    """Execução de exemplo para testes"""
    return ScrapingExecution(
        execution_id="test-execution-123",
        execution_type=ExecutionType.TEST,
        publications_found=10,
        publications_new=5,
        publications_duplicated=3,
        publications_failed=2,
        publications_saved=5,
    )


@pytest.fixture
def sample_content_dje():
    """Conteúdo de exemplo do DJE para testes de parsing"""
    return """
    PROCESSO: 1234567-89.2024.8.26.0100
    Data de Publicação: 15/03/2024
    Data de Disponibilização: 17/03/2024
    
    Autor: João Silva Santos
    Réu: Instituto Nacional do Seguro Social - INSS
    Advogado: Dr. Carlos Advogado, OAB 123456
    
    DECISÃO: Defiro o pedido de aposentadoria por invalidez.
    Valor Principal: R$ 1.500,00
    Valor Líquido: R$ 1.350,00
    Juros Moratórios: R$ 100,00
    Honorários Advocatícios: R$ 50,00
    
    Considerando a documentação médica apresentada e o benefício do INSS,
    determino o pagamento do valor devido ao requerente.
    """
