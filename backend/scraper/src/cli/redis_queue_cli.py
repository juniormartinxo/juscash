"""
CLI para gerenciamento da fila Redis
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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

    def print_banner(self):
        """Imprime banner do CLI"""
        print("\n" + "=" * 60)
        print("🔧 REDIS QUEUE CLI - Gerenciamento de Fila de Publicações")
        print("=" * 60)
        print(f"Redis: {self.settings.redis.host}:{self.settings.redis.port}")
        print(f"Fila: {self.settings.redis.queue_name}")
        print("=" * 60 + "\n")

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
            print(f"📦 Batch size: {worker_stats['settings']['batch_size']}")
            print(f"🔄 Max tentativas: {worker_stats['settings']['max_retries']}")
            print(f"⏰ Delay retry: {worker_stats['settings']['retry_delay']}s")

        except Exception as error:
            print(f"❌ Erro ao obter estatísticas: {error}")

    def peek_queue(self, limit: int = 5):
        """Visualiza algumas publicações da fila sem removê-las"""
        try:
            queue_key = self.settings.redis.queue_name

            # Usar LRANGE para visualizar sem remover
            items = self.queue.redis_client.lrange(queue_key, 0, limit - 1)

            if not items:
                print("📝 Fila vazia")
                return

            print(f"👀 PRÓXIMAS {len(items)} PUBLICAÇÕES NA FILA")
            print("-" * 50)

            for i, item_json in enumerate(items, 1):
                try:
                    data = json.loads(item_json)
                    enqueued_time = datetime.fromtimestamp(data.get("enqueued_at", 0))
                    retry_count = data.get("retry_count", 0)

                    print(f"{i}. Processo: {data.get('process_number', 'N/A')}")
                    print(
                        f"   Enfileirado: {enqueued_time.strftime('%d/%m/%Y %H:%M:%S')}"
                    )
                    print(f"   Tentativas: {retry_count}")
                    print(f"   Autores: {len(data.get('authors', []))}")
                    print(f"   Advogados: {len(data.get('lawyers', []))}")
                    print(f"   Valores: {len(data.get('monetary_values', []))}")
                    print()
                except Exception as e:
                    print(f"{i}. ❌ Erro ao decodificar item: {e}")

        except Exception as error:
            print(f"❌ Erro ao visualizar fila: {error}")

    def clear_queue(self):
        """Limpa a fila (apenas em desenvolvimento)"""
        if self.settings.environment != "development":
            print("❌ Limpeza de fila não permitida em produção!")
            return

        try:
            # Confirmar ação
            response = input(
                "⚠️  Tem certeza que deseja limpar TODAS as filas? (sim/não): "
            )
            if response.lower() not in ["sim", "s", "yes", "y"]:
                print("❌ Operação cancelada")
                return

            self.queue.clear_queue()
            print("✅ Todas as filas foram limpas")

        except Exception as error:
            print(f"❌ Erro ao limpar fila: {error}")

    def inspect_dlq(self, limit: int = 10):
        """Inspeciona Dead Letter Queue"""
        try:
            dlq_key = f"{self.settings.redis.queue_name}:dlq"
            items = self.queue.redis_client.lrange(dlq_key, 0, limit - 1)

            if not items:
                print("💀 Dead Letter Queue vazia")
                return

            print(f"💀 DEAD LETTER QUEUE - {len(items)} ITENS")
            print("-" * 50)

            for i, item_json in enumerate(items, 1):
                try:
                    data = json.loads(item_json)
                    dlq_time = datetime.fromtimestamp(data.get("dlq_timestamp", 0))
                    retry_count = data.get("retry_count", 0)
                    reason = data.get("dlq_reason", "unknown")

                    print(f"{i}. Processo: {data.get('process_number', 'N/A')}")
                    print(f"   Motivo: {reason}")
                    print(f"   Tentativas: {retry_count}")
                    print(f"   DLQ em: {dlq_time.strftime('%d/%m/%Y %H:%M:%S')}")
                    print()
                except Exception as e:
                    print(f"{i}. ❌ Erro ao decodificar item: {e}")

        except Exception as error:
            print(f"❌ Erro ao inspecionar DLQ: {error}")

    def retry_dlq_items(self):
        """Move itens da DLQ de volta para a fila principal"""
        if self.settings.environment != "development":
            print("❌ Operação não permitida em produção!")
            return

        try:
            dlq_key = f"{self.settings.redis.queue_name}:dlq"
            queue_key = self.settings.redis.queue_name

            # Contar itens na DLQ
            dlq_size = self.queue.redis_client.llen(dlq_key)

            if dlq_size == 0:
                print("💀 Dead Letter Queue vazia")
                return

            # Confirmar ação
            response = input(f"⚠️  Reprocessar {dlq_size} itens da DLQ? (sim/não): ")
            if response.lower() not in ["sim", "s", "yes", "y"]:
                print("❌ Operação cancelada")
                return

            # Mover todos os itens
            moved_count = 0
            while True:
                item = self.queue.redis_client.rpop(dlq_key)
                if not item:
                    break

                # Resetar contador de tentativas
                try:
                    data = json.loads(item)
                    data["retry_count"] = 0
                    data.pop("dlq_timestamp", None)
                    data.pop("dlq_reason", None)
                    item = json.dumps(data)
                except:
                    pass  # Se não conseguir resetar, move assim mesmo

                self.queue.redis_client.lpush(queue_key, item)
                moved_count += 1

            print(f"✅ {moved_count} itens movidos da DLQ para a fila principal")

        except Exception as error:
            print(f"❌ Erro ao processar DLQ: {error}")

    async def start_worker_standalone(self):
        """Inicia worker em modo standalone"""
        print("🔄 Iniciando worker Redis em modo standalone...")
        print("Pressione Ctrl+C para parar\n")

        try:
            await self.worker.start()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupção pelo usuário")
            await self.worker.stop()
        except Exception as error:
            print(f"❌ Erro no worker: {error}")

    def show_help(self):
        """Mostra ajuda dos comandos"""
        print("📖 COMANDOS DISPONÍVEIS")
        print("-" * 30)
        print("stats       - Mostra estatísticas da fila")
        print("peek [N]    - Visualiza N publicações da fila (padrão: 5)")
        print("dlq [N]     - Inspeciona Dead Letter Queue (padrão: 10)")
        print("clear       - Limpa todas as filas (apenas dev)")
        print("retry-dlq   - Move itens da DLQ para fila principal (apenas dev)")
        print("worker      - Inicia worker em modo standalone")
        print("help        - Mostra esta ajuda")
        print("exit        - Sair do CLI")

    def run_interactive(self):
        """Executa CLI em modo interativo"""
        self.print_banner()
        self.show_help()

        while True:
            try:
                command = input("\n🔧 redis-queue> ").strip().lower()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0]

                if cmd == "exit":
                    break
                elif cmd == "stats":
                    self.show_stats()
                elif cmd == "peek":
                    limit = int(parts[1]) if len(parts) > 1 else 5
                    self.peek_queue(limit)
                elif cmd == "dlq":
                    limit = int(parts[1]) if len(parts) > 1 else 10
                    self.inspect_dlq(limit)
                elif cmd == "clear":
                    self.clear_queue()
                elif cmd == "retry-dlq":
                    self.retry_dlq_items()
                elif cmd == "worker":
                    await self.start_worker_standalone()
                elif cmd == "help":
                    self.show_help()
                else:
                    print(f"❌ Comando desconhecido: {cmd}")
                    print("Digite 'help' para ver os comandos disponíveis")

            except KeyboardInterrupt:
                break
            except Exception as error:
                print(f"❌ Erro: {error}")

        print("\n👋 Saindo do Redis Queue CLI")


def main():
    """Função principal do CLI"""
    cli = RedisQueueCLI()

    if len(sys.argv) > 1:
        # Modo comando único
        command = sys.argv[1].lower()

        if command == "stats":
            cli.show_stats()
        elif command == "peek":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            cli.peek_queue(limit)
        elif command == "worker":
            asyncio.run(cli.start_worker_standalone())
        else:
            print(f"❌ Comando desconhecido: {command}")
            sys.exit(1)
    else:
        # Modo interativo
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()
