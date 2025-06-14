"""
Entidade ScrapingExecution - Core Domain
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class ExecutionStatus(Enum):
    """Status da execução do scraping"""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class ExecutionType(Enum):
    """Tipo de execução"""

    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    TEST = "TEST"
    RETRY = "RETRY"


@dataclass
class ScrapingExecution:
    """
    Entidade que representa uma execução do scraping
    """

    execution_id: str
    execution_type: ExecutionType
    status: ExecutionStatus = ExecutionStatus.RUNNING

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None

    # Estatísticas
    publications_found: int = 0
    publications_new: int = 0
    publications_duplicated: int = 0
    publications_failed: int = 0
    publications_saved: int = 0

    # Configurações utilizadas
    criteria_used: Dict[str, Any] = field(default_factory=dict)
    max_publications_limit: Optional[int] = None

    # Informações técnicas
    scraper_version: str = "1.0.0"
    browser_user_agent: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    def mark_as_completed(self):
        """Marca execução como concluída"""
        self.status = ExecutionStatus.COMPLETED
        self.finished_at = datetime.now()

    def mark_as_failed(self, error_details: Dict[str, Any]):
        """Marca execução como falha"""
        self.status = ExecutionStatus.FAILED
        self.finished_at = datetime.now()
        self.error_details = error_details

    @property
    def execution_time_seconds(self) -> Optional[int]:
        """Tempo de execução em segundos"""
        if self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None

    @property
    def is_running(self) -> bool:
        """Verifica se ainda está executando"""
        return self.status == ExecutionStatus.RUNNING
