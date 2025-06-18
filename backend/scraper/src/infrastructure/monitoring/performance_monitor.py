"""
Monitor de performance para o scraper
"""

import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class PerformanceMetric:
    """Métrica de performance"""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    network_sent_mb: float
    network_recv_mb: float
    disk_read_mb: float
    disk_write_mb: float
    active_connections: int


@dataclass
class ScrapingSession:
    """Sessão de scraping com métricas"""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_processed: int = 0
    publications_found: int = 0
    errors_count: int = 0
    metrics: List[PerformanceMetric] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def pages_per_second(self) -> Optional[float]:
        duration = self.duration_seconds
        if duration and duration > 0:
            return self.pages_processed / duration
        return None


class PerformanceMonitor:
    """
    Monitor de performance do sistema durante scraping
    """

    def __init__(self, sample_interval: float = 30.0):
        self.sample_interval = sample_interval
        self.current_session: Optional[ScrapingSession] = None
        self.historical_sessions: List[ScrapingSession] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._initial_network_stats = None
        self._initial_disk_stats = None

    async def start_session(self, session_id: str) -> None:
        """Inicia uma nova sessão de monitoramento"""
        logger.info(f"📊 Iniciando monitoramento de performance: {session_id}")

        # Finalizar sessão anterior se existir
        if self.current_session:
            await self.end_session()

        # Capturar estatísticas iniciais
        self._initial_network_stats = psutil.net_io_counters()
        self._initial_disk_stats = psutil.disk_io_counters()

        self.current_session = ScrapingSession(
            session_id=session_id, start_time=datetime.now()
        )

        # Iniciar monitoramento
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def end_session(self) -> Optional[ScrapingSession]:
        """Finaliza sessão atual e retorna métricas"""
        if not self.current_session:
            return None

        logger.info(f"📊 Finalizando monitoramento: {self.current_session.session_id}")

        # Parar monitoramento
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Finalizar sessão
        self.current_session.end_time = datetime.now()

        # Capturar métrica final
        final_metric = self._capture_current_metric()
        if final_metric:
            self.current_session.metrics.append(final_metric)

        # Gerar relatório
        self._log_session_summary(self.current_session)

        # Mover para histórico
        self.historical_sessions.append(self.current_session)
        completed_session = self.current_session
        self.current_session = None

        return completed_session

    def update_session_stats(self, **kwargs) -> None:
        """Atualiza estatísticas da sessão atual"""
        if not self.current_session:
            return

        for key, value in kwargs.items():
            if hasattr(self.current_session, key):
                setattr(self.current_session, key, value)

    async def _monitoring_loop(self) -> None:
        """Loop principal de monitoramento"""
        try:
            while True:
                if self.current_session:
                    metric = self._capture_current_metric()
                    if metric:
                        self.current_session.metrics.append(metric)

                await asyncio.sleep(self.sample_interval)

        except asyncio.CancelledError:
            logger.debug("📊 Loop de monitoramento cancelado")
        except Exception as error:
            logger.error(f"❌ Erro no monitoramento: {error}")

    def _capture_current_metric(self) -> Optional[PerformanceMetric]:
        """Captura métrica atual do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)

            # Rede
            network_stats = psutil.net_io_counters()
            if self._initial_network_stats:
                network_sent_mb = (
                    network_stats.bytes_sent - self._initial_network_stats.bytes_sent
                ) / (1024 * 1024)
                network_recv_mb = (
                    network_stats.bytes_recv - self._initial_network_stats.bytes_recv
                ) / (1024 * 1024)
            else:
                network_sent_mb = network_recv_mb = 0

            # Disco
            disk_stats = psutil.disk_io_counters()
            if self._initial_disk_stats and disk_stats:
                disk_read_mb = (
                    disk_stats.read_bytes - self._initial_disk_stats.read_bytes
                ) / (1024 * 1024)
                disk_write_mb = (
                    disk_stats.write_bytes - self._initial_disk_stats.write_bytes
                ) / (1024 * 1024)
            else:
                disk_read_mb = disk_write_mb = 0

            # Conexões de rede
            connections = psutil.net_connections()
            active_connections = len(
                [c for c in connections if c.status == "ESTABLISHED"]
            )

            return PerformanceMetric(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                active_connections=active_connections,
            )

        except Exception as error:
            logger.warning(f"⚠️  Erro ao capturar métricas: {error}")
            return None

    def _log_session_summary(self, session: ScrapingSession) -> None:
        """Gera log do resumo da sessão"""
        if not session.metrics:
            logger.warning("⚠️  Nenhuma métrica coletada para a sessão")
            return

        # Calcular estatísticas
        avg_cpu = sum(m.cpu_percent for m in session.metrics) / len(session.metrics)
        max_cpu = max(m.cpu_percent for m in session.metrics)

        avg_memory = sum(m.memory_mb for m in session.metrics) / len(session.metrics)
        max_memory = max(m.memory_mb for m in session.metrics)

        total_network_sent = (
            session.metrics[-1].network_sent_mb if session.metrics else 0
        )
        total_network_recv = (
            session.metrics[-1].network_recv_mb if session.metrics else 0
        )

        logger.info("📊 Resumo da Sessão de Performance:")
        logger.info(f"   🆔 ID: {session.session_id}")
        logger.info(f"   ⏱️  Duração: {session.duration_seconds:.1f}s")
        logger.info(f"   📄 Páginas processadas: {session.pages_processed}")
        logger.info(f"   📋 Publicações encontradas: {session.publications_found}")
        logger.info(f"   ❌ Erros: {session.errors_count}")
        logger.info(f"   🖥️  CPU: {avg_cpu:.1f}% (máx: {max_cpu:.1f}%)")
        logger.info(f"   💾 Memória: {avg_memory:.1f}MB (máx: {max_memory:.1f}MB)")
        logger.info(
            f"   🌐 Rede: ↑{total_network_sent:.2f}MB ↓{total_network_recv:.2f}MB"
        )

        if session.pages_per_second:
            logger.info(
                f"   📈 Performance: {session.pages_per_second:.2f} páginas/segundo"
            )

    def get_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna relatório detalhado de uma sessão"""
        # Buscar sessão no histórico
        session = None
        for s in self.historical_sessions:
            if s.session_id == session_id:
                session = s
                break

        if not session:
            return None

        if not session.metrics:
            return {"error": "No metrics available"}

        # Calcular estatísticas detalhadas
        metrics_data = {
            "cpu": [m.cpu_percent for m in session.metrics],
            "memory": [m.memory_mb for m in session.metrics],
            "network_sent": [m.network_sent_mb for m in session.metrics],
            "network_recv": [m.network_recv_mb for m in session.metrics],
            "connections": [m.active_connections for m in session.metrics],
        }

        report = {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_seconds": session.duration_seconds,
            "pages_processed": session.pages_processed,
            "publications_found": session.publications_found,
            "errors_count": session.errors_count,
            "pages_per_second": session.pages_per_second,
            "metrics": {
                "samples_count": len(session.metrics),
                "cpu": {
                    "avg": sum(metrics_data["cpu"]) / len(metrics_data["cpu"]),
                    "min": min(metrics_data["cpu"]),
                    "max": max(metrics_data["cpu"]),
                },
                "memory_mb": {
                    "avg": sum(metrics_data["memory"]) / len(metrics_data["memory"]),
                    "min": min(metrics_data["memory"]),
                    "max": max(metrics_data["memory"]),
                },
                "network_total_mb": {
                    "sent": metrics_data["network_sent"][-1]
                    if metrics_data["network_sent"]
                    else 0,
                    "received": metrics_data["network_recv"][-1]
                    if metrics_data["network_recv"]
                    else 0,
                },
                "peak_connections": max(metrics_data["connections"])
                if metrics_data["connections"]
                else 0,
            },
        }

        return report
