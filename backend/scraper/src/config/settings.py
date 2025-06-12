import os
from typing import List, Optional
from datetime import timedelta
from dataclasses import dataclass
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


@dataclass
class DatabaseSettings:
    """Configurações do banco de dados."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class RedisSettings:
    """Configurações do Redis."""
    url: str
    default_ttl_hours: int = 24
    max_connections: int = 10


@dataclass
class ScrapingSettings:
    """Configurações do scraping."""
    headless: bool = True
    timeout: int = 30000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    max_retries: int = 3
    retry_delay: int = 5
    required_terms: List[str] = None
    
    def __post_init__(self):
        if self.required_terms is None:
            self.required_terms = [
                "Instituto Nacional do Seguro Social",
                "INSS"
            ]


@dataclass
class SchedulerSettings:
    """Configurações do agendador."""
    execution_hour: int = 9
    execution_minute: int = 0
    start_date: str = "2025-03-17"  # Data especificada nos requisitos


@dataclass
class LoggingSettings:
    """Configurações de logging."""
    level: str = "INFO"
    dir: str = "./logs"
    rotation_days: int = 7
    max_size_mb: int = 10
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"


class Settings:
    """
    Classe principal de configurações da aplicação.
    
    Centraliza todas as configurações necessárias para o funcionamento
    do sistema de scraping do DJE.
    """
    
    def __init__(self):
        """Inicializa as configurações a partir das variáveis de ambiente."""
        self.database = DatabaseSettings(
            url=self._get_env("POSTGRES_URL_ASYNC", "postgresql+asyncpg://justcash_user:password@localhost:5432/justcash_db"),
            pool_size=int(self._get_env("DB_POOL_SIZE", "10")),
            max_overflow=int(self._get_env("DB_MAX_OVERFLOW", "20")),
            pool_recycle=int(self._get_env("DB_POOL_RECYCLE", "3600")),
            echo=self._get_env("DB_ECHO", "false").lower() == "true"
        )
        
        self.redis = RedisSettings(
            url=self._get_env("REDIS_URL", "redis://localhost:6379"),
            default_ttl_hours=int(self._get_env("REDIS_TTL_HOURS", "24")),
            max_connections=int(self._get_env("REDIS_MAX_CONNECTIONS", "10"))
        )
        
        self.scraping = ScrapingSettings(
            headless=self._get_env("BROWSER_HEADLESS", "true").lower() == "true",
            timeout=int(self._get_env("BROWSER_TIMEOUT", "30000")),
            user_agent=self._get_env("BROWSER_USER_AGENT", 
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
            max_retries=int(self._get_env("SCRAPER_MAX_RETRIES", "3")),
            retry_delay=int(self._get_env("SCRAPER_RETRY_DELAY", "5"))
        )
        
        self.scheduler = SchedulerSettings(
            execution_hour=int(self._get_env("SCHEDULER_HOUR", "9")),
            execution_minute=int(self._get_env("SCHEDULER_MINUTE", "0")),
            start_date=self._get_env("SCHEDULER_START_DATE", "2025-03-17")
        )
        
        self.logging = LoggingSettings(
            level=self._get_env("LOG_LEVEL", "INFO"),
            dir=self._get_env("LOG_DIR", "./logs"),
            rotation_days=int(self._get_env("LOG_ROTATION_DAYS", "7")),
            max_size_mb=int(self._get_env("LOG_MAX_SIZE_MB", "10"))
        )
        
        # Configurações específicas do DJE
        self.dje_base_url = "https://dje.tjsp.jus.br"
        self.dje_caderno = "3"  # Caderno 3 - Judicial - 1ª Instância
        self.dje_instancia = "1"
        self.dje_local = "Capital"
        self.dje_parte = "1"
        
        # Validar configurações críticas
        self._validate_settings()
    
    def _get_env(self, key: str, default: str = "") -> str:
        """
        Recupera variável de ambiente com valor padrão.
        
        Args:
            key: Nome da variável
            default: Valor padrão se não encontrada
            
        Returns:
            Valor da variável ou padrão
        """
        return os.getenv(key, default)
    
    def _validate_settings(self) -> None:
        """Valida configurações críticas."""
        if not self.database.url:
            raise ValueError("POSTGRES_URL_ASYNC é obrigatória")
        
        if not self.redis.url:
            raise ValueError("REDIS_URL é obrigatória")
        
        if self.scraping.timeout < 5000:
            raise ValueError("Timeout do browser deve ser pelo menos 5 segundos")
        
        if self.scraping.max_retries < 1:
            raise ValueError("Máximo de tentativas deve ser pelo menos 1")
    
    def get_database_url_sync(self) -> str:
        """
        Retorna URL do banco para uso com SQLAlchemy síncrono.
        
        Returns:
            URL modificada para uso síncrono
        """
        return self.database.url.replace("+asyncpg", "")
    
    def get_redis_connection_kwargs(self) -> dict:
        """
        Retorna argumentos para conexão Redis.
        
        Returns:
            Dicionário com argumentos de conexão
        """
        return {
            "url": self.redis.url,
            "max_connections": self.redis.max_connections,
            "socket_keepalive": True,
            "health_check_interval": 30
        }


# Instância global das configurações
settings = Settings()