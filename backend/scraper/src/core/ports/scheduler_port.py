from abc import ABC, abstractmethod
from typing import Callable, Optional
from datetime import datetime


class SchedulerPort(ABC):
    """
    Interface para implementações de agendamento de tarefas.
    
    Define o contrato que deve ser implementado por qualquer
    adaptador que realize agendamento de execuções do scraper.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Inicializa o agendador.
        
        Raises:
            SchedulerException: Se houver erro na inicialização
        """
        pass
    
    @abstractmethod
    async def schedule_daily_scraping(self, 
                                    job_function: Callable,
                                    start_date: datetime,
                                    hour: int = 9,
                                    minute: int = 0) -> str:
        """
        Agenda execução diária do scraping.
        
        Args:
            job_function: Função a ser executada
            start_date: Data de início das execuções
            hour: Hora da execução (padrão: 9h)
            minute: Minuto da execução (padrão: 0)
            
        Returns:
            ID do job agendado
            
        Raises:
            SchedulerException: Se houver erro no agendamento
        """
        pass
    
    @abstractmethod
    async def schedule_one_time_execution(self,
                                        job_function: Callable,
                                        execution_time: datetime) -> str:
        """
        Agenda uma execução única.
        
        Args:
            job_function: Função a ser executada
            execution_time: Momento da execução
            
        Returns:
            ID do job agendado
            
        Raises:
            SchedulerException: Se houver erro no agendamento
        """
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancela um job agendado.
        
        Args:
            job_id: ID do job a cancelar
            
        Returns:
            True se cancelamento foi bem-sucedido
            
        Raises:
            SchedulerException: Se houver erro no cancelamento
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """
        Inicia o agendador.
        
        Raises:
            SchedulerException: Se houver erro ao iniciar
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Para o agendador.
        
        Raises:
            SchedulerException: Se houver erro ao parar
        """
        pass
    
    @abstractmethod
    async def is_running(self) -> bool:
        """
        Verifica se o agendador está rodando.
        
        Returns:
            True se está rodando
        """
        pass