import time
from typing import Optional
from sqlalchemy import text
from loguru import logger

from .config import get_db_config, DatabaseConfig
from .models import Base


class DatabaseConnectionManager:
    """Gerenciador de conexão com o banco de dados"""

    def __init__(self):
        self.max_retries = 5
        self.retry_delay = 2  # segundos
        self._db_config: Optional[DatabaseConfig] = None

    @property
    def db_config(self) -> DatabaseConfig:
        """Lazy loading da configuração do banco"""
        if self._db_config is None:
            self._db_config = get_db_config()
        return self._db_config

    def wait_for_database(self) -> bool:
        """
        Aguarda o banco de dados estar disponível com retry automático

        Returns:
            True se conectou com sucesso, False caso contrário
        """
        logger.info("Aguardando conexão com o banco de dados...")

        for attempt in range(1, self.max_retries + 1):
            try:
                if self.db_config.test_connection():
                    logger.info(f"Conectado ao banco de dados na tentativa {attempt}")
                    return True
            except Exception as e:
                logger.warning(f"Tentativa {attempt}/{self.max_retries} falhou: {e}")

                if attempt < self.max_retries:
                    logger.info(
                        f"Aguardando {self.retry_delay} segundos antes da próxima tentativa..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Todas as tentativas de conexão falharam")
                    return False

        return False

    def create_tables(self) -> bool:
        """
        Cria as tabelas no banco de dados se não existirem

        Returns:
            True se as tabelas foram criadas/já existem, False caso contrário
        """
        try:
            logger.info("Criando tabelas no banco de dados...")
            Base.metadata.create_all(bind=self.db_config.engine)
            logger.info("Tabelas criadas/verificadas com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            return False

    def verify_database_schema(self) -> bool:
        """
        Verifica se o schema do banco está correto

        Returns:
            True se o schema está correto, False caso contrário
        """
        try:
            with self.db_config.get_session() as session:
                # Verifica se a tabela publications existe
                result = session.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'publications'
                    );
                """)
                )

                table_exists = result.scalar()

                if not table_exists:
                    logger.error("Tabela 'publications' não encontrada")
                    return False

                # Verifica colunas essenciais
                essential_columns = [
                    "id",
                    "process_number",
                    "availability_date",
                    "authors",
                    "content",
                    "status",
                    "created_at",
                ]

                for column in essential_columns:
                    result = session.execute(
                        text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'publications' 
                            AND column_name = '{column}'
                        );
                    """)
                    )

                    if not result.scalar():
                        logger.error(
                            f"Coluna '{column}' não encontrada na tabela 'publications'"
                        )
                        return False

                logger.info("Schema do banco de dados verificado com sucesso")
                return True

        except Exception as e:
            logger.error(f"Erro ao verificar schema do banco: {e}")
            return False

    def get_database_info(self) -> Optional[dict]:
        """
        Obtém informações sobre o banco de dados

        Returns:
            Dicionário com informações do banco ou None em caso de erro
        """
        try:
            with self.db_config.get_session() as session:
                # Versão do PostgreSQL
                version_result = session.execute(text("SELECT version();"))
                version = version_result.scalar()

                # Número de publicações
                count_result = session.execute(
                    text("SELECT COUNT(*) FROM publications;")
                )
                publication_count = count_result.scalar()

                # Tamanho do banco
                size_result = session.execute(
                    text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()));
                """)
                )
                database_size = size_result.scalar()

                return {
                    "version": version,
                    "publication_count": publication_count,
                    "database_size": database_size,
                    "connection_url": self._get_safe_connection_url(),
                }

        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {e}")
            return None

    def _get_safe_connection_url(self) -> str:
        """
        Retorna a URL de conexão sem a senha para logs

        Returns:
            URL de conexão mascarada
        """
        url = self.db_config.database_url
        if "@" in url:
            # Mascara a senha na URL
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split(":")
                if len(user_pass) >= 3:  # postgres://user:pass
                    masked_url = f"{user_pass[0]}:{user_pass[1]}:***@{parts[1]}"
                    return masked_url
        return "URL não configurada"

    def initialize_database(self) -> bool:
        """
        Inicializa completamente o banco de dados

        Returns:
            True se inicializado com sucesso, False caso contrário
        """
        logger.info("Inicializando banco de dados...")

        try:
            # 1. Aguarda conexão
            if not self.wait_for_database():
                return False

            # 2. Cria tabelas
            if not self.create_tables():
                return False

            # 3. Verifica schema
            if not self.verify_database_schema():
                return False

            # 4. Exibe informações
            db_info = self.get_database_info()
            if db_info:
                logger.info(
                    f"Banco inicializado - Publicações: {db_info['publication_count']}, "
                    f"Tamanho: {db_info['database_size']}"
                )

            logger.info("Banco de dados inicializado com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Erro na inicialização do banco de dados: {e}")
            return False


# Instância global do gerenciador
connection_manager = DatabaseConnectionManager()
