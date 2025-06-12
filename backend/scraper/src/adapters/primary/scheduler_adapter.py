from typing import Optional, Callable, Any, Dict
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.ports.scheduler_port import SchedulerPort
from src.shared.logger import get_logger

logger = get_logger(__name__)


class APSchedulerAdapter(SchedulerPort):
    """
    Adaptador APScheduler para agendamento de tarefas.
    
    Implementa a interface SchedulerPort usando APScheduler
    para executar tarefas de scraping periodicamente.
    """
    
    def __init__(self):
        """Inicializa o adaptador do agendador."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def initialize(self) -> None:
        """Inicializa o agendador."""
        try:
            logger.info("Inicializando APScheduler")
            self.scheduler.start()
            self.is_running = True
            logger.info("APScheduler inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar APScheduler: {str(e)}")
            raise
    
    async def schedule_daily_task(
        self,
        task_id: str,
        task_func: Callable,
        execution_time: time,
        start_date: Optional[datetime] = None,
        **kwargs
    ) -> str:
        """
        Agenda uma tarefa para execução diária.
        
        Args:
            task_id: Identificador único da tarefa
            task_func: Função a ser executada
            execution_time: Horário de execução (HH:MM)
            start_date: Data de início (opcional)
            **kwargs: Argumentos adicionais para a função
            
        Returns:
            ID do job criado
        """
        try:
            # Criar trigger cron para execução diária
            trigger = CronTrigger(
                hour=execution_time.hour,
                minute=execution_time.minute,
                start_date=start_date
            )
            
            # Adicionar job ao agendador
            job = self.scheduler.add_job(
                task_func,
                trigger=trigger,
                id=task_id,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=3600  # 1 hora de tolerância
            )
            
            logger.info(
                f"Tarefa '{task_id}' agendada para execução diária às "
                f"{execution_time.strftime('%H:%M')}"
            )
            
            if start_date:
                logger.info(f"Início em: {start_date.strftime('%Y-%m-%d')}")
            
            return job.id
            
        except Exception as e:
            logger.error(f"Erro ao agendar tarefa: {str(e)}")
            raise
    
    async def schedule_interval_task(
        self,
        task_id: str,
        task_func: Callable,
        interval_seconds: int,
        **kwargs
    ) -> str:
        """
        Agenda uma tarefa para execução em intervalos.
        
        Args:
            task_id: Identificador único da tarefa
            task_func: Função a ser executada
            interval_seconds: Intervalo entre execuções em segundos
            **kwargs: Argumentos adicionais para a função
            
        Returns:
            ID do job criado
        """
        try:
            job = self.scheduler.add_job(
                task_func,
                'interval',
                seconds=interval_seconds,
                id=task_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            logger.info(
                f"Tarefa '{task_id}' agendada para execução a cada "
                f"{interval_seconds} segundos"
            )
            
            return job.id
            
        except Exception as e:
            logger.error(f"Erro ao agendar tarefa com intervalo: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma tarefa agendada.
        
        Args:
            task_id: ID da tarefa a cancelar
            
        Returns:
            True se cancelada com sucesso
        """
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"Tarefa '{task_id}' cancelada")
            return True
        except Exception as e:
            logger.error(f"Erro ao cancelar tarefa: {str(e)}")
            return False
    
    async def get_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Lista todas as tarefas agendadas.
        
        Returns:
            Dicionário com informações das tarefas
        """
        jobs = self.scheduler.get_jobs()
        
        tasks = {}
        for job in jobs:
            tasks[job.id] = {
                'id': job.id,
                'next_run': job.next_run_time,
                'trigger': str(job.trigger),
                'func': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
            }
        
        return tasks
    
    async def stop(self) -> None:
        """Para o agendador."""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("APScheduler parado") 