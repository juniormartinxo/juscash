import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger


class DatabaseConfig:
    """Configuração do banco de dados"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_database_url()
        self._engine = None
        self._SessionLocal = None

    @property
    def engine(self):
        """Lazy loading do engine"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def SessionLocal(self):
        """Lazy loading da SessionLocal"""
        if self._SessionLocal is None:
            self._SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
        return self._SessionLocal

    def _get_database_url(self) -> str:
        """Obtém a URL do banco de dados das variáveis de ambiente"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Fallback para desenvolvimento local se variáveis individuais estiverem disponíveis
            fallback_url = self._build_fallback_url()
            if fallback_url:
                logger.warning(
                    "DATABASE_URL não encontrada, usando configuração fallback"
                )
                return fallback_url

            logger.error("DATABASE_URL não foi definida nas variáveis de ambiente")
            logger.error("Configure DATABASE_URL ou as variáveis individuais do banco")
            raise ValueError("DATABASE_URL não foi definida nas variáveis de ambiente")
        return database_url

    def _build_fallback_url(self) -> Optional[str]:
        """Constrói URL de fallback a partir de variáveis individuais"""
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB")
        db_user = os.getenv("POSTGRES_USER")
        db_password = os.getenv("POSTGRES_PASSWORD")

        if all([db_name, db_user, db_password]):
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        return None

    def _create_engine(self):
        """Cria e configura o engine do SQLAlchemy"""
        try:
            engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,  # Mude para True para debug SQL
            )
            logger.info("Engine do banco de dados criado com sucesso")
            return engine
        except Exception as e:
            logger.error(f"Erro ao criar engine do banco de dados: {e}")
            raise

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


# Função para criar instância de configuração (lazy loading)
_db_config = None


def get_db_config() -> DatabaseConfig:
    """Obtém a instância global da configuração do banco (singleton)"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


# Para compatibilidade com código existente
db_config = None  # Será inicializado quando necessário

# Base para modelos SQLAlchemy
Base = declarative_base()
