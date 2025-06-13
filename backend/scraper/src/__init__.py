"""
Sistema de Scraping do Diário da Justiça Eletrônico (DJE).

Este módulo implementa um sistema completo para automação de coleta
e gerenciamento de publicações do DJE de São Paulo, seguindo os
princípios da Arquitetura Hexagonal.

Principais componentes:
- Core: Entidades, casos de uso e ports (interfaces)
- Adapters: Implementações específicas (Playwright, SQLAlchemy, Redis, etc.)
- Config: Configurações e setup da aplicação
- Shared: Utilitários compartilhados

Uso:
    # Execução imediata
    python -m src.main

    # Execução com agendamento
    python -m src.main --schedule

    # Testes
    python -m src.main --test-scraping
    python -m src.main --test-db
"""

__version__ = "1.0.0"
__author__ = "JusCash Development Team"
__description__ = "Sistema de Scraping DJE - Diário da Justiça Eletrônico"

# Exports principais para facilitar imports
from src.core.entities.publication import Publication
from src.shared.value_objects import Status, ProcessNumber, ScrapingCriteria
from src.config.settings import settings
from src.shared.logger import get_logger

# Criar instância das configurações

__all__ = [
    "Publication",
    "Status",
    "ProcessNumber",
    "ScrapingCriteria",
    "settings",
    "get_logger",
]
