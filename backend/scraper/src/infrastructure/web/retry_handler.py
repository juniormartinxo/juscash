"""
Sistema avançado de retry com backoff exponencial
"""

import asyncio
import random
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


class RetryHandler:
    """
    Handler avançado para retry de operações com diferentes estratégias
    """

    @staticmethod
    def with_exponential_backoff(
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """
        Decorator para retry com backoff exponencial

        Args:
            max_attempts: Número máximo de tentativas
            min_wait: Tempo mínimo de espera (segundos)
            max_wait: Tempo máximo de espera (segundos)
            multiplier: Multiplicador do backoff
            jitter: Adicionar jitter para evitar thundering herd
        """

        def decorator(func):
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=multiplier, min=min_wait, max=max_wait, jitter=jitter
                ),
                retry=retry_if_exception_type(
                    (
                        ConnectionError,
                        TimeoutError,
                        OSError,
                        Exception,  # Pode ser refinado para tipos específicos
                    )
                ),
                before_sleep=before_sleep_log(logger, logger.level),
                after=after_log(logger, logger.level),
            )
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def with_custom_strategy(
        should_retry: Callable[[Exception], bool],
        max_attempts: int = 3,
        wait_strategy: Callable[[int], float] = None,
    ):
        """
        Retry com estratégia customizada

        Args:
            should_retry: Função que determina se deve tentar novamente
            max_attempts: Número máximo de tentativas
            wait_strategy: Função que calcula tempo de espera
        """

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        if attempt == max_attempts - 1:
                            # Última tentativa, re-raise
                            raise

                        if not should_retry(e):
                            # Não deve tentar novamente
                            raise

                        # Calcular tempo de espera
                        if wait_strategy:
                            wait_time = wait_strategy(attempt + 1)
                        else:
                            wait_time = 2**attempt + random.uniform(0, 1)

                        logger.warning(
                            f"⚠️  Tentativa {attempt + 1}/{max_attempts} falhou: {e}"
                        )
                        logger.info(
                            f"⏳ Aguardando {wait_time:.2f}s antes da próxima tentativa"
                        )

                        await asyncio.sleep(wait_time)

                # Nunca deveria chegar aqui, mas por segurança
                raise last_exception

            return wrapper

        return decorator


class NetworkRetryHandler(RetryHandler):
    """
    Handler especializado para operações de rede
    """

    @staticmethod
    def for_http_requests(max_attempts: int = 5):
        """Retry específico para requisições HTTP"""

        def should_retry_http(exception: Exception) -> bool:
            # Retry para erros de rede e timeouts
            if isinstance(exception, (ConnectionError, TimeoutError)):
                return True

            # Retry para códigos HTTP específicos (se disponível)
            if hasattr(exception, "response") and exception.response:
                status_code = exception.response.status_code
                # Retry para 5xx e alguns 4xx
                return status_code >= 500 or status_code in [408, 429]

            return False

        def wait_strategy(attempt: int) -> float:
            # Backoff exponencial com jitter e limite
            base_wait = min(2**attempt, 30)  # Máximo 30 segundos
            jitter = random.uniform(0, base_wait * 0.1)  # 10% de jitter
            return base_wait + jitter

        return RetryHandler.with_custom_strategy(
            should_retry=should_retry_http,
            max_attempts=max_attempts,
            wait_strategy=wait_strategy,
        )

    @staticmethod
    def for_web_scraping(max_attempts: int = 3):
        """Retry específico para web scraping"""

        def should_retry_scraping(exception: Exception) -> bool:
            # Retry para erros comuns de scraping
            error_message = str(exception).lower()

            retry_conditions = [
                "timeout" in error_message,
                "connection" in error_message,
                "network" in error_message,
                "element not found" in error_message,
                "page not loaded" in error_message,
            ]

            return any(retry_conditions)

        return RetryHandler.with_custom_strategy(
            should_retry=should_retry_scraping,
            max_attempts=max_attempts,
            wait_strategy=lambda attempt: 5 + (attempt * 2),  # 5, 7, 9 segundos
        )
