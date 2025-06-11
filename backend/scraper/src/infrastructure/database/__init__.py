"""
Módulo de inicialização do banco de dados
Garante que a configuração seja carregada corretamente
"""

import os
from loguru import logger


def initialize_database_config():
    """
    Inicializa a configuração do banco de dados
    Deve ser chamado antes de importar qualquer módulo de banco
    """

    # Verifica se DATABASE_URL está definida
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning(
            "DATABASE_URL não encontrada, tentando construir a partir de variáveis individuais..."
        )

        # Tenta construir a partir de variáveis individuais
        db_host = os.getenv("POSTGRES_CONTAINER_NAME", "postgres")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB")
        db_user = os.getenv("POSTGRES_USER")
        db_password = os.getenv("POSTGRES_PASSWORD")

        if all([db_name, db_user, db_password]):
            database_url = (
                f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            )
            os.environ["DATABASE_URL"] = database_url
            logger.info("DATABASE_URL construída a partir de variáveis individuais")
        else:
            logger.error("Não foi possível construir DATABASE_URL")
            logger.error(
                f"Variáveis disponíveis: HOST={db_host}, PORT={db_port}, DB={db_name}, USER={db_user}, PASS={'***' if db_password else 'None'}"
            )

            # Define valores padrão para desenvolvimento
            default_url = (
                "postgresql://juscash_user:juscash_password@postgres:5432/juscash_dje"
            )
            os.environ["DATABASE_URL"] = default_url
            logger.warning(f"Usando URL padrão para desenvolvimento: {default_url}")


def get_connection_manager():
    """
    Obtém o gerenciador de conexão de forma segura
    """
    try:
        from .connection_manager import connection_manager

        return connection_manager
    except Exception as e:
        logger.error(f"Erro ao importar connection_manager: {e}")
        raise


def get_database_service():
    """
    Obtém o serviço de banco de dados de forma segura
    """
    try:
        from src.application.services.database_service import DatabaseService

        return DatabaseService()
    except Exception as e:
        logger.error(f"Erro ao importar DatabaseService: {e}")
        raise


# Função para verificar se o ambiente está configurado
def check_environment():
    """
    Verifica se o ambiente está configurado corretamente
    """
    required_vars = [
        "DATABASE_URL",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.warning(f"Variáveis de ambiente não configuradas: {missing_vars}")
        return False

    logger.info("Ambiente configurado corretamente")
    return True


# Inicializa automaticamente quando o módulo é importado
initialize_database_config()
