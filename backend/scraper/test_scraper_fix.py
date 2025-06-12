#!/usr/bin/env python3
"""
Script para testar se as correções dos adaptadores funcionaram.
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.secondary.redis_cache import RedisCacheAdapter
from src.adapters.primary.scheduler_adapter import APSchedulerAdapter
from src.shared.logger import get_logger

logger = get_logger(__name__)


async def test_redis_adapter():
    """Testa o RedisCacheAdapter."""
    logger.info("Testando RedisCacheAdapter...")
    
    # Criar adaptador (sem conectar ao Redis real)
    adapter = RedisCacheAdapter("redis://localhost:6388")
    
    # Verificar se todos os métodos existem
    methods = ['get', 'set', 'delete', 'exists', 'clear_all', 'initialize']
    
    for method in methods:
        if hasattr(adapter, method):
            logger.info(f"✅ Método '{method}' encontrado")
        else:
            logger.error(f"❌ Método '{method}' NÃO encontrado")
            return False
    
    return True


async def test_scheduler_adapter():
    """Testa o APSchedulerAdapter."""
    logger.info("\nTestando APSchedulerAdapter...")
    
    # Criar adaptador
    adapter = APSchedulerAdapter()
    
    # Verificar se todos os métodos existem
    methods = [
        'initialize', 'schedule_daily_scraping', 'schedule_one_time_execution',
        'cancel_job', 'start', 'stop', 'is_running'
    ]
    
    for method in methods:
        if hasattr(adapter, method):
            logger.info(f"✅ Método '{method}' encontrado")
        else:
            logger.error(f"❌ Método '{method}' NÃO encontrado")
            return False
    
    return True


async def main():
    """Função principal."""
    logger.info("=== Testando correções dos adaptadores ===\n")
    
    # Testar Redis
    redis_ok = await test_redis_adapter()
    
    # Testar Scheduler
    scheduler_ok = await test_scheduler_adapter()
    
    if redis_ok and scheduler_ok:
        logger.info("\n✅ Todos os adaptadores estão corretos!")
        return 0
    else:
        logger.error("\n❌ Alguns adaptadores ainda têm problemas!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)