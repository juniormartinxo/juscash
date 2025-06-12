from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import declarative_base
import asyncio
from typing import Optional

from src.config.settings import settings
from src.shared.logger import get_logger

logger = get_logger(__name__)

# Base para modelos SQLAlchemy
Base = declarative_base()

# Engine global
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


async def get_engine():
    """
    Retorna engine SQLAlchemy (singleton).
    
    Returns:
        Engine configurado para PostgreSQL
    """
    global _engine
    
    if _engine is None:
        _engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,
            pool_recycle=settings.database.pool_recycle,
            future=True
        )
        logger.info("Engine SQLAlchemy criado")
    
    return _engine


async def get_session_factory():
    """
    Retorna factory de sessões SQLAlchemy (singleton).
    
    Returns:
        Factory de sessões configurado
    """
    global _session_factory
    
    if _session_factory is None:
        engine = await get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        logger.info("Factory de sessões SQLAlchemy criado")
    
    return _session_factory


async def get_db_session() -> AsyncSession:
    """
    Retorna nova sessão de banco de dados.
    
    Returns:
        Sessão SQLAlchemy configurada
    """
    factory = await get_session_factory()
    return factory()


async def create_tables():
    """
    Cria todas as tabelas no banco de dados.
    
    Raises:
        Exception: Se houver erro na criação das tabelas
    """
    try:
        engine = await get_engine()
        
        async with engine.begin() as conn:
            # Importar modelos para registrar na Base
            from src.adapters.secondary.sqlalchemy_repository import PublicationModel
            
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Tabelas criadas com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise


async def close_db_connections():
    """
    Fecha todas as conexões com o banco de dados.
    """
    global _engine, _session_factory
    
    try:
        if _engine:
            await _engine.dispose()
            _engine = None
            _session_factory = None
        
        logger.info("Conexões com banco fechadas")
        
    except Exception as e:
        logger.error(f"Erro ao fechar conexões: {str(e)}")


# Função utilitária para uso em testes
async def reset_database():
    """
    Remove e recria todas as tabelas (CUIDADO: apaga dados!).
    
    Raises:
        Exception: Se houver erro na operação
    """
    try:
        engine = await get_engine()
        
        async with engine.begin() as conn:
            # Importar modelos
            from src.adapters.secondary.sqlalchemy_repository import PublicationModel
            
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        logger.warning("Banco de dados resetado - TODOS OS DADOS FORAM PERDIDOS")
        
    except Exception as e:
        logger.error(f"Erro ao resetar banco: {str(e)}")
        raise