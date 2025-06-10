from sqlalchemy import (
    Column, String, DateTime, Integer, Text, JSON, 
    Boolean, Date, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from .config import Base


class PublicationStatus(str, Enum):
    """Status das publicações"""
    NOVA = "NOVA"
    LIDA = "LIDA"
    PROCESSADA = "PROCESSADA"


class Publication(Base):
    """Modelo SQLAlchemy para publicações"""
    
    __tablename__ = "publications"
    
    # Campos principais
    id = Column(String, primary_key=True)
    process_number = Column(String, unique=True, nullable=False, index=True)
    publication_date = Column(Date, nullable=True)
    availability_date = Column(Date, nullable=False, index=True)
    authors = Column(ARRAY(String), nullable=False, default=[])
    defendant = Column(String, nullable=False, default="Instituto Nacional do Seguro Social - INSS")
    lawyers = Column(JSON, nullable=True)  # [{"name": "João", "oab": "123456"}]
    
    # Valores monetários em centavos
    gross_value = Column(Integer, nullable=True)
    net_value = Column(Integer, nullable=True)
    interest_value = Column(Integer, nullable=True)
    attorney_fees = Column(Integer, nullable=True)
    
    # Conteúdo e status
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(PublicationStatus), nullable=False, default=PublicationStatus.NOVA, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Índices compostos
    __table_args__ = (
        Index('idx_status_availability_date', 'status', 'availability_date'),
        Index('idx_availability_date_created_at', 'availability_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Publication(id={self.id}, process_number={self.process_number}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário"""
        return {
            'id': self.id,
            'process_number': self.process_number,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'availability_date': self.availability_date.isoformat() if self.availability_date else None,
            'authors': self.authors,
            'defendant': self.defendant,
            'lawyers': self.lawyers,
            'gross_value': self.gross_value,
            'net_value': self.net_value,
            'interest_value': self.interest_value,
            'attorney_fees': self.attorney_fees,
            'content': self.content,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }