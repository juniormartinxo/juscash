#!/usr/bin/env python3
"""
Multi-Date Multi-Worker Scraper para DJE-SP
Busca processos em múltiplas datas de forma concorrente com controle de progresso
Data inicial: 17/03/2025 até hoje
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import signal
import threading
from dataclasses import dataclass, asdict
from uuid import uuid4

# Adicionar o diretório src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings
from application.services.scraping_orchestrator import ScrapingOrchestrator
from shared.container import Container

logger = setup_logger(__name__)


@dataclass
class DateProcessingStatus:
    """Status de processamento de uma data específica"""

    date: str
    processed: bool = False
    worker_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    publications_found: int = 0
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class WorkerProgress:
    """Progresso de um worker"""

    worker_id: str
    current_date: Optional[str] = None
    dates_processed: int = 0
    total_publications: int = 0
    status: str = "idle"  # idle, working, completed, error


class MultiDateScraper:
    """Scraper que processa múltiplas datas com multi-workers"""

    def __init__(
        self, start_date: str, end_date: str, json_file_path: str, num_workers: int = 3
    ):
        self.start_date = self._parse_date(start_date)
        self.end_date = (
            self._parse_date(end_date) if end_date != "NOW" else datetime.now()
        )
        self.json_file_path = Path(json_file_path)
        self.num_workers = num_workers

        # Estado interno
        self.progress_data: Dict[str, DateProcessingStatus] = {}
        self.workers_progress: Dict[str, WorkerProgress] = {}
        self.date_queue = asyncio.Queue()
        self.lock = threading.Lock()
        self.shutdown_event = asyncio.Event()

        # Container e configurações
        self.settings = get_settings()
        self.container = Container()

        self._load_or_create_progress_file()

        logger.info(f"🚀 MultiDateScraper inicializado")
        logger.info(
            f"📅 Período: {self.start_date.strftime('%d/%m/%Y')} até {self.end_date.strftime('%d/%m/%Y')}"
        )
        logger.info(f"👥 Workers: {self.num_workers}")
        logger.info(f"📊 Arquivo de progresso: {self.json_file_path}")

    def _parse_date(self, date_str: str) -> datetime:
        """Parse data no formato DD/MM/YYYY"""
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            logger.error(f"❌ Formato de data inválido: {date_str}. Use DD/MM/YYYY")
            raise

    def _load_or_create_progress_file(self):
        """Carrega ou cria o arquivo de progresso"""
        try:
            if self.json_file_path.exists():
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Converter dict para DateProcessingStatus
                for date_str, status_data in data.get("dates", {}).items():
                    self.progress_data[date_str] = DateProcessingStatus(**status_data)

                logger.info(
                    f"📂 Arquivo de progresso carregado: {len(self.progress_data)} datas"
                )
            else:
                self._initialize_progress_data()
                self._save_progress()
                logger.info("📝 Arquivo de progresso inicial criado")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar arquivo de progresso: {e}")
            self._initialize_progress_data()

    def _initialize_progress_data(self):
        """Inicializa dados de progresso para todas as datas"""
        logger.info(
            f"🔧 Inicializando datas de {self.start_date.strftime('%d/%m/%Y')} até {self.end_date.strftime('%d/%m/%Y')}"
        )

        current_date = self.start_date
        count = 0
        while current_date <= self.end_date:
            date_str = current_date.strftime("%d/%m/%Y")
            if date_str not in self.progress_data:
                self.progress_data[date_str] = DateProcessingStatus(date=date_str)
                count += 1
            current_date += timedelta(days=1)

        logger.info(f"✅ Inicializadas {count} datas para processamento")

    def _save_progress(self):
        """Salva progresso no arquivo JSON"""
        try:
            with self.lock:
                progress_dict = {
                    "metadata": {
                        "start_date": self.start_date.strftime("%d/%m/%Y"),
                        "end_date": self.end_date.strftime("%d/%m/%Y"),
                        "num_workers": self.num_workers,
                        "last_updated": datetime.now().isoformat(),
                        "total_dates": len(self.progress_data),
                        "processed_dates": sum(
                            1
                            for status in self.progress_data.values()
                            if status.processed
                        ),
                        "total_publications": sum(
                            status.publications_found
                            for status in self.progress_data.values()
                        ),
                    },
                    "dates": {
                        date: asdict(status)
                        for date, status in self.progress_data.items()
                    },
                    "workers": {
                        worker_id: asdict(progress)
                        for worker_id, progress in self.workers_progress.items()
                    },
                }

                # Salvar com backup
                backup_path = self.json_file_path.with_suffix(".json.backup")
                if self.json_file_path.exists():
                    self.json_file_path.rename(backup_path)

                with open(self.json_file_path, "w", encoding="utf-8") as f:
                    json.dump(progress_dict, f, indent=2, ensure_ascii=False)

                # Remover backup se salvamento foi bem-sucedido
                if backup_path.exists():
                    backup_path.unlink()

        except Exception as e:
            logger.error(f"❌ Erro ao salvar progresso: {e}")

    async def _populate_date_queue(self):
        """Popula a fila de datas com datas não processadas"""
        unprocessed_dates = [
            date_str
            for date_str, status in self.progress_data.items()
            if not status.processed or status.error
        ]

        # Ordenar datas (mais antigas primeiro)
        unprocessed_dates.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))

        for date_str in unprocessed_dates:
            await self.date_queue.put(date_str)

        logger.info(
            f"📅 {len(unprocessed_dates)} datas adicionadas à fila de processamento"
        )

    async def _worker(self, worker_id: str):
        """Worker que processa datas da fila"""
        self.workers_progress[worker_id] = WorkerProgress(worker_id=worker_id)
        orchestrator = None

        logger.info(f"👷 Worker {worker_id} iniciado")

        try:
            orchestrator = ScrapingOrchestrator(self.container)

            while not self.shutdown_event.is_set():
                try:
                    # Pegar próxima data da fila com timeout
                    date_str = await asyncio.wait_for(
                        self.date_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # Verificar se ainda há trabalho ou se deve parar
                    if self.date_queue.empty():
                        break
                    continue

                # Atualizar status do worker
                self.workers_progress[worker_id].current_date = date_str
                self.workers_progress[worker_id].status = "working"

                try:
                    # Processar data com timeout
                    await asyncio.wait_for(
                        self._process_date(worker_id, date_str, orchestrator),
                        timeout=300,  # 5 minutos por data
                    )

                    # Marcar tarefa como concluída
                    self.date_queue.task_done()
                    self.workers_progress[worker_id].dates_processed += 1

                except asyncio.TimeoutError:
                    logger.error(
                        f"⏰ Timeout processando data {date_str} no worker {worker_id}"
                    )
                    self.progress_data[date_str].error = "Timeout durante processamento"
                    self.progress_data[date_str].retry_count += 1

                    # Recolocar na fila se não excedeu tentativas
                    if self.progress_data[date_str].retry_count < 3:
                        await self.date_queue.put(date_str)

                    self.date_queue.task_done()

                except Exception as e:
                    logger.error(
                        f"❌ Erro processando data {date_str} no worker {worker_id}: {e}"
                    )
                    self.date_queue.task_done()

                finally:
                    self.workers_progress[worker_id].current_date = None
                    self.workers_progress[worker_id].status = "idle"

                    # Delay entre processamentos para evitar sobrecarga
                    await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Erro crítico no worker {worker_id}: {e}")
            self.workers_progress[worker_id].status = "error"
        finally:
            # Cleanup do orchestrator
            if orchestrator and hasattr(orchestrator.container, "cleanup"):
                try:
                    await orchestrator.container.cleanup()
                    logger.debug(f"🧹 Cleanup worker {worker_id} concluído")
                except Exception as e:
                    logger.warning(f"⚠️ Erro no cleanup do worker {worker_id}: {e}")

            self.workers_progress[worker_id].status = "completed"
            logger.info(f"👷 Worker {worker_id} finalizado")

    async def _process_date(
        self, worker_id: str, date_str: str, orchestrator: ScrapingOrchestrator
    ):
        """Processa uma data específica"""
        logger.info(f"📅 Worker {worker_id} processando data {date_str}")

        status = self.progress_data[date_str]
        status.worker_id = worker_id
        status.start_time = datetime.now().isoformat()
        status.error = None

        try:
            # Adaptar o orquestrador para usar data específica
            execution = await self._scrape_for_date(date_str, orchestrator)

            # Atualizar status
            status.processed = True
            status.end_time = datetime.now().isoformat()
            status.publications_found = execution.publications_found

            # Atualizar progresso do worker
            self.workers_progress[
                worker_id
            ].total_publications += execution.publications_found

            logger.info(
                f"✅ Data {date_str} processada pelo worker {worker_id}: "
                f"{execution.publications_found} publicações encontradas"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao processar data {date_str}: {e}")
            status.error = str(e)
            status.retry_count += 1

            # Recolocar na fila se não excedeu tentativas
            if status.retry_count < 3:
                await self.date_queue.put(date_str)
                logger.info(
                    f"🔄 Data {date_str} recolocada na fila (tentativa {status.retry_count}/3)"
                )

        finally:
            # Salvar progresso
            self._save_progress()

    async def _scrape_for_date(self, date_str: str, orchestrator: ScrapingOrchestrator):
        """Executa scraping para uma data específica"""

        from domain.entities.scraping_execution import ScrapingExecution, ExecutionType
        from uuid import uuid4

        execution = ScrapingExecution(
            execution_id=f"{date_str}_{str(uuid4())[:8]}",
            execution_type=ExecutionType.MANUAL,
            criteria_used={
                "search_terms": ["RPV", "pagamento pelo INSS"],
                "date": date_str,
                "caderno": "3",
                "instancia": "1",
                "local": "Capital",
                "parte": "1",
            },
        )

        try:
            # Extrair publicações usando o orquestrador adaptado
            from application.usecases.extract_publications import (
                ExtractPublicationsUseCase,
            )
            from application.usecases.save_publications_to_files import (
                SavePublicationsToFilesUseCase,
            )

            extract_usecase = ExtractPublicationsUseCase(
                orchestrator.container.web_scraper
            )
            save_usecase = SavePublicationsToFilesUseCase()

            # Modificar o scraper para usar a data específica
            await self._configure_scraper_for_date(
                orchestrator.container.web_scraper, date_str
            )

            # Extrair publicações
            publications = []
            search_terms = ["RPV", "pagamento pelo INSS"]

            async for publication in extract_usecase.execute(
                search_terms, max_pages=20
            ):
                publications.append(publication)
                execution.publications_found += 1

            # Salvar publicações
            if publications:
                save_stats = await save_usecase.execute(publications)
                execution.publications_saved = save_stats["saved"]
                execution.publications_failed = save_stats["failed"]

            execution.mark_as_completed()

        except Exception as error:
            logger.error(f"❌ Erro no scraping para {date_str}: {error}")
            execution.mark_as_failed(
                {"error": str(error), "type": type(error).__name__}
            )
            raise

        return execution

    async def _configure_scraper_for_date(self, web_scraper, date_str: str):
        """Configura o scraper para usar uma data específica"""
        # Injetar a data no scraper adapter
        if hasattr(web_scraper, "_target_date"):
            web_scraper._target_date = date_str
        else:
            # Adicionar atributo se não existir
            setattr(web_scraper, "_target_date", date_str)

    async def run(self):
        """Executa o scraping multi-data com multi-workers"""
        logger.info("🚀 Iniciando scraping multi-data")

        try:
            # Registrar handlers de shutdown
            self._register_signal_handlers()

            # Popular fila de datas
            await self._populate_date_queue()

            if self.date_queue.empty():
                logger.info("✅ Todas as datas já foram processadas!")
                return

            # Iniciar workers
            tasks = []
            for i in range(self.num_workers):
                worker_id = f"worker_{i + 1}"
                task = asyncio.create_task(self._worker(worker_id))
                tasks.append(task)

            # Aguardar conclusão ou shutdown
            while not self.shutdown_event.is_set():
                # Verificar se ainda há trabalho
                if self.date_queue.empty() and all(
                    worker.status in ["idle", "completed"]
                    for worker in self.workers_progress.values()
                ):
                    logger.info("✅ Todas as datas foram processadas!")
                    break

                # Log de progresso a cada 30 segundos
                await asyncio.sleep(30)
                self._log_progress()

            # Cancelar tasks restantes
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Aguardar finalização
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            # Cleanup final
            await self.container.cleanup()
            self._save_progress()
            logger.info("🏁 Scraping multi-data finalizado")

    def _log_progress(self):
        """Log do progresso atual"""
        total_dates = len(self.progress_data)
        processed_dates = sum(
            1 for status in self.progress_data.values() if status.processed
        )
        total_publications = sum(
            status.publications_found for status in self.progress_data.values()
        )

        active_workers = sum(
            1 for worker in self.workers_progress.values() if worker.status == "working"
        )

        logger.info(
            f"📊 Progresso: {processed_dates}/{total_dates} datas processadas "
            f"({processed_dates / total_dates * 100:.1f}%) | "
            f"{total_publications} publicações | "
            f"{active_workers} workers ativos"
        )

    def _register_signal_handlers(self):
        """Registra handlers para shutdown graceful"""

        def signal_handler(signum, frame):
            logger.info(f"🛑 Sinal de shutdown recebido: {signum}")
            asyncio.create_task(self._shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _shutdown(self):
        """Shutdown graceful"""
        logger.info("🔄 Iniciando shutdown graceful...")
        self.shutdown_event.set()
        self._save_progress()
        logger.info("✅ Shutdown graceful concluído")


async def main():
    """Função principal"""
    # Parâmetros de entrada
    START_DATE = "17/03/2025"  # Ajustado para o ano atual do sistema
    END_DATE = "NOW"  # Hoje
    JSON_FILE_PATH = "src/scrap_workrs.json"
    NUM_WORKERS = 1  # Reduzido para evitar sobrecarga de recursos

    # Converter END_DATE para data atual se for "NOW"
    if END_DATE == "NOW":
        end_date_str = datetime.now().strftime("%d/%m/%Y")
    else:
        end_date_str = END_DATE

    logger.info("🌟 Iniciando Multi-Date Multi-Worker Scraper")
    logger.info(f"📅 Período: {START_DATE} até {end_date_str}")
    logger.info(f"👥 Workers: {NUM_WORKERS}")
    logger.info(f"📂 Arquivo de progresso: {JSON_FILE_PATH}")

    try:
        scraper = MultiDateScraper(
            start_date=START_DATE,
            end_date=END_DATE,
            json_file_path=JSON_FILE_PATH,
            num_workers=NUM_WORKERS,
        )

        await scraper.run()

    except KeyboardInterrupt:
        logger.info("⌨️ Interrupção por teclado detectada")
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
