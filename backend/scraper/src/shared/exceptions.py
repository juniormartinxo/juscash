from typing import Optional, Any


class DJEScrapingException(Exception):
    """Exceção base para erros de scraping do DJE."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details or {}


class NavigationException(DJEScrapingException):
    """Exceção para erros de navegação no site do DJE."""
    
    def __init__(self, message: str, url: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, details)
        self.url = url


class ElementNotFoundException(DJEScrapingException):
    """Exceção para quando elementos não são encontrados na página."""
    
    def __init__(self, element_selector: str, page_url: Optional[str] = None, details: Optional[dict] = None):
        message = f"Elemento não encontrado: {element_selector}"
        if page_url:
            message += f" na página {page_url}"
        super().__init__(message, details)
        self.element_selector = element_selector
        self.page_url = page_url


class TimeoutException(DJEScrapingException):
    """Exceção para timeouts durante operações de scraping."""
    
    def __init__(self, operation: str, timeout_seconds: int, details: Optional[dict] = None):
        message = f"Timeout na operação '{operation}' após {timeout_seconds} segundos"
        super().__init__(message, details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class ParsingException(DJEScrapingException):
    """Exceção para erros durante parsing de dados extraídos."""
    
    def __init__(self, field: str, value: Any, reason: str, details: Optional[dict] = None):
        message = f"Erro ao processar campo '{field}' com valor '{value}': {reason}"
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.reason = reason


class DatabaseException(DJEScrapingException):
    """Exceção para erros relacionados ao banco de dados."""
    
    def __init__(self, operation: str, error_details: str, details: Optional[dict] = None):
        message = f"Erro na operação de banco '{operation}': {error_details}"
        super().__init__(message, details)
        self.operation = operation
        self.error_details = error_details


class ValidationException(DJEScrapingException):
    """Exceção para erros de validação de dados."""
    
    def __init__(self, field: str, value: Any, validation_rule: str, details: Optional[dict] = None):
        message = f"Validação falhou para campo '{field}' com valor '{value}': {validation_rule}"
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.validation_rule = validation_rule


class ConfigurationException(DJEScrapingException):
    """Exceção para erros de configuração da aplicação."""
    
    def __init__(self, config_key: str, reason: str, details: Optional[dict] = None):
        message = f"Erro de configuração para '{config_key}': {reason}"
        super().__init__(message, details)
        self.config_key = config_key
        self.reason = reason


class ScrapingLimitException(DJEScrapingException):
    """Exceção para quando limites de scraping são atingidos."""
    
    def __init__(self, limit_type: str, current_value: int, max_value: int, details: Optional[dict] = None):
        message = f"Limite de {limit_type} atingido: {current_value}/{max_value}"
        super().__init__(message, details)
        self.limit_type = limit_type
        self.current_value = current_value
        self.max_value = max_value


class RetryExhaustedException(DJEScrapingException):
    """Exceção para quando todas as tentativas de retry foram esgotadas."""
    
    def __init__(self, operation: str, max_retries: int, last_error: str, details: Optional[dict] = None):
        message = f"Todas as {max_retries} tentativas falharam para '{operation}'. Último erro: {last_error}"
        super().__init__(message, details)
        self.operation = operation
        self.max_retries = max_retries
        self.last_error = last_error


class BrowserException(DJEScrapingException):
    """Exceção para erros relacionados ao browser/Playwright."""
    
    def __init__(self, operation: str, browser_error: str, details: Optional[dict] = None):
        message = f"Erro no browser durante '{operation}': {browser_error}"
        super().__init__(message, details)
        self.operation = operation
        self.browser_error = browser_error


class CacheException(DJEScrapingException):
    """Exceção para erros relacionados ao cache Redis."""
    
    def __init__(self, operation: str, cache_key: str, error_details: str, details: Optional[dict] = None):
        message = f"Erro no cache durante '{operation}' para chave '{cache_key}': {error_details}"
        super().__init__(message, details)
        self.operation = operation
        self.cache_key = cache_key
        self.error_details = error_details


class SchedulerException(DJEScrapingException):
    """Exceção para erros relacionados ao agendador."""
    
    def __init__(self, job_id: str, error_details: str, details: Optional[dict] = None):
        message = f"Erro no agendador para job '{job_id}': {error_details}"
        super().__init__(message, details)
        self.job_id = job_id
        self.error_details = error_details


def handle_exception(exc: Exception, context: str) -> DJEScrapingException:
    """
    Converte exceções genéricas em exceções específicas do domínio.
    
    Args:
        exc: Exceção original
        context: Contexto onde a exceção ocorreu
        
    Returns:
        Exceção específica do domínio
    """
    if isinstance(exc, DJEScrapingException):
        return exc
    
    # Mapear exceções comuns para exceções do domínio
    error_mappings = {
        'TimeoutError': lambda: TimeoutException(context, 30, {'original_error': str(exc)}),
        'ConnectionError': lambda: NavigationException(f"Erro de conexão em {context}", details={'original_error': str(exc)}),
        'ValueError': lambda: ValidationException('unknown', str(exc), context),
        'KeyError': lambda: ElementNotFoundException(str(exc), details={'context': context}),
    }
    
    exception_name = type(exc).__name__
    if exception_name in error_mappings:
        return error_mappings[exception_name]()
    
    # Fallback para exceção genérica
    return DJEScrapingException(
        f"Erro não tratado em {context}: {str(exc)}",
        details={'original_exception': exception_name, 'original_message': str(exc)}
    )