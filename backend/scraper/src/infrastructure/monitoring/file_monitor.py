"""
File monitoring service for detecting new JSON files.

This module implements a watchdog-based file system monitor that detects
new JSON files added to a specified directory and queues them for processing.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import redis
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ..config.settings import Settings


logger = logging.getLogger(__name__)


class JSONFileHandler(FileSystemEventHandler):
    """Handler for JSON file creation events."""

    def __init__(self, redis_client: redis.Redis, queue_name: str = "json_files_queue"):
        """
        Initialize the JSON file handler.

        Args:
            redis_client: Redis client instance
            queue_name: Name of the Redis queue
        """
        self.redis_client = redis_client
        self.queue_name = queue_name

    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: File creation event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if it's a JSON file
        if file_path.suffix.lower() != ".json":
            return

        logger.info(f"New JSON file detected: {file_path}")

        try:
            # Create queue item with file metadata
            queue_item = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "detected_at": datetime.now().isoformat(),
                "size": os.path.getsize(file_path),
                "status": "pending",
                "retry_count": 0,
            }

            # Add to Redis queue
            self.redis_client.lpush(self.queue_name, json.dumps(queue_item))

            logger.info(f"File {file_path.name} added to queue")

        except Exception as e:
            logger.error(f"Error adding file to queue: {e}", exc_info=True)


class FileMonitorService:
    """Service for monitoring directory for new JSON files."""

    def __init__(
        self, monitored_path: str, redis_url: str, queue_name: str = "json_files_queue"
    ):
        """
        Initialize the file monitor service.

        Args:
            monitored_path: Path to monitor for new files
            redis_url: Redis connection URL
            queue_name: Name of the Redis queue
        """
        self.monitored_path = Path(monitored_path)
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.observer: Optional[Observer] = None
        self.redis_client: Optional[redis.Redis] = None

        # Convert to absolute path and ensure monitored directory exists
        self.monitored_path = self.monitored_path.resolve()
        self.monitored_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Monitoring path resolved to: {self.monitored_path}")

    def _connect_redis(self) -> redis.Redis:
        """
        Connect to Redis with retry logic.

        Returns:
            Redis client instance
        """
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=30,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                client.ping()
                logger.info("Successfully connected to Redis")
                return client

            except redis.ConnectionError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Redis connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Redis after all retries")
                    raise

    # 🔥 NOVOS MÉTODOS - ADICIONE AQUI 🔥

    def _scan_existing_files(self) -> None:
        """Processa arquivos JSON já existentes na pasta."""
        try:
            existing_files = list(self.monitored_path.glob("*.json"))

            if existing_files:
                logger.info(
                    f"Encontrados {len(existing_files)} arquivos JSON existentes"
                )

                for file_path in existing_files:
                    try:
                        # Verificar se arquivo não está sendo processado
                        if self._is_file_complete(file_path):
                            queue_item = {
                                "file_path": str(file_path),
                                "file_name": file_path.name,
                                "detected_at": datetime.now().isoformat(),
                                "size": os.path.getsize(file_path),
                                "status": "pending",
                                "retry_count": 0,
                            }

                            # Verificar se já não está na fila
                            if not self._is_already_queued(file_path.name):
                                self.redis_client.lpush(
                                    self.queue_name, json.dumps(queue_item)
                                )
                                logger.info(
                                    f"Arquivo existente adicionado à fila: {file_path.name}"
                                )
                            else:
                                logger.info(
                                    f"Arquivo já está na fila: {file_path.name}"
                                )

                    except Exception as e:
                        logger.error(
                            f"Erro ao processar arquivo existente {file_path}: {e}"
                        )
            else:
                logger.info("Nenhum arquivo JSON existente encontrado")

        except Exception as e:
            logger.error(f"Erro no scan de arquivos existentes: {e}")

    def _is_file_complete(self, file_path: Path) -> bool:
        """Verifica se o arquivo não está sendo escrito."""
        try:
            # Verifica se consegue abrir o arquivo para leitura
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)  # Tenta fazer parse do JSON
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def _is_already_queued(self, file_name: str) -> bool:
        """Verifica se arquivo já está na fila Redis."""
        try:
            # Verificar nas três filas
            queues = [self.queue_name, "json_files_processing", "json_files_failed"]

            for queue in queues:
                queue_length = self.redis_client.llen(queue)
                if queue_length > 0:
                    items = self.redis_client.lrange(queue, 0, queue_length - 1)

                    for item in items:
                        try:
                            queue_item = json.loads(item)
                            if queue_item.get("file_name") == file_name:
                                return True
                        except json.JSONDecodeError:
                            continue

            return False
        except Exception:
            return False

    def start(self) -> None:
        """Start the file monitoring service."""
        try:
            # Connect to Redis
            self.redis_client = self._connect_redis()

            logger.info("Iniciando scan de arquivos JSON existentes...")
            self._scan_existing_files()

            # Create event handler
            event_handler = JSONFileHandler(
                redis_client=self.redis_client, queue_name=self.queue_name
            )

            # Create and configure observer
            self.observer = Observer()
            self.observer.schedule(
                event_handler, str(self.monitored_path), recursive=False
            )

            # Start monitoring
            self.observer.start()
            logger.info(f"Started monitoring directory: {self.monitored_path}")

            # Keep service running
            try:
                while True:
                    time.sleep(1)
                    # Periodic Redis connection check
                    if int(time.time()) % 30 == 0:
                        try:
                            self.redis_client.ping()
                        except redis.ConnectionError:
                            logger.warning(
                                "Lost Redis connection, attempting to reconnect..."
                            )
                            self.redis_client = self._connect_redis()
                            event_handler.redis_client = self.redis_client
                        except redis.TimeoutError:
                            logger.warning("Redis operation timed out, retrying...")
                            time.sleep(1)
                            continue

            except KeyboardInterrupt:
                logger.info("Monitoring service interrupted by user")

        except Exception as e:
            logger.error(f"Error in monitoring service: {e}", exc_info=True)
            raise

        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the file monitoring service."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("File monitoring service stopped")

        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis connection closed")


def main():
    """Main entry point for the file monitor service."""
    import argparse
    from pathlib import Path

    # Determine base path relative to this script
    script_dir = Path(__file__).parent.parent.parent.parent

    parser = argparse.ArgumentParser(description="File monitoring service")
    parser.add_argument(
        "--monitored-path",
        default=str(script_dir / "reports" / "json"),
        help="Path to monitor for new JSON files",
    )
    parser.add_argument(
        "--redis-url", help="Redis connection URL (overrides environment variable)"
    )

    args = parser.parse_args()

    # Get Redis URL from args or environment
    settings = Settings()
    redis_url = args.redis_url or settings.redis_url or "redis://localhost:6379/0"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and start service
    service = FileMonitorService(
        monitored_path=args.monitored_path, redis_url=redis_url
    )

    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        raise


if __name__ == "__main__":
    main()
