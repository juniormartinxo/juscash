from typing import List, Optional, Dict, Any
from datetime import date
from loguru import logger

from src.domain.entities.publication import Publication
from src.domain.repositories.publication_repository import PublicationRepository
from src.infrastructure.database.repositories.publication_repository_impl import PostgreSQLPublicationRepository


class DatabaseService:
    """Serviço de aplicação para operações de banco de dados"""
    
    def __init__(self, repository: Optional[PublicationRepository] = None):
        """
        Inicializa o serviço com um repositório.
        Se nenhum repositório for fornecido, usa a implementação PostgreSQL padrão.
        """
        self._repository = repository or PostgreSQLPublicationRepository()
    
    def save_publication(self, publication_data: Dict[str, Any]) -> Publication:
        """
        Salva uma nova publicação no banco de dados
        
        Args:
            publication_data: Dicionário com os dados da publicação
            
        Returns:
            Publication: A entidade da publicação salva
            
        Raises:
            ValueError: Se os dados são inválidos ou se a publicação já existe
        """
        try:
            # Cria a entidade de domínio a partir dos dados
            publication = self._create_publication_entity(publication_data)
            
            # Verifica se a publicação já existe
            if self._repository.exists_by_process_number(publication.process_number):
                logger.info(f"Publicação já existe: {publication.process_number}")
                return self._repository.find_by_process_number(publication.process_number)
            
            # Salva a publicação
            saved_publication = self._repository.save(publication)
            logger.info(f"Nova publicação salva: {saved_publication.process_number}")
            
            return saved_publication
            
        except Exception as e:
            logger.error(f"Erro ao salvar publicação: {e}")
            raise
    
    def get_publication_by_process_number(self, process_number: str) -> Optional[Publication]:
        """
        Busca uma publicação pelo número do processo
        
        Args:
            process_number: Número do processo
            
        Returns:
            Publication ou None se não encontrada
        """
        try:
            return self._repository.find_by_process_number(process_number)
        except Exception as e:
            logger.error(f"Erro ao buscar publicação por número de processo {process_number}: {e}")
            raise
    
    def get_publications(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Publication]:
        """
        Busca publicações com paginação e filtros
        
        Args:
            limit: Número máximo de publicações a retornar
            offset: Número de publicações a pular
            filters: Filtros opcionais
            
        Returns:
            Lista de publicações
        """
        try:
            return self._repository.find_all(limit=limit, offset=offset, filters=filters)
        except Exception as e:
            logger.error(f"Erro ao buscar publicações: {e}")
            raise
    
    def update_publication_status(self, publication_id: str, new_status: str) -> bool:
        """
        Atualiza o status de uma publicação
        
        Args:
            publication_id: ID da publicação
            new_status: Novo status
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            return self._repository.update_status(publication_id, new_status)
        except Exception as e:
            logger.error(f"Erro ao atualizar status da publicação {publication_id}: {e}")
            raise
    
    def count_publications(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Conta o número de publicações que atendem aos filtros
        
        Args:
            filters: Filtros opcionais
            
        Returns:
            Número total de publicações
        """
        try:
            return self._repository.count_by_filters(filters)
        except Exception as e:
            logger.error(f"Erro ao contar publicações: {e}")
            raise
    
    def publication_exists(self, process_number: str) -> bool:
        """
        Verifica se uma publicação já existe pelo número do processo
        
        Args:
            process_number: Número do processo
            
        Returns:
            True se existe, False caso contrário
        """
        try:
            return self._repository.exists_by_process_number(process_number)
        except Exception as e:
            logger.error(f"Erro ao verificar existência da publicação {process_number}: {e}")
            raise
    
    def delete_publication(self, publication_id: str) -> bool:
        """
        Remove uma publicação pelo ID
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        try:
            return self._repository.delete_by_id(publication_id)
        except Exception as e:
            logger.error(f"Erro ao remover publicação {publication_id}: {e}")
            raise
    
    def _create_publication_entity(self, data: Dict[str, Any]) -> Publication:
        """
        Cria uma entidade Publication a partir dos dados fornecidos
        
        Args:
            data: Dicionário com os dados da publicação
            
        Returns:
            Publication: Entidade criada
            
        Raises:
            ValueError: Se dados obrigatórios estão faltando
        """
        # Validação de campos obrigatórios
        required_fields = ['process_number', 'availability_date', 'authors', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Campo obrigatório '{field}' está faltando ou vazio")
        
        # Cria a entidade
        publication = Publication(
            process_number=data['process_number'],
            availability_date=data['availability_date'],
            authors=data['authors'] if isinstance(data['authors'], list) else [data['authors']],
            content=data['content'],
            publication_date=data.get('publication_date'),
            defendant=data.get('defendant', "Instituto Nacional do Seguro Social - INSS"),
            status=data.get('status', 'NOVA')
        )
        
        # Adiciona advogados se fornecidos
        if 'lawyers' in data and data['lawyers']:
            for lawyer_data in data['lawyers']:
                if isinstance(lawyer_data, dict) and 'name' in lawyer_data and 'oab' in lawyer_data:
                    publication.add_lawyer(lawyer_data['name'], lawyer_data['oab'])
        
        # Define valores monetários se fornecidos
        monetary_fields = {
            'gross_value': data.get('gross_value'),
            'net_value': data.get('net_value'),
            'interest_value': data.get('interest_value'),
            'attorney_fees': data.get('attorney_fees')
        }
        
        # Converte valores de reais para centavos se necessário
        for field, value in monetary_fields.items():
            if value is not None:
                if isinstance(value, (int, float)):
                    # Se o valor é um número, assume que está em reais e converte para centavos
                    setattr(publication, field, int(value * 100) if isinstance(value, float) else value)
                elif isinstance(value, str):
                    # Se é string, tenta converter
                    try:
                        float_value = float(value.replace(',', '.').replace('R$ ', '').strip())
                        setattr(publication, field, int(float_value * 100))
                    except ValueError:
                        logger.warning(f"Não foi possível converter o valor monetário '{field}': {value}")
        
        return publication