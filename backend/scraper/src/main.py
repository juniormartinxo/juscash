import asyncio
from loguru import logger
from src.scheduler import DJEScheduler
from src.database import DatabaseService
import os

async def main():
    """Função principal"""
    logger.info("Iniciando sistema de scraping DJE")
    
    # Configurar banco de dados
    db_service = DatabaseService(os.getenv('DATABASE_URL'))
    await db_service.init()
    
    # Iniciar scheduler
    scheduler = DJEScheduler(db_service)
    scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())