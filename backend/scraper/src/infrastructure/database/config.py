import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger


class DatabaseConfig:
    """Configuração do banco de dados"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def _get_database_url(self) -> str:
        """Obtém a URL do banco de dados das variáveis de ambiente"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL não foi definida nas variáveis de ambiente")
        return database_url
    
    def _create_engine(self):
        """Cria e configura o engine do SQLAlchemy"""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False  # Mude para True para debug SQL
        )
    
    @contextmanager
    def get_session(self):
        """Context manager para sessões do banco de dados"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na transação do banco de dados: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco de dados"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Conexão com o banco de dados estabelecida com sucesso")
            return True
        except Exception as e:
            logger.error(f"Falha ao conectar com o banco de dados: {e}")
            return False


# Instância global da configuração do banco
db_config = DatabaseConfig()

# Base para modelos SQLAlchemy
Base = declarative_base()