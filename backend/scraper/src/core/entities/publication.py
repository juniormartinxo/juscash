from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from src.shared.value_objects import ProcessNumber, Status


@dataclass
class Publication:
    """
    Entidade Publication representando uma publicação do DJE.
    
    Esta entidade contém todas as informações extraídas de uma publicação
    do Diário da Justiça Eletrônico, seguindo as regras de negócio definidas.
    """
    
    # Identificadores únicos
    id: UUID = field(default_factory=uuid4)
    process_number: Optional[ProcessNumber] = None
    
    # Datas importantes
    publication_date: Optional[datetime] = None
    availability_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Partes envolvidas (sempre usar INSS como réu conforme regra)
    authors: List[str] = field(default_factory=list)
    defendant: str = field(default="Instituto Nacional do Seguro Social - INSS")
    lawyers: List[str] = field(default_factory=list)
    
    # Valores monetários
    gross_value: Optional[Decimal] = None
    net_value: Optional[Decimal] = None
    interest_value: Optional[Decimal] = None
    attorney_fees: Optional[Decimal] = None
    
    # Conteúdo e status
    content: Optional[str] = None
    status: Status = field(default_factory=lambda: Status.NEW)
    
    def __post_init__(self):
        """Validações após inicialização."""
        self._validate_authors()
        self._validate_lawyers()
        self._validate_monetary_values()
    
    def _validate_authors(self) -> None:
        """Valida lista de autores."""
        if self.authors:
            # Remove strings vazias e duplicatas mantendo ordem
            seen = set()
            self.authors = [
                author.strip() 
                for author in self.authors 
                if author.strip() and not (author.strip() in seen or seen.add(author.strip()))
            ]
    
    def _validate_lawyers(self) -> None:
        """Valida lista de advogados."""
        if self.lawyers:
            # Remove strings vazias e duplicatas mantendo ordem
            seen = set()
            self.lawyers = [
                lawyer.strip() 
                for lawyer in self.lawyers 
                if lawyer.strip() and not (lawyer.strip() in seen or seen.add(lawyer.strip()))
            ]
    
    def _validate_monetary_values(self) -> None:
        """Valida valores monetários."""
        monetary_fields = ['gross_value', 'net_value', 'interest_value', 'attorney_fees']
        
        for field_name in monetary_fields:
            value = getattr(self, field_name)
            if value is not None and value < 0:
                setattr(self, field_name, None)
    
    def update_status(self, new_status: Status) -> None:
        """
        Atualiza o status da publicação.
        
        Args:
            new_status: Novo status a ser aplicado
        """
        if not isinstance(new_status, Status):
            raise ValueError("Status deve ser uma instância de Status enum")
        
        self.status = new_status
        self.updated_at = datetime.now()
    
    def has_required_search_terms(self, required_terms: List[str]) -> bool:
        """
        Verifica se a publicação contém os termos obrigatórios de busca.
        
        Args:
            required_terms: Lista de termos que devem estar presentes
            
        Returns:
            True se todos os termos estiverem presentes no conteúdo
        """
        if not self.content or not required_terms:
            return False
        
        content_lower = self.content.lower()
        return all(term.lower() in content_lower for term in required_terms)
    
    def extract_process_info(self, content: str) -> None:
        """
        Extrai informações básicas do processo a partir do conteúdo.
        Método auxiliar para parsing inicial.
        
        Args:
            content: Conteúdo completo da publicação
        """
        self.content = content
        self.updated_at = datetime.now()
    
    def is_valid_for_processing(self) -> bool:
        """
        Verifica se a publicação tem dados mínimos para processamento.
        
        Returns:
            True se a publicação tem dados suficientes
        """
        return (
            self.process_number is not None and
            self.content is not None and
            len(self.content.strip()) > 0
        )
    
    def to_dict(self) -> dict:
        """
        Converte a entidade para dicionário para serialização.
        
        Returns:
            Dicionário com todos os dados da publicação
        """
        return {
            'id': str(self.id),
            'process_number': str(self.process_number) if self.process_number else None,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'availability_date': self.availability_date.isoformat() if self.availability_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'authors': self.authors,
            'defendant': self.defendant,
            'lawyers': self.lawyers,
            'gross_value': str(self.gross_value) if self.gross_value else None,
            'net_value': str(self.net_value) if self.net_value else None,
            'interest_value': str(self.interest_value) if self.interest_value else None,
            'attorney_fees': str(self.attorney_fees) if self.attorney_fees else None,
            'content': self.content,
            'status': self.status.value
        }
    
    def __str__(self) -> str:
        """Representação string da publicação."""
        process_info = f"Processo: {self.process_number}" if self.process_number else "Processo: N/A"
        status_info = f"Status: {self.status.value}"
        return f"Publication({process_info}, {status_info})"
    
    def __repr__(self) -> str:
        """Representação técnica da publicação."""
        return (
            f"Publication(id={self.id}, process_number={self.process_number}, "
            f"status={self.status.value}, created_at={self.created_at})"
        )