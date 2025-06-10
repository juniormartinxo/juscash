from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from uuid import uuid4


@dataclass
class Lawyer:
    """Entidade que representa um advogado"""
    name: str
    oab: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "oab": self.oab}


@dataclass
class Publication:
    """Entidade de domínio para publicações"""
    
    # Campos obrigatórios
    process_number: str
    availability_date: date
    authors: List[str]
    content: str
    
    # Campos opcionais com valores padrão
    id: str = field(default_factory=lambda: str(uuid4()))
    publication_date: Optional[date] = None
    defendant: str = "Instituto Nacional do Seguro Social - INSS"
    lawyers: List[Lawyer] = field(default_factory=list)
    gross_value: Optional[int] = None  # Em centavos
    net_value: Optional[int] = None    # Em centavos
    interest_value: Optional[int] = None  # Em centavos
    attorney_fees: Optional[int] = None   # Em centavos
    status: str = "NOVA"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validações após a inicialização"""
        self._validate_process_number()
        self._validate_authors()
        self._validate_content()
        self._validate_status()
    
    def _validate_process_number(self):
        """Valida o número do processo"""
        if not self.process_number or not self.process_number.strip():
            raise ValueError("Número do processo é obrigatório")
    
    def _validate_authors(self):
        """Valida a lista de autores"""
        if not self.authors or len(self.authors) == 0:
            raise ValueError("Pelo menos um autor é obrigatório")
        
        # Remove autores vazios
        self.authors = [author.strip() for author in self.authors if author.strip()]
        
        if not self.authors:
            raise ValueError("Pelo menos um autor válido é obrigatório")
    
    def _validate_content(self):
        """Valida o conteúdo da publicação"""
        if not self.content or not self.content.strip():
            raise ValueError("Conteúdo da publicação é obrigatório")
    
    def _validate_status(self):
        """Valida o status da publicação"""
        valid_statuses = ["NOVA", "LIDA", "PROCESSADA"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status deve ser um dos seguintes: {valid_statuses}")
    
    def add_lawyer(self, name: str, oab: str):
        """Adiciona um advogado à publicação"""
        if not name or not name.strip():
            raise ValueError("Nome do advogado é obrigatório")
        if not oab or not oab.strip():
            raise ValueError("OAB do advogado é obrigatória")
        
        lawyer = Lawyer(name=name.strip(), oab=oab.strip())
        self.lawyers.append(lawyer)
    
    def update_status(self, new_status: str):
        """Atualiza o status da publicação"""
        old_status = self.status
        self.status = new_status
        self._validate_status()
        
        # Lógica de negócio para transições de status
        self._validate_status_transition(old_status, new_status)
    
    def _validate_status_transition(self, old_status: str, new_status: str):
        """Valida se a transição de status é permitida"""
        valid_transitions = {
            "NOVA": ["LIDA"],
            "LIDA": ["PROCESSADA"],
            "PROCESSADA": []  # Status final
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f"Transição de status de '{old_status}' para '{new_status}' não é permitida")
    
    def set_monetary_value(self, gross: Optional[float] = None, net: Optional[float] = None, 
                          interest: Optional[float] = None, fees: Optional[float] = None):
        """Define valores monetários (converte de reais para centavos)"""
        if gross is not None:
            self.gross_value = int(gross * 100)
        if net is not None:
            self.net_value = int(net * 100)
        if interest is not None:
            self.interest_value = int(interest * 100)
        if fees is not None:
            self.attorney_fees = int(fees * 100)
    
    def get_monetary_values_in_reais(self) -> Dict[str, Optional[float]]:
        """Retorna valores monetários convertidos para reais"""
        return {
            "gross_value": self.gross_value / 100 if self.gross_value is not None else None,
            "net_value": self.net_value / 100 if self.net_value is not None else None,
            "interest_value": self.interest_value / 100 if self.interest_value is not None else None,
            "attorney_fees": self.attorney_fees / 100 if self.attorney_fees is not None else None,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário"""
        return {
            "id": self.id,
            "process_number": self.process_number,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "availability_date": self.availability_date.isoformat(),
            "authors": self.authors,
            "defendant": self.defendant,
            "lawyers": [lawyer.to_dict() for lawyer in self.lawyers],
            "gross_value": self.gross_value,
            "net_value": self.net_value,
            "interest_value": self.interest_value,
            "attorney_fees": self.attorney_fees,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }