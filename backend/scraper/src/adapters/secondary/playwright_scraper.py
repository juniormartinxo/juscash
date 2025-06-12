"""
Arquivo: src/adapters/secondary/playwright_scraper.py (VERSÃO ATUALIZADA)

Implementação do scraping do DJE usando Playwright com arquitetura modular.
Segue princípios da Arquitetura Hexagonal como adapter secundário.

VERSÃO ATUALIZADA: Integra os novos helpers modulares para pesquisa avançada,
parsing de conteúdo e navegação orchestrada.
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from src.core.entities.publication import Publication
from src.core.ports.scraper_port import ScraperPort
from src.shared.value_objects import ScrapingCriteria, DJEUrl, ProcessNumber, Status
from src.shared.exceptions import (
    BrowserException, NavigationException, ElementNotFoundException,
    TimeoutException, ParsingException, handle_exception
)
from src.shared.logger import get_logger

# === IMPORTS DOS NOVOS MÓDULOS ===
from .dje_navigation_helper import DJENavigationHelper
from .dje_search_handler import DJEAdvancedSearchHandler
from .dje_content_parser import DJEContentParser

logger = get_logger(__name__)


class PlaywrightScraperAdapter(ScraperPort):
    """
    Implementação do scraping do DJE usando Playwright (VERSÃO MODULAR).
    
    ATUALIZAÇÃO: Agora utiliza arquitetura modular com helpers especializados:
    - DJENavigationHelper: Orchestração do fluxo completo
    - DJEAdvancedSearchHandler: Pesquisas avançadas especializadas
    - DJEContentParser: Extração e parsing de conteúdo
    
    Responsabilidades principais:
    - Gerenciamento do ciclo de vida do browser
    - Interface com o domínio (Port implementation)
    - Delegação para helpers especializados
    - Tratamento de erros de infraestrutura
    """
    
    def __init__(self, 
                 headless: bool = False,
                 timeout: int = 30000,
                 user_agent: Optional[str] = None,
                 max_retries: int = 3):
        """
        Inicializa o adaptador Playwright com configuração modular.
        
        Args:
            headless: Se o browser deve rodar em modo headless
            timeout: Timeout padrão em milissegundos
            user_agent: User agent customizado
            max_retries: Número máximo de tentativas em caso de erro
        """
        # Configurar ambiente para WSL
        os.environ['DISPLAY'] = '0'
        os.environ['MOZ_ENABLE_WAYLAND'] = '0'
        os.environ['GDK_BACKEND'] = 'x11'
        
        self.headless = False
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.max_retries = max_retries
        
        # Atributos de controle do browser
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # === NOVOS HELPERS MODULARES ===
        self.dje_helper: Optional[DJENavigationHelper] = None
        self.search_handler: Optional[DJEAdvancedSearchHandler] = None
        self.content_parser: Optional[DJEContentParser] = None
        
        # Configurações específicas do adapter
        self.adapter_config = {
            'enable_detailed_logging': True,
            'enable_performance_metrics': True,
            'enable_automatic_retry': True,
            'enable_session_cleanup': True
        }
        
        # Métricas de performance
        self.performance_metrics = {
            'initialization_time': None,
            'total_scraping_time': None,
            'publications_per_second': 0.0,
            'error_rate': 0.0
        }
    
    async def initialize(self) -> None:
        """
        Inicializa o browser Playwright e helpers modulares.
        
        ATUALIZAÇÃO: Agora inicializa todos os helpers especializados
        após configurar o browser.
        
        Raises:
            BrowserException: Se erro na inicialização
        """
        start_time = datetime.now()
        
        try:
            logger.info("🚀 Inicializando Playwright Scraper (Versão Modular)...")
            
            # === CONFIGURAÇÃO DO AMBIENTE ===
            await self._configure_wsl_environment()
            
            # === INICIALIZAÇÃO DO PLAYWRIGHT ===
            self.playwright = await async_playwright().start()
            
            # === CONFIGURAÇÃO DO BROWSER ===
            browser_args = self._get_browser_args()
            
            self.browser = await self.playwright.firefox.launch(
                headless=self.headless,
                args=browser_args,
                slow_mo=100  # Para debug e estabilidade
            )
            
            # === CRIAÇÃO DO CONTEXTO ===
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1280, 'height': 720},
                java_script_enabled=True,
                ignore_https_errors=True
            )
            
            # === CRIAÇÃO DA PÁGINA ===
            self.page = await self.context.new_page()
            
            # Configurar timeouts
            self.page.set_default_timeout(self.timeout)
            self.page.set_default_navigation_timeout(self.timeout)
            
            # === INICIALIZAÇÃO DOS HELPERS MODULARES ===
            await self._initialize_helpers()
            
            # === TESTE DE FUNCIONAMENTO ===
            if not self.headless:
                await self._test_browser_functionality()
            
            # === MÉTRICAS DE PERFORMANCE ===
            self.performance_metrics['initialization_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info("✅ Playwright Scraper inicializado com sucesso")
            logger.info(f"⏱️ Tempo de inicialização: {self.performance_metrics['initialization_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Playwright: {str(e)}")
            await self._cleanup_on_error()
            raise BrowserException("initialize", str(e))
    
    async def _configure_wsl_environment(self) -> None:
        """Configura ambiente WSL para display gráfico."""
        logger.info("🔧 Configurando ambiente WSL...")
        
        # Configurar display
        os.environ['DISPLAY'] = ':0'
        
        # Verificar disponibilidade do display
        display_available = os.system('xdpyinfo >/dev/null 2>&1') == 0
        
        if not display_available:
            logger.warning("⚠️ Display não detectado - configurando automaticamente...")
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    content = f.read()
                
                import re
                match = re.search(r'nameserver\s+(\S+)', content)
                if match:
                    windows_ip = match.group(1)
                    os.environ['DISPLAY'] = f'{windows_ip}:0'
                    logger.info(f"🖥️ Display configurado para: {os.environ['DISPLAY']}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao configurar display automaticamente: {e}")
    
    def _get_browser_args(self) -> List[str]:
        """Retorna argumentos otimizados para o browser."""
        args = [
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ]
        
        if not self.headless:
            args.extend([
                '--new-instance',
                '--no-remote',
                '--display=' + os.environ.get('DISPLAY', ':0')
            ])
            
            # Forçar X11
            os.environ['MOZ_ENABLE_WAYLAND'] = '0'
            os.environ['GDK_BACKEND'] = 'x11'
        
        return args
    
    async def _initialize_helpers(self) -> None:
        """
        Inicializa todos os helpers modulares.
        
        NOVO MÉTODO: Centraliza a inicialização dos components modulares.
        """
        if not self.page:
            raise BrowserException("initialize_helpers", "Página não disponível")
        
        logger.info("🔧 Inicializando helpers modulares...")
        
        # Helper principal de navegação (orchestrador)
        self.dje_helper = DJENavigationHelper(self.page)
        
        # Helper especializado em pesquisa
        self.search_handler = DJEAdvancedSearchHandler(self.page)
        
        # Helper especializado em parsing
        self.content_parser = DJEContentParser(self.page)
        
        # Configurar session de scraping
        self.dje_helper.configure_scraping_session({
            'max_retries': self.max_retries,
            'enable_pagination': True,
            'max_pages_per_session': 5,  # Limitar para performance
            'max_publications_per_page': 30
        })
        
        logger.info("✅ Helpers modulares inicializados")
    
    async def _test_browser_functionality(self) -> None:
        """Testa funcionalidade básica do browser."""
        logger.info("🧪 Testando funcionalidade do browser...")
        
        try:
            await self.page.goto('about:blank')
            await self.page.wait_for_timeout(1000)
            
            title = await self.page.title()
            logger.info(f"✅ Browser funcionando - Título: {title}")
            
        except Exception as e:
            logger.warning(f"⚠️ Teste de funcionalidade falhou: {e}")
    
    async def navigate_to_dje(self, url: DJEUrl) -> bool:
        """
        Navega para a página principal do DJE.
        
        MÉTODO MANTIDO: Interface compatível com a versão anterior.
        
        Args:
            url: URL do DJE
            
        Returns:
            bool: True se navegação foi bem-sucedida
            
        Raises:
            BrowserException: Se browser não inicializado
            NavigationException: Se erro na navegação
            TimeoutException: Se timeout
        """
        if not self.page:
            raise BrowserException("navigate", "Browser não inicializado")
        
        main_url = url.get_main_url()
        logger.info(f"🌐 Navegando para DJE: {main_url}")
        
        for attempt in range(self.max_retries):
            try:
                # Navegar para a página principal
                response = await self.page.goto(main_url, wait_until='networkidle')
                
                if not response or response.status >= 400:
                    raise NavigationException(
                        f"Erro HTTP {response.status if response else 'desconhecido'}",
                        main_url
                    )
                
                # Aguardar carregamento da página
                await self.page.wait_for_load_state('domcontentloaded')
                
                # Verificar se chegamos na página correta
                title = await self.page.title()
                if "dje" not in title.lower() and "diário" not in title.lower():
                    logger.warning(f"⚠️ Título da página não esperado: {title}")
                
                logger.info("✅ Navegação para DJE realizada com sucesso")
                return True
                
            except PlaywrightTimeoutError:
                logger.warning(f"⏰ Timeout na tentativa {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise TimeoutException("navigate_to_dje", self.timeout // 1000)
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Erro na navegação (tentativa {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise NavigationException(f"Falha após {self.max_retries} tentativas", main_url)
                await asyncio.sleep(2)
        
        return False
    
    async def navigate_to_caderno(self, criteria: ScrapingCriteria) -> bool:
        """
        MÉTODO ATUALIZADO: Navega para caderno usando pesquisa avançada modular.
        
        Agora delega para o DJENavigationHelper que orquestrea todo o processo
        de pesquisa avançada usando os helpers especializados.
        
        Args:
            criteria: Critérios de scraping
            
        Returns:
            bool: True se navegação/pesquisa foi bem-sucedida
            
        Raises:
            BrowserException: Se helpers não inicializados
            NavigationException: Se erro na pesquisa
        """
        if not self.page:
            raise BrowserException("navigate_caderno", "Browser não inicializado")
        
        if not self.dje_helper:
            raise BrowserException("navigate_caderno", "DJE Helper não inicializado")
        
        logger.info(f"🎯 Executando pesquisa avançada para: {criteria.get_caderno_description()}")
        
        try:
            # Aguardar página carregar completamente
            await self.page.wait_for_load_state('networkidle')
            
            # === VALIDAÇÃO DOS CRITÉRIOS ===
            validation_result = await self.dje_helper.validate_search_criteria(criteria)
            
            if not validation_result['is_valid']:
                logger.error("❌ Critérios de pesquisa inválidos")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")
                raise NavigationException("Critérios de pesquisa inválidos")
            
            if validation_result['warnings']:
                logger.warning("⚠️ Avisos nos critérios de pesquisa:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")
            
            # === EXECUÇÃO DA PESQUISA ===
            # Usar helper principal para orquestrar pesquisa avançada
            success = await self.dje_helper.execute_search_only(criteria)
            
            if success:
                logger.info("✅ Pesquisa avançada executada com sucesso")
                
                # Obter resumo dos resultados
                summary = await self.dje_helper.get_search_results_summary()
                total_results = summary.get('result_metadata', {}).get('total_results', 0)
                logger.info(f"📊 Resultados encontrados: {total_results}")
                
                return True
            else:
                logger.error("❌ Falha na execução da pesquisa avançada")
                return False
                
        except PlaywrightTimeoutError:
            raise TimeoutException("navigate_to_caderno", self.timeout // 1000)
        except Exception as e:
            logger.error(f"❌ Erro ao executar pesquisa avançada: {str(e)}")
            raise NavigationException(f"Erro na pesquisa avançada: {str(e)}")
    
    async def extract_publications(self, 
                                 criteria: ScrapingCriteria, 
                                 max_publications: Optional[int] = None) -> List[Publication]:
        """
        MÉTODO ATUALIZADO: Extrai publicações usando helpers modulares.
        
        Agora utiliza o DJENavigationHelper que orquestrea todo o fluxo:
        1. Navegação entre páginas
        2. Extração usando DJEContentParser
        3. Validação usando critérios de negócio
        
        Args:
            criteria: Critérios de scraping e validação
            max_publications: Limite máximo de publicações
            
        Returns:
            List[Publication]: Publicações extraídas e validadas
            
        Raises:
            BrowserException: Se helpers não inicializados
            ParsingException: Se erro na extração
        """
        if not self.page:
            raise BrowserException("extract_publications", "Browser não inicializado")
        
        if not self.dje_helper:
            raise BrowserException("extract_publications", "DJE Helper não inicializado")
        
        start_time = datetime.now()
        
        logger.info(f"📋 Extraindo publicações com critérios: {criteria}")
        if max_publications:
            logger.info(f"📊 Limite máximo: {max_publications} publicações")
        
        try:
            # === EXECUÇÃO DO FLUXO COMPLETO ===
            # O DJENavigationHelper orquestrea todo o processo:
            # - Navegação entre páginas de resultados
            # - Extração usando DJEContentParser
            # - Validação dos critérios
            # - Paginação automática (se habilitada)
            publications = await self.dje_helper.execute_full_scraping_flow(
                criteria,
                max_publications
            )
            
            # === MÉTRICAS DE PERFORMANCE ===
            extraction_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics['total_scraping_time'] = extraction_time
            
            if publications and extraction_time > 0:
                self.performance_metrics['publications_per_second'] = len(publications) / extraction_time
            
            # === LOG DE RESULTADOS ===
            logger.info(f"🎉 Extração concluída:")
            logger.info(f"  📋 Publicações extraídas: {len(publications)}")
            logger.info(f"  ⏱️ Tempo de extração: {extraction_time:.2f}s")
            logger.info(f"  📈 Taxa: {self.performance_metrics['publications_per_second']:.2f} pub/s")
            
            # === ESTATÍSTICAS DA SESSÃO ===
            session_stats = self.dje_helper.get_session_statistics()
            logger.info(f"📊 Estatísticas da sessão:")
            logger.info(f"  📄 Páginas processadas: {session_stats['pages_processed']}")
            logger.info(f"  ❌ Erros: {session_stats['errors_count']}")
            logger.info(f"  📈 Taxa de sucesso: {session_stats.get('success_rate', 0):.2%}")
            
            return publications
            
        except Exception as e:
            # Calcular taxa de erro
            session_stats = self.dje_helper.get_session_statistics()
            if session_stats['pages_processed'] > 0:
                self.performance_metrics['error_rate'] = session_stats['errors_count'] / session_stats['pages_processed']
            
            logger.error(f"❌ Erro durante extração de publicações: {str(e)}")
            raise ParsingException("extract_publications", "fluxo_completo", str(e))
    
    async def extract_publication_details(self, publication: Publication) -> Publication:
        """
        MÉTODO MANTIDO: Extrai detalhes de publicação específica.
        
        Args:
            publication: Publicação para extrair detalhes
            
        Returns:
            Publication: Publicação com detalhes atualizados
        """
        logger.debug(f"📝 Detalhes da publicação {publication.id} já extraídos pelo fluxo modular")
        
        # Na implementação modular, os detalhes são extraídos automaticamente
        # pelo DJEContentParser durante o fluxo principal
        return publication
    
    async def close(self) -> None:
        """
        MÉTODO ATUALIZADO: Fecha browser e limpa recursos modulares.
        
        Agora inclui limpeza dos helpers modulares e relatório final.
        """
        try:
            logger.info("🔄 Fechando Playwright Scraper...")
            
            # === LIMPEZA DOS HELPERS ===
            if self.dje_helper:
                await self.dje_helper.cleanup_session()
            
            # === RELATÓRIO FINAL DE PERFORMANCE ===
            self._log_final_performance_report()
            
            # === FECHAMENTO DO BROWSER ===
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            # === LIMPEZA DOS HELPERS ===
            self.dje_helper = None
            self.search_handler = None
            self.content_parser = None
            
            logger.info("✅ Playwright Scraper fechado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao fechar Playwright: {str(e)}")
            raise BrowserException("close", str(e))
    
    def _log_final_performance_report(self) -> None:
        """Gera relatório final de performance."""
        if self.adapter_config['enable_performance_metrics']:
            logger.info("📊 Relatório Final de Performance:")
            logger.info(f"  🚀 Tempo de inicialização: {self.performance_metrics['initialization_time']:.2f}s")
            logger.info(f"  ⏱️ Tempo total de scraping: {self.performance_metrics['total_scraping_time']:.2f}s")
            logger.info(f"  📈 Publicações por segundo: {self.performance_metrics['publications_per_second']:.2f}")
            logger.info(f"  ❌ Taxa de erro: {self.performance_metrics['error_rate']:.2%}")
    
    async def _cleanup_on_error(self):
        """Limpa recursos em caso de erro na inicialização."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass  # Ignorar erros durante limpeza
    
    # === MÉTODOS DE CONVENIÊNCIA (NOVOS) ===
    
    async def health_check(self) -> Dict[str, Any]:
        """
        NOVO MÉTODO: Executa verificação de saúde completa.
        
        Returns:
            Dict com status de todos os componentes
        """
        if not self.dje_helper:
            return {'status': 'unhealthy', 'error': 'Helpers não inicializados'}
        
        return await self.dje_helper.execute_health_check()
    
    async def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        NOVO MÉTODO: Retorna estatísticas completas de scraping.
        
        Returns:
            Dict com estatísticas detalhadas
        """
        stats = {
            'adapter_performance': self.performance_metrics.copy(),
            'adapter_config': self.adapter_config.copy()
        }
        
        if self.dje_helper:
            stats['session_statistics'] = self.dje_helper.get_session_statistics()
            stats['configuration_summary'] = self.dje_helper.get_configuration_summary()
        
        return stats
    
    async def validate_criteria_before_scraping(self, criteria: ScrapingCriteria) -> Dict[str, Any]:
        """
        NOVO MÉTODO: Valida critérios antes de iniciar scraping.
        
        Args:
            criteria: Critérios a serem validados
            
        Returns:
            Dict com resultado da validação
        """
        if not self.dje_helper:
            return {'is_valid': False, 'error': 'Helper não inicializado'}
        
        return await self.dje_helper.validate_search_criteria(criteria)