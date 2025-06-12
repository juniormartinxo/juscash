from datetime import datetime, time
from typing import Optional

from src.core.ports.scheduler_port import SchedulerPort
from src.core.usecases.scrape_publications import ScrapePublicationsUseCase
from src.shared.value_objects import ScrapingCriteria
from src.shared.exceptions import SchedulerException, ConfigurationException
from src.shared.logger import get_logger

logger = get_logger(__name__)


class ScheduleScrapingUseCase:
    """
    Caso de uso para agendamento da execução automática do scraping.
    
    Gerencia o agendamento diário do scraping de publicações
    conforme especificado nos requisitos (início em 17/03/2025).
    """
    
    def __init__(self, 
                 scheduler: SchedulerPort,
                 scrape_use_case: ScrapePublicationsUseCase):
        """
        Inicializa o caso de uso.
        
        Args:
            scheduler: Implementação do port de agendamento
            scrape_use_case: Caso de uso de scraping para executar
        """
        self.scheduler = scheduler
        self.scrape_use_case = scrape_use_case
        self._job_id: Optional[str] = None
    
    async def setup_daily_execution(self, 
                                  start_date: Optional[datetime] = None,
                                  execution_time: Optional[time] = None,
                                  criteria: Optional[ScrapingCriteria] = None) -> str:
        """
        Configura execução diária do scraping.
        
        Args:
            start_date: Data de início (padrão: 17/03/2025)
            execution_time: Horário da execução (padrão: 09:00)
            criteria: Critérios de scraping (usa padrão se não informado)
            
        Returns:
            ID do job agendado
            
        Raises:
            SchedulerException: Se houver erro no agendamento
            ConfigurationException: Se configurações estiverem inválidas
        """
        # Valores padrão conforme especificação
        if start_date is None:
            start_date = datetime(2025, 3, 17)  # 17/03/2025 conforme requisito
        
        if execution_time is None:
            execution_time = time(9, 0)  # 09:00 padrão
        
        if start_date < datetime.now():
            logger.warning(f"Data de início ({start_date}) é anterior à data atual")
        
        logger.info(f"Configurando execução diária a partir de {start_date.date()} às {execution_time}")
        
        try:
            # Inicializar scheduler
            await self.scheduler.initialize()
            
            # Criar função wrapper para execução do scraping
            async def scheduled_scraping_job():
                """Função que será executada pelo agendador."""
                try:
                    logger.info("Iniciando execução agendada do scraping")
                    stats = await self.scrape_use_case.execute(
                        criteria=criteria,
                        skip_duplicates=True
                    )
                    logger.info(f"Execução agendada concluída: {stats}")
                except Exception as e:
                    logger.error(f"Erro na execução agendada: {str(e)}")
                    # Aqui poderia enviar notificação de erro
                    raise
            
            # Agendar execução diária
            self._job_id = await self.scheduler.schedule_daily_scraping(
                job_function=scheduled_scraping_job,
                start_date=start_date,
                hour=execution_time.hour,
                minute=execution_time.minute
            )
            
            logger.info(f"Scraping agendado com sucesso. Job ID: {self._job_id}")
            return self._job_id
            
        except Exception as e:
            logger.error(f"Erro ao configurar agendamento: {str(e)}")
            raise SchedulerException(
                job_id="setup",
                error_details=str(e)
            )
    
    async def schedule_immediate_execution(self, 
                                         criteria: Optional[ScrapingCriteria] = None) -> str:
        """
        Agenda uma execução imediata (única) do scraping.
        
        Args:
            criteria: Critérios de scraping (usa padrão se não informado)
            
        Returns:
            ID do job agendado
            
        Raises:
            SchedulerException: Se houver erro no agendamento
        """
        logger.info("Agendando execução imediata do scraping")
        
        try:
            # Executar em 1 minuto a partir de agora
            execution_time = datetime.now().replace(second=0, microsecond=0)
            execution_time = execution_time.replace(minute=execution_time.minute + 1)
            
            async def immediate_scraping_job():
                """Função para execução imediata."""
                try:
                    logger.info("Iniciando execução imediata do scraping")
                    stats = await self.scrape_use_case.execute(
                        criteria=criteria,
                        skip_duplicates=True
                    )
                    logger.info(f"Execução imediata concluída: {stats}")
                except Exception as e:
                    logger.error(f"Erro na execução imediata: {str(e)}")
                    raise
            
            job_id = await self.scheduler.schedule_one_time_execution(
                job_function=immediate_scraping_job,
                execution_time=execution_time
            )
            
            logger.info(f"Execução imediata agendada para {execution_time}. Job ID: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Erro ao agendar execução imediata: {str(e)}")
            raise SchedulerException(
                job_id="immediate",
                error_details=str(e)
            )
    
    async def cancel_scheduled_execution(self) -> bool:
        """
        Cancela a execução agendada atual.
        
        Returns:
            True se cancelamento foi bem-sucedido
            
        Raises:
            SchedulerException: Se houver erro no cancelamento
        """
        if not self._job_id:
            logger.warning("Nenhuma execução agendada para cancelar")
            return False
        
        try:
            success = await self.scheduler.cancel_job(self._job_id)
            if success:
                logger.info(f"Execução agendada cancelada: {self._job_id}")
                self._job_id = None
            else:
                logger.warning(f"Não foi possível cancelar job: {self._job_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao cancelar execução agendada: {str(e)}")
            raise SchedulerException(
                job_id=self._job_id,
                error_details=str(e)
            )
    
    async def start_scheduler(self) -> None:
        """
        Inicia o agendador.
        
        Raises:
            SchedulerException: Se houver erro ao iniciar
        """
        try:
            await self.scheduler.start()
            logger.info("Agendador iniciado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao iniciar agendador: {str(e)}")
            raise SchedulerException(
                job_id="start",
                error_details=str(e)
            )
    
    async def stop_scheduler(self) -> None:
        """
        Para o agendador.
        
        Raises:
            SchedulerException: Se houver erro ao parar
        """
        try:
            await self.scheduler.stop()
            logger.info("Agendador parado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao parar agendador: {str(e)}")
            raise SchedulerException(
                job_id="stop",
                error_details=str(e)
            )
    
    async def get_scheduler_status(self) -> dict:
        """
        Retorna status atual do agendador.
        
        Returns:
            Dicionário com informações de status
        """
        try:
            is_running = await self.scheduler.is_running()
            return {
                'is_running': is_running,
                'job_id': self._job_id,
                'has_scheduled_job': self._job_id is not None
            }
        except Exception as e:
            logger.error(f"Erro ao obter status do agendador: {str(e)}")
            return {
                'is_running': False,
                'job_id': None,
                'has_scheduled_job': False,
                'error': str(e)
            }