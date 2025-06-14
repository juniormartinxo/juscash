"""
Entidade Publication - Core Domain
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


@dataclass(frozen=True)
class Lawyer:
    """Advogado responsável"""

    name: str
    oab: str


@dataclass(frozen=True)
class MonetaryValue:
    """Valor monetário em centavos"""

    amount_cents: int

    @classmethod
    def from_real(cls, value: Decimal) -> "MonetaryValue":
        """Converte valor em reais para centavos"""
        return cls(amount_cents=int(value * 100))

    def to_real(self) -> Decimal:
        """Converte centavos para reais"""
        return Decimal(self.amount_cents) / 100


@dataclass(frozen=True)
class Publication:
    """
    Entidade principal - Publicação do DJE

    Representa uma publicação extraída do Diário da Justiça Eletrônico
    com todos os dados necessários para processamento.
    """

    # Identificação
    process_number: str

    # Datas
    publication_date: Optional[datetime]
    availability_date: datetime

    # Partes do processo
    authors: List[str]
    defendant: str = "Instituto Nacional do Seguro Social - INSS"
    lawyers: List[Lawyer] = field(default_factory=list)

    # Valores monetários (em centavos)
    gross_value: Optional[MonetaryValue] = None
    net_value: Optional[MonetaryValue] = None
    interest_value: Optional[MonetaryValue] = None
    attorney_fees: Optional[MonetaryValue] = None

    # Conteúdo
    content: str = ""

    # Status e metadados
    status: str = "NOVA"
    scraping_source: str = "DJE-SP"
    caderno: str = "3"
    instancia: str = "1"
    local: str = "Capital"
    parte: str = "1"

    # Metadados de extração
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validações pós-inicialização"""
        if not self.process_number.strip():
            raise ValueError("Número do processo é obrigatório")

        if not self.authors:
            raise ValueError("Pelo menos um autor é obrigatório")

        if not self.content.strip():
            raise ValueError("Conteúdo da publicação é obrigatório")

    def to_api_dict(self) -> Dict[str, Any]:
        """Converte para formato da API"""

        def format_datetime_for_api(dt: datetime) -> str:
            """Formata datetime para o formato esperado pela API (ISO 8601 UTC)"""
            if dt.tzinfo is None:
                # Se não tem timezone, assume UTC
                dt = dt.replace(tzinfo=None)
            # Converter para UTC e formatar como ISO string
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        return {
            "processNumber": self.process_number,
            "publicationDate": format_datetime_for_api(self.publication_date)
            if self.publication_date
            else None,
            "availabilityDate": format_datetime_for_api(self.availability_date),
            "authors": self.authors,
            "defendant": self.defendant,
            "lawyers": [
                {"name": lawyer.name, "oab": lawyer.oab} for lawyer in self.lawyers
            ],
            "grossValue": self.gross_value.amount_cents if self.gross_value else None,
            "netValue": self.net_value.amount_cents if self.net_value else None,
            "interestValue": self.interest_value.amount_cents
            if self.interest_value
            else None,
            "attorneyFees": self.attorney_fees.amount_cents
            if self.attorney_fees
            else None,
            "content": self.content,
            "status": self.status,
            "scrapingSource": self.scraping_source,
            "caderno": self.caderno,
            "instancia": self.instancia,
            "local": self.local,
            "parte": self.parte,
            "extractionMetadata": self.extraction_metadata,
        }
