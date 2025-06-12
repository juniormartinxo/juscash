import asyncio
import sys
import signal
from datetime import datetime, time
from typing import Optional

from src.config.settings import settings
from src.config.database import create_tables, close_db_connections
from src.shared.logger import get_logger, setup_logging
from src.shared.value_objects import ScrapingCriteria

# Imports dos adaptadores
from src.adapters.secondary.playwright_scraper import PlaywrightScraperAdapter
from src.adapters.secondary.sqlalchemy_repository import EnhancedSQLAlchemyRepository as SQLAlchemyRepository
from src.adapters.secondary.redis_cache import RedisCacheAdapter
from src.adapters.primary.scheduler_adapter import APSchedulerAdapter

# Imports dos casos de uso
from src.core.usecases.scrape_publications import ScrapePublicationsUseCase
from src.core.usecases.schedule_scraping import ScheduleScrapingUseCase

# Setup inicial do logging
setup_logging()
logger = get_logger(__name__)


class DJEScrapingApplication:
    """
    Aplicação principal do sistema de scraping do DJE.
    
    Coordena a inicialização de todos os componentes e gerencia
    o ciclo de vida da aplicação seguindo a arquitetura hexagonal.
    """
    
    def __init__(self):
        """Inicializa a aplicação com configurações padrão."""
        self.settings = settings
        
        # Adaptadores (infraestrutura)
        self.scraper_adapter: Optional[PlaywrightScraperAdapter] = None
        self.database_adapter: Optional[SQLAlchemyRepository] = None
        self.cache_adapter: Optional[RedisCacheAdapter] = None
        self.scheduler_adapter: Optional[APSchedulerAdapter] = None
        
        # Casos de uso (aplicação)
        self.scrape_use_case: Optional[ScrapePublicationsUseCase] = None
        self.schedule_use_case: Optional[ScheduleScrapingUseCase] = None
        
        # Estado da aplicação
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Configurar handlers para sinais do sistema
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema (SIGINT, SIGTERM)."""
        if sys.platform != "win32":
            # Unix/Linux
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
        else:
            # Windows
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de shutdown."""
        logger.info(f"Sinal recebido: {signum}. Iniciando shutdown graceful...")
        self.shutdown_event.set()
    
    async def initialize(self) -> None:
        """
        Inicializa todos os componentes da aplicação.
        
        Raises:
            Exception: Se houver erro na inicialização de qualquer componente
        """
        logger.info("🚀 Iniciando aplicação DJE Scraping...")
        
        try:
            # 1. Inicializar banco de dados
            logger.info("📊 Inicializando banco de dados...")
            #await create_tables()
            
            self.database_adapter = SQLAlchemyRepository(
                database_url=self.settings.database.url
            )
            logger.info("✅ Banco de dados inicializado")
            
            # 2. Inicializar cache Redis (opcional)
            try:
                logger.info("🔄 Inicializando cache Redis...")
                self.cache_adapter = RedisCacheAdapter(
                    redis_url=self.settings.redis.url
                )
                await self.cache_adapter.initialize()
                logger.info("✅ Cache Redis inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Cache Redis não disponível: {str(e)}")
                self.cache_adapter = None
            
            # 3. Inicializar scraper Playwright
            logger.info("🌐 Inicializando scraper Playwright...")
            self.scraper_adapter = PlaywrightScraperAdapter(
                headless=self.settings.scraping.headless,
                timeout=self.settings.scraping.timeout,
                user_agent=self.settings.scraping.user_agent,
                max_retries=self.settings.scraping.max_retries
            )
            await self.scraper_adapter.initialize()
            logger.info("✅ Scraper Playwright inicializado")
            
            # 4. Inicializar agendador
            logger.info("⏰ Inicializando agendador...")
            self.scheduler_adapter = APSchedulerAdapter()
            await self.scheduler_adapter.initialize()
            logger.info("✅ Agendador inicializado")
            
            # 5. Inicializar casos de uso
            logger.info("🎯 Inicializando casos de uso...")
            self.scrape_use_case = ScrapePublicationsUseCase(
                scraper=self.scraper_adapter,
                database=self.database_adapter,
                cache=self.cache_adapter
            )
            
            self.schedule_use_case = ScheduleScrapingUseCase(
                scheduler=self.scheduler_adapter,
                scrape_use_case=self.scrape_use_case
            )
            logger.info("✅ Casos de uso inicializados")
            
            self.is_running = True
            logger.info("🎉 Aplicação inicializada com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização da aplicação: {str(e)}")
            await self.cleanup()
            raise
    
    async def run_immediate_scraping(self) -> dict:
        """
        Executa scraping imediato (uma vez).
        
        Returns:
            Dicionário com estatísticas da execução
            
        Raises:
            Exception: Se aplicação não estiver inicializada ou houver erro
        """
        if not self.is_running or not self.scrape_use_case:
            raise RuntimeError("Aplicação não foi inicializada")
        
        logger.info("🔄 Executando scraping imediato...")
        
        # Criar critérios padrão
        criteria = ScrapingCriteria(
            required_terms=tuple(self.settings.scraping.required_terms),
            caderno=self.settings.dje_caderno,
            instancia=self.settings.dje_instancia,
            local=self.settings.dje_local,
            parte=self.settings.dje_parte
        )
        
        # Executar scraping
        stats = await self.scrape_use_case.execute(
            criteria=criteria,
            skip_duplicates=True
        )
        
        logger.info(f"✅ Scraping imediato concluído: {stats}")
        return stats
    
    async def setup_scheduled_scraping(self) -> str:
        """
        Configura execução automática diária do scraping.
        
        Returns:
            ID do job agendado
            
        Raises:
            Exception: Se aplicação não estiver inicializada ou houver erro
        """
        if not self.is_running or not self.schedule_use_case:
            raise RuntimeError("Aplicação não foi inicializada")
        
        logger.info("📅 Configurando scraping automático...")
        
        # Parsear data de início
        start_date = datetime.strptime(
            self.settings.scheduler.start_date, 
            "%Y-%m-%d"
        )
        
        # Configurar horário de execução
        execution_time = time(
            hour=self.settings.scheduler.execution_hour,
            minute=self.settings.scheduler.execution_minute
        )
        
        # Criar critérios padrão
        criteria = ScrapingCriteria(
            required_terms=tuple(self.settings.scraping.required_terms),
            caderno=self.settings.dje_caderno,
            instancia=self.settings.dje_instancia,
            local=self.settings.dje_local,
            parte=self.settings.dje_parte
        )
        
        # Configurar agendamento
        job_id = await self.schedule_use_case.setup_daily_execution(
            start_date=start_date,
            execution_time=execution_time,
            criteria=criteria
        )
        
        # Iniciar agendador
        await self.schedule_use_case.start_scheduler()
        
        logger.info(f"✅ Scraping automático configurado. Job ID: {job_id}")
        logger.info(f"📅 Execuções diárias a partir de {start_date.date()} às {execution_time}")
        
        return job_id
    
    async def run_with_scheduler(self) -> None:
        """
        Executa a aplicação com agendamento automático.
        
        Mantém a aplicação rodando e aguarda sinal de shutdown.
        """
        if not self.is_running:
            raise RuntimeError("Aplicação não foi inicializada")
        
        logger.info("🔄 Iniciando modo agendado...")
        
        try:
            # Configurar scraping automático
            job_id = await self.setup_scheduled_scraping()
            
            logger.info("⏰ Aplicação rodando em modo agendado. Pressione Ctrl+C para parar.")
            
            # Aguardar sinal de shutdown
            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)
            
            logger.info("🛑 Sinal de shutdown recebido")
            
        except KeyboardInterrupt:
            logger.info("🛑 Interrupção via teclado recebida")
        except Exception as e:
            logger.error(f"❌ Erro durante execução agendada: {str(e)}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """
        Limpa recursos e fecha conexões.
        """
        logger.info("🧹 Iniciando limpeza de recursos...")
        
        self.is_running = False
        
        # Parar agendador
        if self.scheduler_adapter:
            try:
                await self.scheduler_adapter.stop()
                logger.info("✅ Agendador parado")
            except Exception as e:
                logger.error(f"❌ Erro ao parar agendador: {str(e)}")
        
        # Fechar scraper
        if self.scraper_adapter:
            try:
                await self.scraper_adapter.close()
                logger.info("✅ Scraper fechado")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar scraper: {str(e)}")
        
        # Fechar cache
        if self.cache_adapter:
            try:
                await self.cache_adapter.close()
                logger.info("✅ Cache fechado")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar cache: {str(e)}")
        
        # Fechar conexões de banco
        try:
            await close_db_connections()
            logger.info("✅ Conexões de banco fechadas")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar banco: {str(e)}")
        
        logger.info("🏁 Limpeza concluída")


async def main():
    """
    Função principal da aplicação.
    
    Ponto de entrada que pode ser usado de diferentes formas:
    - Execução imediata: python -m src.main
    - Execução agendada: python -m src.main --schedule
    """
    app = DJEScrapingApplication()
    
    try:
        # Inicializar aplicação
        await app.initialize()
        
        # Verificar argumentos da linha de comando
        if len(sys.argv) > 1 and "--schedule" in sys.argv:
            # Modo agendado
            await app.run_with_scheduler()
        else:
            # Modo imediato (execução única)
            logger.info("🔄 Modo execução imediata")
            stats = await app.run_immediate_scraping()
            
            # Exibir resumo
            logger.info("📊 RESUMO DA EXECUÇÃO:")
            logger.info(f"   📋 Publicações encontradas: {stats.get('publications_found', 0)}")
            logger.info(f"   ✅ Publicações novas: {stats.get('publications_new', 0)}")
            logger.info(f"   🔄 Publicações duplicadas: {stats.get('publications_duplicated', 0)}")
            logger.info(f"   ❌ Publicações com erro: {stats.get('publications_failed', 0)}")
            logger.info(f"   ⏱️ Tempo de execução: {stats.get('execution_time_seconds', 0):.2f}s")
    
    except KeyboardInterrupt:
        logger.info("🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal na aplicação: {str(e)}")
        sys.exit(1)
    finally:
        await app.cleanup()


async def test_scraper():
    scraper = PlaywrightScraperAdapter(headless=False)
    
    try:
        print("🚀 Inicializando scraper...")
        await scraper.initialize()
        print("✅ Scraper inicializado!")
        
        print("🌐 Navegando para teste...")
        await scraper.page.goto('https://example.com')
        print("✅ Navegação concluída!")
        
        print("⏳ Aguardando 5 segundos...")
        await scraper.page.wait_for_timeout(5000)
        
        print("📸 Tirando screenshot...")
        await scraper.page.screenshot(path='test_scraper.png')
        print("✅ Screenshot salvo!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        print("🔒 Fechando scraper...")
        await scraper.close()
        print("✅ Teste concluído!")

# CLI adicional para operações específicas
async def test_scraping():
    """Função para testar o scraping sem agendamento."""
    logger.info("🧪 Modo teste de scraping")
    app = DJEScrapingApplication()
    
    try:
        await app.initialize()
        stats = await app.run_immediate_scraping()
        logger.info(f"🧪 Teste concluído: {stats}")
        return stats
    finally:
        await app.cleanup()


async def test_database():
    """Função para testar conexão com banco de dados."""
    logger.info("🧪 Testando conexão com banco de dados")
    
    try:
        from src.config.database import get_db_session
        
        async with await get_db_session() as session:
            logger.info("✅ Conexão com banco de dados OK")
            return True
    except Exception as e:
        logger.error(f"❌ Erro na conexão: {str(e)}")
        return False


if __name__ == "__main__":
    # Verificar argumentos especiais
    if len(sys.argv) > 1:
        if "--test-scraping" in sys.argv:
            asyncio.run(test_scraper())
        elif "--test-db" in sys.argv:
            asyncio.run(test_database())
        else:
            asyncio.run(main())
    else:
        asyncio.run(main())