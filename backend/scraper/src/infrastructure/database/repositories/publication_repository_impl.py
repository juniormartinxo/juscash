from typing import List, Optional, Dict, Any
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from loguru import logger

from src.domain.repositories.publication_repository import PublicationRepository
from src.domain.entities.publication import Publication as PublicationEntity, Lawyer
from src.infrastructure.database.models import (
    Publication as PublicationModel,
    PublicationStatus,
)
from src.infrastructure.database.config import get_db_config


class PostgreSQLPublicationRepository(PublicationRepository):
    """Implementação concreta (Adapter) do repositório de publicações para PostgreSQL"""

    def __init__(self):
        self._db_config = None

    @property
    def db_config(self):
        """Lazy loading da configuração do banco"""
        if self._db_config is None:
            self._db_config = get_db_config()
        return self._db_config

    def save(self, publication: PublicationEntity) -> PublicationEntity:
        """Salva uma publicação no banco de dados"""
        try:
            with self.db_config.get_session() as session:
                # Verifica se já existe uma publicação com o mesmo número de processo
                existing = (
                    session.query(PublicationModel)
                    .filter(
                        PublicationModel.process_number == publication.process_number
                    )
                    .first()
                )

                if existing:
                    raise ValueError(
                        f"Publicação com número de processo {publication.process_number} já existe"
                    )

                # Converte lawyers para formato JSON
                lawyers_json = (
                    [lawyer.to_dict() for lawyer in publication.lawyers]
                    if publication.lawyers
                    else None
                )

                # Cria o modelo SQLAlchemy
                db_publication = PublicationModel(
                    id=publication.id,
                    process_number=publication.process_number,
                    publication_date=publication.publication_date,
                    availability_date=publication.availability_date,
                    authors=publication.authors,
                    defendant=publication.defendant,
                    lawyers=lawyers_json,
                    gross_value=publication.gross_value,
                    net_value=publication.net_value,
                    interest_value=publication.interest_value,
                    attorney_fees=publication.attorney_fees,
                    content=publication.content,
                    status=PublicationStatus(publication.status),
                )

                session.add(db_publication)
                session.flush()  # Para obter o ID gerado

                # Atualiza a entidade com os timestamps
                publication.created_at = db_publication.created_at
                publication.updated_at = db_publication.updated_at

                logger.info(
                    f"Publicação salva com sucesso: {publication.process_number}"
                )
                return publication

        except IntegrityError as e:
            logger.error(f"Erro de integridade ao salvar publicação: {e}")
            raise ValueError(
                f"Publicação com número de processo {publication.process_number} já existe"
            )
        except Exception as e:
            logger.error(f"Erro ao salvar publicação: {e}")
            raise

    def find_by_process_number(
        self, process_number: str
    ) -> Optional[PublicationEntity]:
        """Busca uma publicação pelo número do processo"""
        try:
            with self.db_config.get_session() as session:
                db_publication = (
                    session.query(PublicationModel)
                    .filter(PublicationModel.process_number == process_number)
                    .first()
                )

                if db_publication:
                    return self._model_to_entity(db_publication)
                return None

        except Exception as e:
            logger.error(
                f"Erro ao buscar publicação por número de processo {process_number}: {e}"
            )
            raise

    def find_by_id(self, publication_id: str) -> Optional[PublicationEntity]:
        """Busca uma publicação pelo ID"""
        try:
            with self.db_config.get_session() as session:
                db_publication = (
                    session.query(PublicationModel)
                    .filter(PublicationModel.id == publication_id)
                    .first()
                )

                if db_publication:
                    return self._model_to_entity(db_publication)
                return None

        except Exception as e:
            logger.error(f"Erro ao buscar publicação por ID {publication_id}: {e}")
            raise

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[PublicationEntity]:
        """Busca todas as publicações com paginação e filtros opcionais"""
        try:
            with self.db_config.get_session() as session:
                query = session.query(PublicationModel)

                # Aplica filtros se fornecidos
                if filters:
                    query = self._apply_filters(query, filters)

                # Aplica ordenação (mais recentes primeiro)
                query = query.order_by(PublicationModel.created_at.desc())

                # Aplica paginação
                db_publications = query.offset(offset).limit(limit).all()

                return [self._model_to_entity(pub) for pub in db_publications]

        except Exception as e:
            logger.error(f"Erro ao buscar publicações: {e}")
            raise

    def update_status(self, publication_id: str, new_status: str) -> bool:
        """Atualiza o status de uma publicação"""
        try:
            with self.db_config.get_session() as session:
                db_publication = (
                    session.query(PublicationModel)
                    .filter(PublicationModel.id == publication_id)
                    .first()
                )

                if not db_publication:
                    logger.warning(f"Publicação com ID {publication_id} não encontrada")
                    return False

                # Valida o novo status
                try:
                    new_status_enum = PublicationStatus(new_status)
                except ValueError:
                    logger.error(f"Status inválido: {new_status}")
                    return False

                db_publication.status = new_status_enum
                db_publication.updated_at = func.now()

                logger.info(
                    f"Status da publicação {publication_id} atualizado para {new_status}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Erro ao atualizar status da publicação {publication_id}: {e}"
            )
            raise

    def exists_by_process_number(self, process_number: str) -> bool:
        """Verifica se uma publicação já existe pelo número do processo"""
        try:
            with self.db_config.get_session() as session:
                exists = (
                    session.query(PublicationModel)
                    .filter(PublicationModel.process_number == process_number)
                    .first()
                    is not None
                )

                return exists

        except Exception as e:
            logger.error(
                f"Erro ao verificar existência da publicação {process_number}: {e}"
            )
            raise

    def count_by_filters(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta o número de publicações que atendem aos filtros"""
        try:
            with self.db_config.get_session() as session:
                query = session.query(func.count(PublicationModel.id))

                if filters:
                    query = self._apply_filters(query, filters)

                return query.scalar()

        except Exception as e:
            logger.error(f"Erro ao contar publicações: {e}")
            raise

    def delete_by_id(self, publication_id: str) -> bool:
        """Remove uma publicação pelo ID"""
        try:
            with self.db_config.get_session() as session:
                deleted_count = (
                    session.query(PublicationModel)
                    .filter(PublicationModel.id == publication_id)
                    .delete()
                )

                if deleted_count > 0:
                    logger.info(f"Publicação {publication_id} removida com sucesso")
                    return True
                else:
                    logger.warning(f"Publicação com ID {publication_id} não encontrada")
                    return False

        except Exception as e:
            logger.error(f"Erro ao remover publicação {publication_id}: {e}")
            raise

    def _model_to_entity(self, db_publication: PublicationModel) -> PublicationEntity:
        """Converte um modelo SQLAlchemy para entidade de domínio"""
        # Converte lawyers JSON para lista de objetos Lawyer
        lawyers = []
        if db_publication.lawyers:
            for lawyer_data in db_publication.lawyers:
                lawyers.append(
                    Lawyer(
                        name=lawyer_data.get("name", ""), oab=lawyer_data.get("oab", "")
                    )
                )

        return PublicationEntity(
            id=db_publication.id,
            process_number=db_publication.process_number,
            publication_date=db_publication.publication_date,
            availability_date=db_publication.availability_date,
            authors=db_publication.authors or [],
            defendant=db_publication.defendant,
            lawyers=lawyers,
            gross_value=db_publication.gross_value,
            net_value=db_publication.net_value,
            interest_value=db_publication.interest_value,
            attorney_fees=db_publication.attorney_fees,
            content=db_publication.content,
            status=db_publication.status.value,
            created_at=db_publication.created_at,
            updated_at=db_publication.updated_at,
        )

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Aplica filtros à query"""
        if "status" in filters:
            query = query.filter(
                PublicationModel.status == PublicationStatus(filters["status"])
            )

        if "process_number" in filters:
            query = query.filter(
                PublicationModel.process_number.ilike(f"%{filters['process_number']}%")
            )

        if "availability_date_from" in filters:
            query = query.filter(
                PublicationModel.availability_date >= filters["availability_date_from"]
            )

        if "availability_date_to" in filters:
            query = query.filter(
                PublicationModel.availability_date <= filters["availability_date_to"]
            )

        if "search_term" in filters:
            search_term = f"%{filters['search_term']}%"
            query = query.filter(
                or_(
                    PublicationModel.content.ilike(search_term),
                    PublicationModel.process_number.ilike(search_term),
                    func.array_to_string(PublicationModel.authors, ",").ilike(
                        search_term
                    ),
                )
            )

        return query
