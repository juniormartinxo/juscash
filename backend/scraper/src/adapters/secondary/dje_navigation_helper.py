"""
Arquivo: src/adapters/secondary/dje_navigation_helper.py

Helper principal para navegação e orchestração de operações no DJE.
Segue princípios da Arquitetura Hexagonal como componente de infraestrutura.

Responsabilidades:
- Orchestração do fluxo completo de scraping
- Coordenação entre search handler e content parser
- Gerenciamento de navegação entre páginas
- Implementação de estratégias de retry e error handling
"""

from typing import List, Optional, Dict, Any, Iterator
from datetime import datetime
from playwright.async_api import Page

from src.core.entities.publication import Publication
from src.shared.value_objects import ScrapingCriteria, DJEUrl
from src.shared.exceptions import (
    NavigationException, ParsingException, BrowserException, TimeoutException
)
from src.shared.logger import get_logger

from .dje_search_handler import DJEAdvancedSearchHandler
from .dje_content_parser import DJEContentParser

logger = get_logger(__name__)


class DJENavigationHelper:
    """
    Helper principal para navegação no DJE.
    
    Responsabilidade: Agregar e coordenar os diferentes handlers especializados
    para fornecer uma interface unificada de scraping do DJE.
    
    Princípios da Arquitetura Hexagonal:
    - Componente de infraestrutura (adapter secundário)
    - Orchestração de operações complexas
    - Interface simplificada para o adapter principal
    - Encapsulamento da complexidade específica do DJE
    """
    
    def __init__(self, page: Page):
        """
        Inicializa o helper de navegação.
        
        Args:
            page: Instância da página Playwright
        """
        self.page = page
        self.search_handler = DJEAdvancedSearchHandler(page)
        self.content_parser = DJEContentParser(page)
        
        # Configurações do helper
        self.config = {
            'max_retries': 3,
            'retry_delay': 2000,  # ms
            'max_pages_per_session': 10,
            'max_publications_per_page': 50,
            'enable_pagination': True,
            'enable_detail_extraction': False  # Para otimização de performance
        }
        
        # Estado do scraping
        self.session_stats = {
            'pages_processed': 0,
            'publications_found': 0,
            'publications_extracted': 0,
            'errors_count': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def execute_full_scraping_flow(self, 
                                       criteria: ScrapingCriteria,
                                       max_publications: Optional[int] = None) -> List[Publication]:
        """
        Executa o fluxo completo de scraping do DJE.
        
        Fluxo:
        1. Executa pesquisa avançada
        2. Extrai publicações da primeira página
        3. Navega por páginas adicionais (se habilitado)
        4. Consolida resultados
        
        Args:
            criteria: Critérios de scraping
            max_publications: Limite máximo de publicações
            
        Returns:
            List[Publication]: Publicações extraídas e validadas
            
        Raises:
            NavigationException: Se erro na navegação
            ParsingException: Se erro na extração
        """
        logger.info("🚀 Iniciando fluxo completo de scraping do DJE...")
        
        # Inicializar estatísticas
        self.session_stats['start_time'] = datetime.now()
        self.session_stats['pages_processed'] = 0
        self.session_stats['publications_found'] = 0
        self.session_stats['publications_extracted'] = 0
        self.session_stats['errors_count'] = 0
        
        all_publications: List[Publication] = []
        
        try:
            # === FASE 1: EXECUTAR PESQUISA ===
            logger.info("📍 Fase 1: Executando pesquisa avançada...")
            search_success = await self._execute_search_with_retry(criteria)
            
            if not search_success:
                raise NavigationException("Falha na pesquisa avançada após múltiplas tentativas")
            
            # === FASE 2: PROCESSAR PÁGINAS DE RESULTADOS ===
            logger.info("📍 Fase 2: Processando páginas de resultados...")
            
            page_count = 0
            has_more_pages = True
            
            while (has_more_pages and 
                   page_count < self.config['max_pages_per_session'] and
                   (not max_publications or len(all_publications) < max_publications)):
                
                page_count += 1
                logger.info(f"📄 Processando página {page_count}...")
                
                # Extrair publicações da página atual
                page_publications = await self._extract_publications_from_current_page(
                    criteria, 
                    max_publications - len(all_publications) if max_publications else None
                )
                
                if page_publications:
                    all_publications.extend(page_publications)
                    self.session_stats['publications_extracted'] += len(page_publications)
                    logger.info(f"✅ {len(page_publications)} publicações extraídas da página {page_count}")
                else:
                    logger.warning(f"⚠️ Nenhuma publicação extraída da página {page_count}")
                
                self.session_stats['pages_processed'] += 1
                
                # Verificar se deve continuar para próxima página
                if self.config['enable_pagination']:
                    has_more_pages = await self._navigate_to_next_page_safely()
                else:
                    has_more_pages = False
                
                # Verificar limite de publicações
                if max_publications and len(all_publications) >= max_publications:
                    logger.info(f"Limite de {max_publications} publicações atingido")
                    break
            
            # === FASE 3: FINALIZAÇÃO ===
            self._finalize_session_stats()
            
            logger.info(f"🎉 Scraping concluído:")
            logger.info(f"  📊 Páginas processadas: {self.session_stats['pages_processed']}")
            logger.info(f"  📋 Publicações extraídas: {len(all_publications)}")
            logger.info(f"  ⏱️ Tempo total: {self._get_session_duration()}")
            
            return all_publications
            
        except Exception as e:
            self.session_stats['errors_count'] += 1
            self._finalize_session_stats()
            
            logger.error(f"❌ Erro no fluxo de scraping: {str(e)}")
            raise
    
    async def _execute_search_with_retry(self, criteria: ScrapingCriteria) -> bool:
        """
        Executa pesquisa com retry automático.
        
        Args:
            criteria: Critérios de scraping
            
        Returns:
            bool: True se pesquisa foi bem-sucedida
        """
        for attempt in range(self.config['max_retries']):
            try:
                logger.info(f"🔍 Tentativa de pesquisa {attempt + 1}/{self.config['max_retries']}")
                
                success = await self.search_handler.execute_project_search()
                
                if success:
                    logger.info("✅ Pesquisa executada com sucesso")
                    return True
                else:
                    logger.warning(f"⚠️ Pesquisa falhou na tentativa {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Erro na pesquisa (tentativa {attempt + 1}): {str(e)}")
                self.session_stats['errors_count'] += 1
            
            # Aguardar antes da próxima tentativa (exceto na última)
            if attempt < self.config['max_retries'] - 1:
                logger.info(f"⏳ Aguardando {self.config['retry_delay']}ms antes da próxima tentativa...")
                await self.page.wait_for_timeout(self.config['retry_delay'])
        
        return False
    
    async def _extract_publications_from_current_page(self, 
                                                    criteria: ScrapingCriteria,
                                                    max_publications: Optional[int] = None) -> List[Publication]:
        """
        Extrai publicações da página atual com tratamento de erro.
        
        Args:
            criteria: Critérios de scraping
            max_publications: Limite para esta página
            
        Returns:
            List[Publication]: Publicações extraídas
        """
        try:
            # Aguardar página carregar
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Extrair publicações usando o content parser
            publications = await self.content_parser.extract_publications_from_results(
                criteria, 
                max_publications or self.config['max_publications_per_page']
            )
            
            return publications
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair publicações da página atual: {str(e)}")
            self.session_stats['errors_count'] += 1
            return []
    
    async def _navigate_to_next_page_safely(self) -> bool:
        """
        Navega para próxima página com tratamento de erro.
        
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            # Verificar se há próxima página
            pagination_info = await self.content_parser.check_pagination()
            
            if not pagination_info.get('has_next_page'):
                logger.info("📄 Não há mais páginas para processar")
                return False
            
            # Navegar para próxima página
            success = await self.content_parser.navigate_to_next_page()
            
            if success:
                logger.info("➡️ Navegação para próxima página realizada")
                # Aguardar carregamento
                await self.page.wait_for_load_state('networkidle', timeout=30000)
                return True
            else:
                logger.warning("⚠️ Falha na navegação para próxima página")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao navegar para próxima página: {str(e)}")
            self.session_stats['errors_count'] += 1
            return False
    
    async def execute_targeted_publication_extraction(self, 
                                                    criteria: ScrapingCriteria,
                                                    publication_links: List[str]) -> List[Publication]:
        """
        Extrai publicações específicas a partir de lista de links.
        
        Args:
            criteria: Critérios de validação
            publication_links: URLs das publicações específicas
            
        Returns:
            List[Publication]: Publicações extraídas
        """
        logger.info(f"🎯 Extraindo {len(publication_links)} publicações específicas...")
        
        publications = []
        
        for i, link in enumerate(publication_links):
            try:
                logger.info(f"📄 Processando publicação {i+1}/{len(publication_links)}")
                
                # Navegar para página específica
                success = await self.content_parser.navigate_to_publication_detail(link)
                
                if not success:
                    logger.warning(f"⚠️ Falha ao navegar para {link}")
                    continue
                
                # Extrair publicação detalhada
                publication = await self.content_parser.extract_detailed_publication(criteria)
                
                if publication:
                    publications.append(publication)
                    logger.info(f"✅ Publicação extraída: {publication.process_number}")
                else:
                    logger.warning(f"⚠️ Não foi possível extrair publicação de {link}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {link}: {str(e)}")
                self.session_stats['errors_count'] += 1
                continue
        
        logger.info(f"🎉 Extração direcionada concluída: {len(publications)} publicações")
        return publications
    
    async def get_search_results_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo dos resultados da pesquisa atual.
        
        Returns:
            Dict com resumo dos resultados
        """
        try:
            # Obter metadados dos resultados
            result_metadata = await self.content_parser._extract_result_metadata()
            
            # Obter informações de paginação
            pagination_info = await self.content_parser.check_pagination()
            
            # Obter links de publicações
            publication_links = await self.content_parser.extract_publication_links()
            
            summary = {
                'result_metadata': result_metadata,
                'pagination_info': pagination_info,
                'publication_links_count': len(publication_links),
                'publication_links': publication_links[:10],  # Primeiros 10 para preview
                'session_stats': self.session_stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {'error': str(e)}
    
    async def execute_search_only(self, criteria: ScrapingCriteria) -> bool:
        """
        Executa apenas a pesquisa, sem extração de conteúdo.
        
        Útil para validação de parâmetros ou contagem de resultados.
        
        Args:
            criteria: Critérios de scraping
            
        Returns:
            bool: True se pesquisa foi bem-sucedida
        """
        logger.info("🔍 Executando apenas pesquisa (sem extração)...")
        
        try:
            success = await self._execute_search_with_retry(criteria)
            
            if success:
                # Obter resumo dos resultados
                summary = await self.get_search_results_summary()
                logger.info("✅ Pesquisa executada - Resumo disponível")
                logger.info(f"📊 Resultados encontrados: {summary.get('result_metadata', {}).get('total_results', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro na execução da pesquisa: {str(e)}")
            return False
    
    def configure_scraping_session(self, config_updates: Dict[str, Any]) -> None:
        """
        Configura parâmetros da sessão de scraping.
        
        Args:
            config_updates: Dicionário com configurações a atualizar
        """
        logger.info("⚙️ Configurando sessão de scraping...")
        
        valid_configs = {
            'max_retries', 'retry_delay', 'max_pages_per_session',
            'max_publications_per_page', 'enable_pagination', 'enable_detail_extraction'
        }
        
        for key, value in config_updates.items():
            if key in valid_configs:
                old_value = self.config.get(key)
                self.config[key] = value
                logger.info(f"  {key}: {old_value} → {value}")
            else:
                logger.warning(f"⚠️ Configuração inválida ignorada: {key}")
        
        logger.info("✅ Configuração da sessão atualizada")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da sessão atual.
        
        Returns:
            Dict com estatísticas detalhadas
        """
        stats = self.session_stats.copy()
        
        # Calcular métricas adicionais
        if stats['start_time']:
            duration = self._get_session_duration()
            stats['duration_seconds'] = duration.total_seconds()
            stats['duration_formatted'] = str(duration)
            
            # Taxa de sucesso
            if stats['pages_processed'] > 0:
                stats['success_rate'] = (stats['pages_processed'] - stats['errors_count']) / stats['pages_processed']
                stats['publications_per_page'] = stats['publications_extracted'] / stats['pages_processed']
            else:
                stats['success_rate'] = 0.0
                stats['publications_per_page'] = 0.0
        
        return stats
    
    def reset_session_statistics(self) -> None:
        """Reset das estatísticas da sessão."""
        logger.info("🔄 Resetando estatísticas da sessão...")
        
        self.session_stats = {
            'pages_processed': 0,
            'publications_found': 0,
            'publications_extracted': 0,
            'errors_count': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("✅ Estatísticas resetadas")
    
    def _finalize_session_stats(self) -> None:
        """Finaliza estatísticas da sessão."""
        self.session_stats['end_time'] = datetime.now()
    
    def _get_session_duration(self) -> datetime:
        """
        Calcula duração da sessão.
        
        Returns:
            timedelta com duração da sessão
        """
        if not self.session_stats['start_time']:
            return datetime.now() - datetime.now()  # Zero duration
        
        end_time = self.session_stats['end_time'] or datetime.now()
        return end_time - self.session_stats['start_time']
    
    async def validate_search_criteria(self, criteria: ScrapingCriteria) -> Dict[str, Any]:
        """
        Valida critérios de pesquisa antes da execução.
        
        Args:
            criteria: Critérios a serem validados
            
        Returns:
            Dict com resultado da validação
        """
        logger.info("🔍 Validando critérios de pesquisa...")
        
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        try:
            # Validar termos de busca
            search_terms = getattr(criteria, 'search_terms', [])
            if not search_terms:
                validation_result['warnings'].append("Nenhum termo de busca especificado")
                validation_result['suggestions'].append("Adicionar termos específicos pode melhorar a precisão")
            
            # Validar data início
            start_date = getattr(criteria, 'start_date', None)
            if start_date and start_date < datetime(2025, 3, 17):
                validation_result['warnings'].append("Data anterior ao início do projeto (17/03/2025)")
            
            # Validar se tem critérios mínimos para RPV + INSS
            content_check = criteria.get_search_string() if hasattr(criteria, 'get_search_string') else ""
            if 'rpv' not in content_check.lower() or 'inss' not in content_check.lower():
                validation_result['warnings'].append("Critérios podem não incluir termos obrigatórios do projeto")
                validation_result['suggestions'].append("Verificar se inclui 'RPV' e 'INSS'")
            
            logger.info(f"✅ Validação concluída - Válido: {validation_result['is_valid']}")
            if validation_result['warnings']:
                logger.warning(f"⚠️ {len(validation_result['warnings'])} avisos encontrados")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Erro na validação: {str(e)}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Erro durante validação: {str(e)}")
            return validation_result
    
    async def execute_health_check(self) -> Dict[str, Any]:
        """
        Executa verificação de saúde dos componentes.
        
        Returns:
            Dict com status dos componentes
        """
        logger.info("🏥 Executando health check dos componentes...")
        
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check da página
        try:
            page_url = self.page.url
            page_title = await self.page.title()
            
            health_status['components']['page'] = {
                'status': 'healthy',
                'url': page_url,
                'title': page_title
            }
        except Exception as e:
            health_status['components']['page'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check do search handler
        try:
            search_metadata = await self.search_handler.get_search_metadata()
            health_status['components']['search_handler'] = {
                'status': 'healthy',
                'metadata': search_metadata
            }
        except Exception as e:
            health_status['components']['search_handler'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check do content parser
        try:
            # Teste simples do parser
            test_content = "Teste básico do parser"
            is_valid = self.content_parser._is_valid_publication_content(test_content)
            
            health_status['components']['content_parser'] = {
                'status': 'healthy',
                'test_result': f"Validation test: {is_valid}"
            }
        except Exception as e:
            health_status['components']['content_parser'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'
        
        logger.info(f"🏥 Health check concluído - Status: {health_status['overall_status']}")
        return health_status
    
    async def cleanup_session(self) -> None:
        """
        Limpa recursos da sessão atual.
        """
        logger.info("🧹 Limpando recursos da sessão...")
        
        try:
            # Finalizar estatísticas se não finalizadas
            if not self.session_stats.get('end_time'):
                self._finalize_session_stats()
            
            # Log final das estatísticas
            final_stats = self.get_session_statistics()
            logger.info("📊 Estatísticas finais da sessão:")
            logger.info(f"  📄 Páginas processadas: {final_stats['pages_processed']}")
            logger.info(f"  📋 Publicações extraídas: {final_stats['publications_extracted']}")
            logger.info(f"  ❌ Erros: {final_stats['errors_count']}")
            logger.info(f"  ⏱️ Duração: {final_stats.get('duration_formatted', 'N/A')}")
            logger.info(f"  📈 Taxa de sucesso: {final_stats.get('success_rate', 0):.2%}")
            
            logger.info("✅ Limpeza da sessão concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro durante limpeza: {str(e)}")
    
    # === MÉTODOS DE CONVENIÊNCIA ===
    
    async def quick_search_and_count(self, criteria: ScrapingCriteria) -> int:
        """
        Executa pesquisa rápida e retorna apenas contagem de resultados.
        
        Args:
            criteria: Critérios de pesquisa
            
        Returns:
            int: Número de resultados encontrados
        """
        try:
            success = await self.execute_search_only(criteria)
            
            if success:
                summary = await self.get_search_results_summary()
                return summary.get('result_metadata', {}).get('total_results', 0)
            
            return 0
            
        except Exception as e:
            logger.error(f"Erro na contagem rápida: {e}")
            return 0
    
    async def extract_sample_publications(self, 
                                        criteria: ScrapingCriteria, 
                                        sample_size: int = 5) -> List[Publication]:
        """
        Extrai uma amostra pequena de publicações para teste.
        
        Args:
            criteria: Critérios de pesquisa
            sample_size: Tamanho da amostra
            
        Returns:
            List[Publication]: Amostra de publicações
        """
        logger.info(f"🧪 Extraindo amostra de {sample_size} publicações...")
        
        # Temporariamente desabilitar paginação
        original_pagination = self.config['enable_pagination']
        self.config['enable_pagination'] = False
        
        try:
            publications = await self.execute_full_scraping_flow(criteria, sample_size)
            return publications[:sample_size]
            
        finally:
            # Restaurar configuração original
            self.config['enable_pagination'] = original_pagination
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da configuração atual.
        
        Returns:
            Dict com configuração atual
        """
        return {
            'config': self.config.copy(),
            'session_stats': self.session_stats.copy(),
            'components': {
                'search_handler': type(self.search_handler).__name__,
                'content_parser': type(self.content_parser).__name__
            },
            'timestamp': datetime.now().isoformat()
        }