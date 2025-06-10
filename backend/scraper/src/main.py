# src/main.py
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Carrega variáveis de ambiente
load_dotenv()

from src.infrastructure.database.connection_manager import connection_manager
from src.application.services.database_service import DatabaseService


def setup_logging():
    """Configura o sistema de logs"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = Path(os.getenv("LOG_DIR", "./logs"))
    
    # Cria diretório de logs se não existir
    log_dir.mkdir(exist_ok=True)
    
    # Remove configuração padrão do loguru
    logger.remove()
    
    # Configuração para console
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Configuração para arquivo
    logger.add(
        log_dir / "scraper_{time:YYYY-MM-DD}.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention=f"{os.getenv('LOG_ROTATION_DAYS', '7')} days",
        compression="zip"
    )
    
    # Configuração para erros
    logger.add(
        log_dir / "scraper_errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )


def validate_environment():
    """Valida se todas as variáveis de ambiente necessárias estão configuradas"""
    required_vars = [
        "DATABASE_URL",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variáveis de ambiente obrigatórias não configuradas: {missing_vars}")
        logger.error("Por favor, configure o arquivo .env baseado no .env.example")
        return False
    
    return True


def test_database_service():
    """Testa o serviço de banco de dados com dados de exemplo"""
    try:
        db_service = DatabaseService()
        
        # Dados de teste
        test_publication = {
            "process_number": "1234567-89.2025.8.26.0001",
            "availability_date": "2025-03-17",
            "authors": ["João da Silva", "Maria Santos"],
            "content": "Teste de publicação para verificar a conexão com o banco de dados.",
            "defendant": "Instituto Nacional do Seguro Social - INSS",
            "lawyers": [
                {"name": "Dr. Pedro Advogado", "oab": "SP123456"},
                {"name": "Dra. Ana Advocacia", "oab": "SP654321"}
            ],
            "gross_value": 5000.50,
            "net_value": 4500.30,
            "interest_value": 300.20,
            "attorney_fees": 200.00
        }
        
        # Tenta salvar a publicação de teste
        logger.info("Testando salvamento de publicação...")
        saved_publication = db_service.save_publication(test_publication)
        logger.success(f"Publicação de teste salva com sucesso: {saved_publication.id}")
        
        # Testa busca
        logger.info("Testando busca de publicação...")
        found_publication = db_service.get_publication_by_process_number(test_publication["process_number"])
        
        if found_publication:
            logger.success(f"Publicação encontrada: {found_publication.process_number}")
        else:
            logger.error("Publicação não encontrada após salvamento")
            return False
        
        # Testa contagem
        logger.info("Testando contagem de publicações...")
        count = db_service.count_publications()
        logger.info(f"Total de publicações no banco: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no teste do serviço de banco de dados: {e}")
        return False


def main():
    """Função principal do scraper"""
    logger.info("=== INICIANDO SCRAPER DJE ===")
    
    # 1. Configurar logs
    setup_logging()
    
    # 2. Validar ambiente
    if not validate_environment():
        sys.exit(1)
    
    # 3. Inicializar banco de dados
    logger.info("Inicializando conexão com o banco de dados...")
    if not connection_manager.initialize_database():
        logger.error("Falha ao inicializar banco de dados")
        sys.exit(1)
    
    # 4. Testar serviço de banco de dados
    logger.info("Testando serviços de banco de dados...")
    if not test_database_service():
        logger.error("Falha nos testes do serviço de banco de dados")
        sys.exit(1)
    
    # 5. Exibir informações do sistema
    db_info = connection_manager.get_database_info()
    if db_info:
        logger.info("=== INFORMAÇÕES DO SISTEMA ===")
        logger.info(f"Versão PostgreSQL: {db_info['version'].split(',')[0]}")
        logger.info(f"Publicações no banco: {db_info['publication_count']}")
        logger.info(f"Tamanho do banco: {db_info['database_size']}")
        logger.info(f"URL de conexão: {db_info['connection_url']}")
    
    logger.info("=== SCRAPER CONFIGURADO COM SUCESSO ===")
    logger.info("Sistema pronto para scraping das publicações DJE")
    
    # TODO: Aqui será implementado o scheduler e o scraper principal
    # Por enquanto, o sistema fica em modo de teste
    
    try:
        logger.info("Pressione Ctrl+C para finalizar o scraper")
        
        # Mantém o programa rodando
        import time
        while True:
            time.sleep(60)  # Aguarda 1 minuto
            logger.info("Scraper ativo - aguardando implementação do scheduler...")
            
    except KeyboardInterrupt:
        logger.info("Finalizando scraper...")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)
    
    logger.info("Scraper finalizado")


if __name__ == "__main__":
    main()