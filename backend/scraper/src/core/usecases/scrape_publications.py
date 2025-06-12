from typing import List, Optional
from datetime import datetime

from src.core.entities.publication import Publication
from src.core.ports.scraper_port import ScraperPort
from src.core.ports.database_port import DatabasePort
from src.core.ports.cache_port import CachePort
from src.shared.value_objects import ScrapingCriteria, DJEUrl, ProcessNumber, Status
from src.shared.exceptions import (
    DJEScrapingException, ValidationException, DatabaseException,
    RetryExhaustedException
)
from src.shared.logger import get_logger

logger = get_logger(__name__)


class ScrapePublicationsUseCase:
    """
    Caso de uso principal para scraping de publicações do DJE.
    
    Coordena todo o processo de extração, validação e persistência
    das publicações encontradas no Diário da Justiça Eletrônico.
    """
    
    def __init__(self, 
                 scraper: ScraperPort,
                 database: DatabasePort,
                 cache: Optional[CachePort] = None):
        """
        Inicializa o caso de uso.
        
        Args:
            scraper: Implementação do port de scraping
            database: Implementação do port de banco de dados
            cache: Implementação opcional do port de cache
        """
        self.scraper = scraper
        self.database = database
        self.cache = cache
        self._default_criteria = ScrapingCriteria(
            required_terms=("Instituto Nacional do Seguro Social", "INSS"),
            caderno="3",
            instancia="1", 
            local="Capital",
            parte="1"
        )
    
    async def execute(self, 
                     criteria: Optional[ScrapingCriteria] = None,
                     max_publications: Optional[int] = None,
                     skip_duplicates: bool = True) -> dict:
        """
        Executa o scraping completo das publicações.
        
        Args:
            criteria: Critérios de busca (usa padrão se não informado)
            max_publications: Limite máximo de publicações para processar
            skip_duplicates: Se deve pular publicações já existentes
            
        Returns:
            Dicionário com estatísticas da execução
            
        Raises:
            DJEScrapingException: Para qualquer erro durante o processo
        """
        execution_start = datetime.now()
        criteria = criteria or self._default_criteria
        
        stats = {
            'started_at': execution_start,
            'criteria': str(criteria),
            'publications_found': 0,
            'publications_new': 0,
            'publications_duplicated': 0,
            'publications_saved': 0,
            'publications_failed': 0,
            'errors': []
        }
        
        logger.info(f"Iniciando scraping com critérios: {criteria}")
        
        try:
            # 1. Verificar cache se disponível
            cache_key = f"scraping_{criteria.caderno}_{execution_start.date()}"
            if self.cache and await self.cache.exists(cache_key):
                logger.info("Execução já realizada hoje (encontrada no cache)")
                cached_stats = await self.cache.get(cache_key)
                return cached_stats or stats
            
            # 2. Inicializar scraper
            await self.scraper.initialize()
            logger.info("Scraper inicializado com sucesso")
            
            # 3. Navegar para DJE
            dje_url = DJEUrl()
            navigation_success = await self.scraper.navigate_to_dje(dje_url)
            if not navigation_success:
                raise DJEScrapingException("Falha na navegação inicial para o DJE")
            
            logger.info("Navegação para DJE realizada com sucesso")
            
            # 4. Navegar para caderno específico
            caderno_success = await self.scraper.navigate_to_caderno(criteria)
            if not caderno_success:
                raise DJEScrapingException(f"Falha ao acessar {criteria.get_caderno_description()}")
            
            logger.info(f"Acesso ao {criteria.get_caderno_description()} realizado")
            
            # 5. Extrair publicações
            publications = await self.scraper.extract_publications(criteria, max_publications)
            stats['publications_found'] = len(publications)
            
            logger.info(f"Encontradas {len(publications)} publicações para processar")
            
            # 6. Processar cada publicação
            for publication in publications:
                try:
                    await self._process_single_publication(publication, skip_duplicates, stats)
                except Exception as e:
                    logger.error(f"Erro ao processar publicação {publication.id}: {str(e)}")
                    stats['publications_failed'] += 1
                    stats['errors'].append({
                        'publication_id': str(publication.id),
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 7. Armazenar estatísticas no cache
            if self.cache:
                await self.cache.set(cache_key, stats)
            
            execution_end = datetime.now()
            execution_time = (execution_end - execution_start).total_seconds()
            
            stats['finished_at'] = execution_end
            stats['execution_time_seconds'] = execution_time
            
            logger.info(f"Scraping concluído em {execution_time:.2f}s")
            logger.info(f"Estatísticas: {stats['publications_new']} novas, "
                       f"{stats['publications_duplicated']} duplicadas, "
                       f"{stats['publications_failed']} falharam")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro durante execução do scraping: {str(e)}")
            stats['errors'].append({
                'general_error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise
            
        finally:
            # 8. Fechar scraper
            try:
                await self.scraper.close()
                logger.info("Scraper fechado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao fechar scraper: {str(e)}")
    
    async def _process_single_publication(self, 
                                        publication: Publication,
                                        skip_duplicates: bool,
                                        stats: dict) -> None:
        """
        Processa uma única publicação.
        
        Args:
            publication: Publicação a processar
            skip_duplicates: Se deve pular duplicatas
            stats: Dicionário de estatísticas para atualizar
        """
        try:
            # 1. Extrair detalhes completos
            detailed_publication = await self.scraper.extract_publication_details(publication)
            
            # 2. Validar dados extraídos
            if not detailed_publication.is_valid_for_processing():
                logger.warning(f"Publicação {detailed_publication.id} não tem dados suficientes")
                stats['publications_failed'] += 1
                return
            
            # 3. Verificar duplicata se solicitado
            if skip_duplicates and detailed_publication.process_number:
                exists = await self.database.exists_by_process_number(
                    detailed_publication.process_number
                )
                if exists:
                    logger.info(f"Publicação duplicada ignorada: {detailed_publication.process_number}")
                    stats['publications_duplicated'] += 1
                    return
            
            # 4. Garantir que réu seja sempre INSS (regra de negócio)
            detailed_publication.defendant = "Instituto Nacional do Seguro Social - INSS"
            detailed_publication.status = Status.NEW
            
            # 5. Salvar no banco de dados
            saved_publication = await self.database.save_publication(detailed_publication)
            stats['publications_new'] += 1
            stats['publications_saved'] += 1
            
            logger.info(f"Publicação salva: {saved_publication.process_number}")
            
        except DatabaseException as e:
            logger.error(f"Erro de banco ao processar publicação: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao processar publicação: {str(e)}")
            raise