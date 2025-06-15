"""
CLI para gerenciamento da fila Redis
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Adicionar o diretório src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.queue.redis_queue_adapter import RedisQueueAdapter
from infrastructure.queue.publication_worker import PublicationWorker
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class RedisQueueCLI:
    """CLI para gerenciamento da fila Redis"""

    def __init__(self):
        self.queue = RedisQueueAdapter()
        self.worker = PublicationWorker()
        self.settings = get_settings()

    def show_stats(self):
        """Mostra estatísticas da fila"""
        try:
            stats = self.queue.get_queue_stats()
            worker_stats = self.worker.get_stats()

            print("📊 ESTATÍSTICAS DA FILA")
            print("-" * 30)
            print(f"📝 Fila principal: {stats['queue_size']} publicações")
            print(f"⏰ Fila com delay: {stats['delayed_queue_size']} publicações")
            print(f"📈 Total pendente: {stats['total_pending']} publicações")

            # Dead Letter Queue
            try:
                dlq_key = f"{self.settings.redis.queue_name}:dlq"
                dlq_size = self.queue.redis_client.llen(dlq_key)
                print(f"💀 Dead Letter Queue: {dlq_size} publicações")
            except:
                print("💀 Dead Letter Queue: N/A")

            print(
                f"\n🔄 Worker ativo: {'✅' if worker_stats['worker_running'] else '❌'}"
            )

        except Exception as error:
            print(f"❌ Erro ao obter estatísticas: {error}")

    async def start_worker_standalone(self):
        """Inicia worker em modo standalone"""
        print("🔄 Iniciando worker Redis...")
        print("Pressione Ctrl+C para parar\n")

        try:
            await self.worker.start()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupção pelo usuário")
            await self.worker.stop()


def main():
    """Função principal do CLI"""
    cli = RedisQueueCLI()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "stats":
            cli.show_stats()
        elif command == "worker":
            asyncio.run(cli.start_worker_standalone())
        else:
            print(f"❌ Comando desconhecido: {command}")
            print("Comandos disponíveis: stats, worker")
    else:
        print("Redis Queue CLI")
        print("Uso: python redis_cli.py [stats|worker]")


if __name__ == "__main__":
    main()
