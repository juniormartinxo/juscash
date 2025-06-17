"""
Main entry point for the monitoring and processing services.

This script starts both the file monitor and API worker services
to continuously monitor for new JSON files and process them.
"""

import argparse
import logging
import multiprocessing
import os
import signal
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.monitoring.file_monitor import FileMonitorService
from src.infrastructure.monitoring.api_worker import APIWorker
from src.infrastructure.config.settings import Settings


logger = logging.getLogger(__name__)


class MonitoringOrchestrator:
    """Orchestrates the file monitoring and API worker services."""

    def __init__(
        self,
        monitored_path: str,
        log_path: str,
        api_endpoint: str,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize the monitoring orchestrator.

        Args:
            monitored_path: Path to monitor for new JSON files
            log_path: Path for storing error logs
            api_endpoint: API endpoint URL
            redis_url: Redis connection URL
        """
        self.monitored_path = monitored_path
        self.log_path = log_path
        self.api_endpoint = api_endpoint

        # Get Redis URL from settings if not provided
        if not redis_url:
            settings = Settings()
            redis_url = settings.redis_url or "redis://localhost:6379/0"

        self.redis_url = redis_url
        self.processes = []

    def _start_file_monitor(self) -> multiprocessing.Process:
        """Start the file monitoring service in a separate process."""

        def run_monitor():
            # Configure logging for subprocess
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

            service = FileMonitorService(
                monitored_path=self.monitored_path, redis_url=self.redis_url
            )
            service.start()

        process = multiprocessing.Process(target=run_monitor, name="FileMonitor")
        process.start()
        logger.info(f"Started file monitor process (PID: {process.pid})")
        return process

    def _start_api_worker(self) -> multiprocessing.Process:
        """Start the API worker service in a separate process."""

        def run_worker():
            # Configure logging for subprocess
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

            worker = APIWorker(
                redis_url=self.redis_url,
                api_endpoint=self.api_endpoint,
                log_path=self.log_path,
            )
            worker.start()

        process = multiprocessing.Process(target=run_worker, name="APIWorker")
        process.start()
        logger.info(f"Started API worker process (PID: {process.pid})")
        return process

    def start(self) -> None:
        """Start all services."""
        logger.info("Starting monitoring orchestrator...")

        # Convert paths to absolute paths
        monitored_path_abs = Path(self.monitored_path).resolve()
        log_path_abs = Path(self.log_path).resolve()

        logger.info(f"Monitored path: {self.monitored_path} -> {monitored_path_abs}")
        logger.info(f"Log path: {self.log_path} -> {log_path_abs}")
        logger.info(f"API endpoint: {self.api_endpoint}")
        logger.info(f"Redis URL: {self.redis_url}")

        # Update paths to absolute
        self.monitored_path = str(monitored_path_abs)
        self.log_path = str(log_path_abs)

        # Ensure directories exist
        Path(self.monitored_path).mkdir(parents=True, exist_ok=True)
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        # Check if directories were created
        if Path(self.monitored_path).exists():
            logger.info(f"Monitored directory exists: {self.monitored_path}")
        else:
            logger.error(f"Failed to create monitored directory: {self.monitored_path}")

        if Path(self.log_path).exists():
            logger.info(f"Log directory exists: {self.log_path}")
        else:
            logger.error(f"Failed to create log directory: {self.log_path}")

        # Start services
        self.processes.append(self._start_file_monitor())
        self.processes.append(self._start_api_worker())

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Monitor processes
        try:
            while True:
                for process in self.processes[:]:
                    if not process.is_alive():
                        logger.warning(
                            f"Process {process.name} (PID: {process.pid}) died"
                        )
                        self.processes.remove(process)

                        # Restart the process
                        if process.name == "FileMonitor":
                            self.processes.append(self._start_file_monitor())
                        elif process.name == "APIWorker":
                            self.processes.append(self._start_api_worker())

                # Check every 5 seconds
                import time

                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Orchestrator interrupted by user")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def stop(self) -> None:
        """Stop all services."""
        logger.info("Stopping all services...")

        for process in self.processes:
            if process.is_alive():
                logger.info(f"Terminating {process.name} (PID: {process.pid})")
                process.terminate()
                process.join(timeout=5)

                if process.is_alive():
                    logger.warning(f"Force killing {process.name}")
                    process.kill()
                    process.join()

        logger.info("All services stopped")


def main():
    """Main entry point for the monitoring system."""
    # Determine base path relative to this script
    script_dir = Path(__file__).parent.parent.parent.parent

    parser = argparse.ArgumentParser(
        description="JSON file monitoring and processing system"
    )
    parser.add_argument(
        "--monitored-path",
        default=str(script_dir / "reports" / "json"),
        help="Path to monitor for new JSON files",
    )
    parser.add_argument(
        "--log-path",
        default=str(script_dir / "reports" / "log"),
        help="Path for storing error logs",
    )
    parser.add_argument(
        "--api-endpoint", required=True, help="API endpoint URL for sending JSON data"
    )
    parser.add_argument(
        "--redis-url", help="Redis connection URL (overrides environment variable)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and start orchestrator
    orchestrator = MonitoringOrchestrator(
        monitored_path=args.monitored_path,
        log_path=args.log_path,
        api_endpoint=args.api_endpoint,
        redis_url=args.redis_url,
    )

    try:
        orchestrator.start()
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
