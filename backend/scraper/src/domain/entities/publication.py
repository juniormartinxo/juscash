"""
Entidade Publication - Core Domain
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    publication_date: Optional[datetime] = None
    availability_date: Optional[datetime] = None

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

        # Validar formato do número do processo
        if not self._validate_process_number_format(self.process_number):
            raise ValueError(f"Número do processo inválido: {self.process_number}")

        # Validar autores
        if len(self.authors) == 1 and self.authors[0] == "Não identificado":
            raise ValueError("Autor não pode ser 'Não identificado'")

        # Validar datas (permitir pequeno buffer para evitar problemas de timezone)
        now = datetime.now()

        if self.publication_date:
            # Permitir até 1 dia no futuro para evitar problemas de timezone
            max_future = now.replace(hour=0, minute=0, second=0) + timedelta(days=2)
            if self.publication_date > max_future:
                raise ValueError(
                    f"Data de publicação muito no futuro: {self.publication_date}"
                )

        # Permitir até 1 dia no futuro para availability_date
        max_future = now.replace(hour=0, minute=0, second=0) + timedelta(days=2)
        if self.availability_date > max_future:
            raise ValueError(
                f"Data de disponibilização muito no futuro: {self.availability_date}"
            )

    def _validate_process_number_format(self, process_number: str) -> bool:
        """Valida formato do número do processo brasileiro"""
        parts = process_number.split("-")
        if len(parts) != 2:
            return False

        # Verificar sequencial (7 dígitos)
        if len(parts[0]) != 7 or not parts[0].isdigit():
            return False

        # Verificar resto (DD.AAAA.J.TR.OOOO)
        rest_parts = parts[1].split(".")
        if len(rest_parts) != 5:
            return False

        # Validar cada parte
        expected_lengths = [2, 4, 1, 2, 4]
        for i, (part, length) in enumerate(zip(rest_parts, expected_lengths)):
            if len(part) != length or not part.isdigit():
                return False

        return True

    def to_api_dict(self) -> Dict[str, Any]:
        """Converte para formato da API"""

        def format_datetime_for_api(dt: datetime) -> str:
            """Formata datetime para o formato esperado pela API (ISO 8601 UTC)"""
            if dt.tzinfo is None:
                # Se não tem timezone, assume UTC
                dt = dt.replace(tzinfo=None)
            # Converter para UTC e formatar como ISO string
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        def clean_content(content: str) -> str:
            """Limpa o conteúdo removendo caracteres problemáticos"""
            if not content:
                return ""

            # Remover quebras de linha e espaços extras
            cleaned = " ".join(content.split())

            # Limitar tamanho para evitar rejeição da API (máximo 2000 caracteres)
            if len(cleaned) > 2000:
                cleaned = cleaned[:2000] + "..."

            return cleaned

        # Garantir que todos os campos obrigatórios estejam presentes
        data = {
            "process_number": self.process_number,
            "availability_date": format_datetime_for_api(self.availability_date),
            "authors": self.authors,
            "defendant": "Instituto Nacional do Seguro Social - INSS",  # Valor padrão
            "content": clean_content(self.content),
            "status": "NOVA",  # Valor padrão
            "scraping_source": "DJE-SP",  # Valor padrão
            "caderno": "3",  # Valor padrão
            "instancia": "1",  # Valor padrão
            "local": "Capital",  # Valor padrão
            "parte": "1",  # Valor padrão
        }

        # Adicionar campos opcionais apenas se existirem
        if self.publication_date:
            data["publicationDate"] = format_datetime_for_api(self.publication_date)

        # Sempre incluir lawyers como array (mesmo que vazio)
        data["lawyers"] = [
            {"name": lawyer.name, "oab": lawyer.oab} for lawyer in self.lawyers
        ]

        if self.gross_value:
            data["gross_value"] = self.gross_value.amount_cents

        if self.net_value:
            data["net_value"] = self.net_value.amount_cents

        if self.interest_value:
            data["interest_value"] = self.interest_value.amount_cents

        if self.attorney_fees:
            data["attorney_fees"] = self.attorney_fees.amount_cents

        if self.extraction_metadata:
            data["extraction_metadata"] = self.extraction_metadata

        return data
