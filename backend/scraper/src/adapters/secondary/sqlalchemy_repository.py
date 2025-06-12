from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Numeric, Boolean, JSON, select, exists, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from datetime import datetime
from decimal import Decimal
import enum

from src.core.entities.publication import Publication
from src.core.ports.database_port import DatabasePort
from src.shared.value_objects import Status, ProcessNumber
from src.shared.exceptions import DatabaseException, ValidationException
from src.shared.logger import get_logger

logger = get_logger(__name__)

# Base para modelos SQLAlchemy
Base = declarative_base()


# Enums que correspondem ao schema Prisma
class PublicationStatusEnum(enum.Enum):
    NOVA = "NOVA"
    LIDA = "LIDA"
    ENVIADA_PARA_ADV = "ENVIADA_PARA_ADV"
    CONCLUIDA = "CONCLUIDA"


class ScrapingExecutionTypeEnum(enum.Enum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    TEST = "TEST"
    RETRY = "RETRY"


class ScrapingExecutionStatusEnum(enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class ScrapingLogLevelEnum(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PublicationModel(Base):
    """
    Modelo SQLAlchemy atualizado para corresponder ao schema Prisma.
    
    Representa a tabela 'publications' com todos os campos necessários
    para o sistema de scraping DJE conforme implementado.
    """
    
    __tablename__ = "publications"
    
    # Campos obrigatórios
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[PublicationStatusEnum] = mapped_column(
        SQLEnum(PublicationStatusEnum, name="publication_status"), 
        nullable=False, 
        default=PublicationStatusEnum.NOVA
    )
    defendant: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        default="Instituto Nacional do Seguro Social - INSS"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Campos de identificação (opcionais)
    process_number: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    
    # Campos de datas
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    availability_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Campos de partes envolvidas
    authors: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, default=list)
    lawyers: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, default=list)
    
    # Campos de valores monetários (usando Decimal para precisão)
    gross_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    net_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    interest_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    attorney_fees: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Conteúdo completo
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Campos específicos para scraping (novos)
    scraping_source: Mapped[str] = mapped_column(String(50), nullable=False, default="DJE-SP")
    caderno: Mapped[str] = mapped_column(String(10), nullable=False, default="3")
    instancia: Mapped[str] = mapped_column(String(10), nullable=False, default="1")
    local: Mapped[str] = mapped_column(String(50), nullable=False, default="Capital")
    parte: Mapped[str] = mapped_column(String(10), nullable=False, default="1")
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scraping_execution_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    
    def to_entity(self) -> Publication:
        """
        Converte o modelo SQLAlchemy para entidade do domínio.
        
        Returns:
            Entidade Publication com dados do modelo
        """
        process_number = None
        if self.process_number:
            try:
                process_number = ProcessNumber(self.process_number)
            except Exception as e:
                logger.warning(f"Erro ao criar ProcessNumber: {str(e)}")
        
        # Mapear status do Prisma para o sistema Python
        status_mapping = {
            PublicationStatusEnum.NOVA: Status.NEW,
            PublicationStatusEnum.LIDA: Status.READ,
            PublicationStatusEnum.ENVIADA_PARA_ADV: Status.SENT_TO_LAWYER,
            PublicationStatusEnum.CONCLUIDA: Status.COMPLETED
        }
        
        status = status_mapping.get(self.status, Status.NEW)
        
        return Publication(
            id=self.id,
            process_number=process_number,
            publication_date=self.publication_date,
            availability_date=self.availability_date,
            created_at=self.created_at,
            updated_at=self.updated_at,
            authors=self.authors or [],
            defendant=self.defendant,
            lawyers=self.lawyers or [],
            gross_value=self.gross_value,
            net_value=self.net_value,
            interest_value=self.interest_value,
            attorney_fees=self.attorney_fees,
            content=self.content,
            status=status
        )
    
    @classmethod
    def from_entity(cls, publication: Publication, scraping_execution_id: Optional[UUID] = None) -> 'PublicationModel':
        """
        Cria um modelo SQLAlchemy a partir de uma entidade do domínio.
        
        Args:
            publication: Entidade Publication
            scraping_execution_id: ID da execução de scraping (opcional)
            
        Returns:
            Modelo SQLAlchemy com dados da entidade
        """
        # Mapear status do sistema Python para Prisma
        status_mapping = {
            Status.NEW: PublicationStatusEnum.NOVA,
            Status.READ: PublicationStatusEnum.LIDA,
            Status.SENT_TO_LAWYER: PublicationStatusEnum.ENVIADA_PARA_ADV,
            Status.COMPLETED: PublicationStatusEnum.CONCLUIDA
        }
        
        status = status_mapping.get(publication.status, PublicationStatusEnum.NOVA)
        
        return cls(
            id=publication.id,
            process_number=str(publication.process_number) if publication.process_number else None,
            publication_date=publication.publication_date,
            availability_date=publication.availability_date,
            created_at=publication.created_at,
            updated_at=publication.updated_at,
            authors=publication.authors or [],
            defendant=publication.defendant,
            lawyers=publication.lawyers or [],
            gross_value=publication.gross_value,
            net_value=publication.net_value,
            interest_value=publication.interest_value,
            attorney_fees=publication.attorney_fees,
            content=publication.content,
            status=status,
            scraping_execution_id=scraping_execution_id
        )


class ScrapingExecutionModel(Base):
    """
    Modelo para rastrear execuções do sistema de scraping.
    
    Corresponde à tabela 'scraping_executions' do schema Prisma,
    permitindo monitorar e auditar todas as execuções do scraper.
    """
    
    __tablename__ = "scraping_executions"
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_type: Mapped[ScrapingExecutionTypeEnum] = mapped_column(
        SQLEnum(ScrapingExecutionTypeEnum, name="scraping_execution_type"),
        nullable=False
    )
    status: Mapped[ScrapingExecutionStatusEnum] = mapped_column(
        SQLEnum(ScrapingExecutionStatusEnum, name="scraping_execution_status"),
        nullable=False,
        default=ScrapingExecutionStatusEnum.RUNNING
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_time_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Estatísticas da execução
    publications_found: Mapped[int] = mapped_column(nullable=False, default=0)
    publications_new: Mapped[int] = mapped_column(nullable=False, default=0)
    publications_duplicated: Mapped[int] = mapped_column(nullable=False, default=0)
    publications_failed: Mapped[int] = mapped_column(nullable=False, default=0)
    publications_saved: Mapped[int] = mapped_column(nullable=False, default=0)
    
    # Configurações e metadados
    criteria_used: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    max_publications_limit: Mapped[Optional[int]] = mapped_column(nullable=True)
    scraper_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    browser_user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ScrapingLogModel(Base):
    """
    Modelo para logs detalhados do processo de scraping.
    
    Complementa os logs de arquivo com persistência em banco
    para análise via interface web.
    """
    
    __tablename__ = "scraping_logs"
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    scraping_execution_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    level: Mapped[ScrapingLogLevelEnum] = mapped_column(
        SQLEnum(ScrapingLogLevelEnum, name="scraping_log_level"),
        nullable=False,
        default=ScrapingLogLevelEnum.INFO
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


class EnhancedSQLAlchemyRepository(DatabasePort):
    """
    Repositório SQLAlchemy aprimorado para trabalhar com o schema Prisma.
    
    Inclui suporte para execuções de scraping e logs detalhados,
    mantendo compatibilidade com a interface original.
    """
    
    def __init__(self, database_url: str):
        """
        Inicializa o repositório.
        
        Args:
            database_url: URL de conexão com o banco PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.current_execution_id: Optional[UUID] = None
    
    async def create_tables(self) -> None:
        """Cria as tabelas no banco de dados."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {str(e)}")
            raise DatabaseException("create_tables", str(e))
    
    async def start_scraping_execution(self, 
                                     execution_type: str = "MANUAL",
                                     criteria: Optional[dict] = None,
                                     max_publications: Optional[int] = None) -> UUID:
        """
        Inicia uma nova execução de scraping.
        
        Args:
            execution_type: Tipo de execução (SCHEDULED, MANUAL, TEST, RETRY)
            criteria: Critérios de busca utilizados
            max_publications: Limite máximo de publicações
            
        Returns:
            ID da execução criada
        """
        try:
            async with self.async_session() as session:
                execution = ScrapingExecutionModel(
                    execution_type=ScrapingExecutionTypeEnum(execution_type),
                    criteria_used=criteria,
                    max_publications_limit=max_publications
                )
                
                session.add(execution)
                await session.commit()
                await session.refresh(execution)
                
                self.current_execution_id = execution.id
                logger.info(f"Execução de scraping iniciada: {execution.id}")
                
                return execution.id
                
        except Exception as e:
            logger.error(f"Erro ao iniciar execução de scraping: {str(e)}")
            raise DatabaseException("start_scraping_execution", str(e))
    
    async def finish_scraping_execution(self, 
                                      execution_id: UUID,
                                      status: str,
                                      stats: dict,
                                      error_details: Optional[dict] = None) -> None:
        """
        Finaliza uma execução de scraping com estatísticas.
        
        Args:
            execution_id: ID da execução
            status: Status final (COMPLETED, FAILED, etc.)
            stats: Estatísticas da execução
            error_details: Detalhes de erro se houver
        """
        try:
            async with self.async_session() as session:
                stmt = select(ScrapingExecutionModel).where(ScrapingExecutionModel.id == execution_id)
                result = await session.execute(stmt)
                execution = result.scalar_one_or_none()
                
                if execution:
                    execution.status = ScrapingExecutionStatusEnum(status)
                    execution.finished_at = datetime.now()
                    execution.execution_time_seconds = int((execution.finished_at - execution.started_at).total_seconds())
                    
                    # Atualizar estatísticas
                    execution.publications_found = stats.get('found', 0)
                    execution.publications_new = stats.get('new', 0)
                    execution.publications_duplicated = stats.get('duplicated', 0)
                    execution.publications_failed = stats.get('failed', 0)
                    execution.publications_saved = stats.get('saved', 0)
                    
                    if error_details:
                        execution.error_details = error_details
                    
                    await session.commit()
                    logger.info(f"Execução de scraping finalizada: {execution_id} - Status: {status}")
                
        except Exception as e:
            logger.error(f"Erro ao finalizar execução de scraping: {str(e)}")
            raise DatabaseException("finish_scraping_execution", str(e))
    
    async def save_publication(self, publication: Publication) -> Publication:
        """
        Salva uma publicação no banco de dados.
        
        Args:
            publication: Publicação a ser salva
            
        Returns:
            Publicação salva com ID atualizado
            
        Raises:
            DatabaseException: Se houver erro na operação de salvamento
            ValidationException: Se dados da publicação estiverem inválidos
        """
        try:
            async with self.async_session() as session:
                model = PublicationModel.from_entity(publication, self.current_execution_id)
                session.add(model)
                await session.commit()
                await session.refresh(model)
                
                logger.debug(f"Publicação salva: {model.id}")
                return model.to_entity()
                
        except Exception as e:
            logger.error(f"Erro ao salvar publicação: {str(e)}")
            raise DatabaseException("save_publication", str(e))
    
    async def save_publications(self, publications: List[Publication]) -> List[Publication]:
        """
        Salva múltiplas publicações em uma transação.
        
        Args:
            publications: Lista de publicações a serem salvas
            
        Returns:
            Lista de publicações salvas
            
        Raises:
            DatabaseException: Se houver erro na operação de salvamento
        """
        try:
            async with self.async_session() as session:
                models = [PublicationModel.from_entity(pub, self.current_execution_id) for pub in publications]
                session.add_all(models)
                await session.commit()
                
                # Refresh all models to get updated data
                for model in models:
                    await session.refresh(model)
                
                logger.info(f"Salvadas {len(models)} publicações")
                return [model.to_entity() for model in models]
                
        except Exception as e:
            logger.error(f"Erro ao salvar publicações: {str(e)}")
            raise DatabaseException("save_publications", str(e))
    
    async def find_by_id(self, publication_id: UUID) -> Optional[Publication]:
        """
        Busca uma publicação pelo ID.
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Publicação encontrada ou None
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        try:
            async with self.async_session() as session:
                stmt = select(PublicationModel).where(PublicationModel.id == publication_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                return model.to_entity() if model else None
                
        except Exception as e:
            logger.error(f"Erro ao buscar publicação por ID: {str(e)}")
            raise DatabaseException("find_by_id", str(e))
    
    async def find_by_process_number(self, process_number: ProcessNumber) -> Optional[Publication]:
        """
        Busca uma publicação pelo número do processo.
        
        Args:
            process_number: Número do processo
            
        Returns:
            Publicação encontrada ou None
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        try:
            async with self.async_session() as session:
                stmt = select(PublicationModel).where(PublicationModel.process_number == str(process_number))
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                return model.to_entity() if model else None
                
        except Exception as e:
            logger.error(f"Erro ao buscar publicação por número do processo: {str(e)}")
            raise DatabaseException("find_by_process_number", str(e))
    
    async def exists_by_process_number(self, process_number: ProcessNumber) -> bool:
        """
        Verifica se já existe uma publicação com o número do processo.
        
        Args:
            process_number: Número do processo a verificar
            
        Returns:
            True se já existe
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        try:
            async with self.async_session() as session:
                stmt = select(exists().where(PublicationModel.process_number == str(process_number)))
                result = await session.execute(stmt)
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Erro ao verificar existência por número do processo: {str(e)}")
            raise DatabaseException("exists_by_process_number", str(e))
    
    async def update_status(self, publication_id: UUID, new_status: Status) -> bool:
        """
        Atualiza o status de uma publicação.
        
        Args:
            publication_id: ID da publicação
            new_status: Novo status
            
        Returns:
            True se atualização foi bem-sucedida
            
        Raises:
            DatabaseException: Se houver erro na atualização
        """
        try:
            async with self.async_session() as session:
                stmt = select(PublicationModel).where(PublicationModel.id == publication_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    # Mapear status do sistema Python para Prisma
                    status_mapping = {
                        Status.NEW: PublicationStatusEnum.NOVA,
                        Status.READ: PublicationStatusEnum.LIDA,
                        Status.SENT_TO_LAWYER: PublicationStatusEnum.ENVIADA_PARA_ADV,
                        Status.COMPLETED: PublicationStatusEnum.CONCLUIDA
                    }
                    
                    model.status = status_mapping.get(new_status, PublicationStatusEnum.NOVA)
                    model.updated_at = datetime.now()
                    
                    await session.commit()
                    logger.debug(f"Status da publicação {publication_id} atualizado para {new_status}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status da publicação: {str(e)}")
            raise DatabaseException("update_status", str(e))
    
    async def find_by_status(self, status: Status, limit: Optional[int] = None) -> List[Publication]:
        """
        Busca publicações por status.
        
        Args:
            status: Status das publicações a buscar
            limit: Limite de resultados
            
        Returns:
            Lista de publicações encontradas
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        try:
            async with self.async_session() as session:
                # Mapear status do sistema Python para Prisma
                status_mapping = {
                    Status.NEW: PublicationStatusEnum.NOVA,
                    Status.READ: PublicationStatusEnum.LIDA,
                    Status.SENT_TO_LAWYER: PublicationStatusEnum.ENVIADA_PARA_ADV,
                    Status.COMPLETED: PublicationStatusEnum.CONCLUIDA
                }
                
                prisma_status = status_mapping.get(status, PublicationStatusEnum.NOVA)
                stmt = select(PublicationModel).where(PublicationModel.status == prisma_status)
                
                if limit:
                    stmt = stmt.limit(limit)
                
                result = await session.execute(stmt)
                models = result.scalars().all()
                
                return [model.to_entity() for model in models]
                
        except Exception as e:
            logger.error(f"Erro ao buscar publicações por status: {str(e)}")
            raise DatabaseException("find_by_status", str(e))
    
    async def count_by_status(self, status: Status) -> int:
        """
        Conta publicações por status.
        
        Args:
            status: Status a contar
            
        Returns:
            Número de publicações com o status
            
        Raises:
            DatabaseException: Se houver erro na consulta
        """
        try:
            async with self.async_session() as session:
                # Mapear status do sistema Python para Prisma
                status_mapping = {
                    Status.NEW: PublicationStatusEnum.NOVA,
                    Status.READ: PublicationStatusEnum.LIDA,
                    Status.SENT_TO_LAWYER: PublicationStatusEnum.ENVIADA_PARA_ADV,
                    Status.COMPLETED: PublicationStatusEnum.CONCLUIDA
                }
                
                prisma_status = status_mapping.get(status, PublicationStatusEnum.NOVA)
                stmt = select(PublicationModel).where(PublicationModel.status == prisma_status)
                result = await session.execute(stmt)
                models = result.scalars().all()
                
                return len(models)
                
        except Exception as e:
            logger.error(f"Erro ao contar publicações por status: {str(e)}")
            raise DatabaseException("count_by_status", str(e))
    
    async def close(self) -> None:
        """Fecha as conexões com o banco de dados."""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("Conexões do repositório fechadas")
        except Exception as e:
            logger.error(f"Erro ao fechar conexões: {str(e)}")