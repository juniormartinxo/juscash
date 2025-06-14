"""
Sistema de verificação de saúde do scraper
"""

import asyncio
import psutil
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class HealthStatus(Enum):
    """Status de saúde"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Resultado de verificação de saúde"""

    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: Optional[float] = None


class HealthChecker:
    """
    Sistema completo de verificação de saúde
    """

    def __init__(self):
        self.settings = get_settings()
        self.checks: List[HealthCheck] = []

        # Thresholds configuráveis
        self.thresholds = {
            "cpu_usage_warning": 70.0,
            "cpu_usage_critical": 90.0,
            "memory_usage_warning": 75.0,
            "memory_usage_critical": 90.0,
            "disk_usage_warning": 80.0,
            "disk_usage_critical": 95.0,
            "api_response_time_warning": 5.0,  # segundos
            "api_response_time_critical": 15.0,
        }

    async def run_all_checks(self) -> Dict[str, Any]:
        """Executa todas as verificações de saúde"""
        logger.info("🏥 Iniciando verificações de saúde...")

        check_functions = [
            self._check_system_resources,
            self._check_api_connectivity,
            self._check_dje_accessibility,
            self._check_disk_space,
            self._check_network_connectivity,
            self._check_log_files,
            self._check_configuration,
        ]

        # Executar verificações em paralelo
        results = await asyncio.gather(
            *[check_func() for check_func in check_functions], return_exceptions=True
        )

        # Processar resultados
        all_checks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Verificação falhou
                check_name = check_functions[i].__name__.replace("_check_", "")
                error_check = HealthCheck(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Erro durante verificação: {result}",
                    details={"error": str(result)},
                    timestamp=datetime.now(),
                )
                all_checks.append(error_check)
            else:
                all_checks.extend(result if isinstance(result, list) else [result])

        self.checks = all_checks

        # Calcular status geral
        overall_status = self._calculate_overall_status(all_checks)

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "total_checks": len(all_checks),
            "healthy_checks": len(
                [c for c in all_checks if c.status == HealthStatus.HEALTHY]
            ),
            "warning_checks": len(
                [c for c in all_checks if c.status == HealthStatus.WARNING]
            ),
            "critical_checks": len(
                [c for c in all_checks if c.status == HealthStatus.CRITICAL]
            ),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "timestamp": check.timestamp.isoformat(),
                    "response_time_ms": check.response_time_ms,
                }
                for check in all_checks
            ],
        }

        logger.info(
            f"🏥 Verificações concluídas: Status geral = {overall_status.value}"
        )
        return health_report

    async def _check_system_resources(self) -> List[HealthCheck]:
        """Verifica recursos do sistema"""
        checks = []

        # CPU
        try:
            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent >= self.thresholds["cpu_usage_critical"]:
                status = HealthStatus.CRITICAL
                message = f"Uso crítico de CPU: {cpu_percent:.1f}%"
            elif cpu_percent >= self.thresholds["cpu_usage_warning"]:
                status = HealthStatus.WARNING
                message = f"Uso alto de CPU: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Uso normal de CPU: {cpu_percent:.1f}%"

            checks.append(
                HealthCheck(
                    name="cpu_usage",
                    status=status,
                    message=message,
                    details={
                        "cpu_percent": cpu_percent,
                        "cpu_count": psutil.cpu_count(),
                    },
                    timestamp=datetime.now(),
                )
            )

        except Exception as error:
            checks.append(
                HealthCheck(
                    name="cpu_usage",
                    status=HealthStatus.UNKNOWN,
                    message=f"Erro ao verificar CPU: {error}",
                    details={"error": str(error)},
                    timestamp=datetime.now(),
                )
            )

        # Memória
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent >= self.thresholds["memory_usage_critical"]:
                status = HealthStatus.CRITICAL
                message = f"Uso crítico de memória: {memory_percent:.1f}%"
            elif memory_percent >= self.thresholds["memory_usage_warning"]:
                status = HealthStatus.WARNING
                message = f"Uso alto de memória: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Uso normal de memória: {memory_percent:.1f}%"

            checks.append(
                HealthCheck(
                    name="memory_usage",
                    status=status,
                    message=message,
                    details={
                        "memory_percent": memory_percent,
                        "total_gb": memory.total / (1024**3),
                        "available_gb": memory.available / (1024**3),
                        "used_gb": memory.used / (1024**3),
                    },
                    timestamp=datetime.now(),
                )
            )

        except Exception as error:
            checks.append(
                HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.UNKNOWN,
                    message=f"Erro ao verificar memória: {error}",
                    details={"error": str(error)},
                    timestamp=datetime.now(),
                )
            )

        return checks

    async def _check_api_connectivity(self) -> HealthCheck:
        """Verifica conectividade com a API"""
        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.settings.api.base_url}/health")

                response_time = (datetime.now() - start_time).total_seconds()

                if response.status_code == 200:
                    if response_time >= self.thresholds["api_response_time_critical"]:
                        status = HealthStatus.CRITICAL
                        message = f"API muito lenta: {response_time:.2f}s"
                    elif response_time >= self.thresholds["api_response_time_warning"]:
                        status = HealthStatus.WARNING
                        message = f"API lenta: {response_time:.2f}s"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"API respondendo: {response_time:.2f}s"
                else:
                    status = HealthStatus.CRITICAL
                    message = f"API retornou status {response.status_code}"

                return HealthCheck(
                    name="api_connectivity",
                    status=status,
                    message=message,
                    details={
                        "api_url": self.settings.api.base_url,
                        "status_code": response.status_code,
                        "response_time_seconds": response_time,
                    },
                    timestamp=datetime.now(),
                    response_time_ms=response_time * 1000,
                )

        except httpx.TimeoutException:
            return HealthCheck(
                name="api_connectivity",
                status=HealthStatus.CRITICAL,
                message="Timeout na conexão com API",
                details={"api_url": self.settings.api.base_url, "error": "timeout"},
                timestamp=datetime.now(),
            )
        except Exception as error:
            return HealthCheck(
                name="api_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Erro na conexão com API: {error}",
                details={"api_url": self.settings.api.base_url, "error": str(error)},
                timestamp=datetime.now(),
            )

    async def _check_dje_accessibility(self) -> HealthCheck:
        """Verifica acessibilidade do site DJE"""
        start_time = datetime.now()

        try:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            # Tentar acessar DJE
            await page.goto(self.settings.scraper.target_url, timeout=30000)

            response_time = (datetime.now() - start_time).total_seconds()

            # Verificar se carregou corretamente
            title = await page.title()

            # Verificar elementos importantes
            has_caderno_links = (
                await page.query_selector('a[href*="cdCaderno"]') is not None
            )

            await browser.close()
            await playwright.stop()

            if "justiça" in title.lower() or "dje" in title.lower():
                if has_caderno_links:
                    status = HealthStatus.HEALTHY
                    message = f"DJE acessível: {response_time:.2f}s"
                else:
                    status = HealthStatus.WARNING
                    message = f"DJE carregou mas links de caderno não encontrados"
            else:
                status = HealthStatus.WARNING
                message = f"DJE pode não ter carregado corretamente"

            return HealthCheck(
                name="dje_accessibility",
                status=status,
                message=message,
                details={
                    "dje_url": self.settings.scraper.target_url,
                    "page_title": title,
                    "has_caderno_links": has_caderno_links,
                    "response_time_seconds": response_time,
                },
                timestamp=datetime.now(),
                response_time_ms=response_time * 1000,
            )

        except Exception as error:
            return HealthCheck(
                name="dje_accessibility",
                status=HealthStatus.CRITICAL,
                message=f"Erro ao acessar DJE: {error}",
                details={
                    "dje_url": self.settings.scraper.target_url,
                    "error": str(error),
                },
                timestamp=datetime.now(),
            )

    async def _check_disk_space(self) -> HealthCheck:
        """Verifica espaço em disco"""
        try:
            disk_usage = psutil.disk_usage(".")
            disk_percent = (disk_usage.used / disk_usage.total) * 100

            if disk_percent >= self.thresholds["disk_usage_critical"]:
                status = HealthStatus.CRITICAL
                message = f"Espaço em disco crítico: {disk_percent:.1f}%"
            elif disk_percent >= self.thresholds["disk_usage_warning"]:
                status = HealthStatus.WARNING
                message = f"Espaço em disco baixo: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Espaço em disco normal: {disk_percent:.1f}%"

            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "total_gb": disk_usage.total / (1024**3),
                    "used_gb": disk_usage.used / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                },
                timestamp=datetime.now(),
            )

        except Exception as error:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar disco: {error}",
                details={"error": str(error)},
                timestamp=datetime.now(),
            )

    async def _check_network_connectivity(self) -> HealthCheck:
        """Verifica conectividade de rede"""
        try:
            # Teste básico de conectividade
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = datetime.now()
                response = await client.get("https://www.google.com")
                response_time = (datetime.now() - start_time).total_seconds()

                if response.status_code == 200:
                    status = HealthStatus.HEALTHY
                    message = f"Conectividade OK: {response_time:.2f}s"
                else:
                    status = HealthStatus.WARNING
                    message = f"Conectividade degradada: status {response.status_code}"

                return HealthCheck(
                    name="network_connectivity",
                    status=status,
                    message=message,
                    details={
                        "test_url": "https://www.google.com",
                        "status_code": response.status_code,
                        "response_time_seconds": response_time,
                    },
                    timestamp=datetime.now(),
                    response_time_ms=response_time * 1000,
                )

        except Exception as error:
            return HealthCheck(
                name="network_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Sem conectividade: {error}",
                details={"error": str(error)},
                timestamp=datetime.now(),
            )

    async def _check_log_files(self) -> HealthCheck:
        """Verifica arquivos de log"""
        try:
            from pathlib import Path

            log_dir = Path("./logs")

            if not log_dir.exists():
                return HealthCheck(
                    name="log_files",
                    status=HealthStatus.WARNING,
                    message="Diretório de logs não existe",
                    details={"log_dir": str(log_dir)},
                    timestamp=datetime.now(),
                )

            # Verificar logs recentes
            recent_logs = []
            one_day_ago = datetime.now() - timedelta(days=1)

            for log_file in log_dir.glob("*.log"):
                file_stat = log_file.stat()
                file_modified = datetime.fromtimestamp(file_stat.st_mtime)

                if file_modified > one_day_ago:
                    recent_logs.append(
                        {
                            "file": log_file.name,
                            "size_mb": file_stat.st_size / (1024 * 1024),
                            "modified": file_modified.isoformat(),
                        }
                    )

            if recent_logs:
                status = HealthStatus.HEALTHY
                message = f"Logs ativos: {len(recent_logs)} arquivos"
            else:
                status = HealthStatus.WARNING
                message = "Nenhum log recente encontrado"

            return HealthCheck(
                name="log_files",
                status=status,
                message=message,
                details={
                    "log_dir": str(log_dir),
                    "recent_logs_count": len(recent_logs),
                    "recent_logs": recent_logs[
                        :5
                    ],  # Limitar para não ficar muito grande
                },
                timestamp=datetime.now(),
            )

        except Exception as error:
            return HealthCheck(
                name="log_files",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar logs: {error}",
                details={"error": str(error)},
                timestamp=datetime.now(),
            )

    async def _check_configuration(self) -> HealthCheck:
        """Verifica configuração do sistema"""
        try:
            # Verificar configurações essenciais
            config_issues = []

            # Verificar API Key
            if not self.settings.api.scraper_api_key:
                config_issues.append("SCRAPER_API_KEY não configurada")
            elif len(self.settings.api.scraper_api_key) < 32:
                config_issues.append("SCRAPER_API_KEY muito curta")

            # Verificar URLs
            if not self.settings.api.base_url:
                config_issues.append("API_BASE_URL não configurada")

            if not self.settings.scraper.target_url:
                config_issues.append("SCRAPER_TARGET_URL não configurada")

            # Verificar timeouts
            if self.settings.browser.timeout < 5000:
                config_issues.append("Browser timeout muito baixo")

            if config_issues:
                status = HealthStatus.WARNING
                message = f"Problemas de configuração: {len(config_issues)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Configuração válida"

            return HealthCheck(
                name="configuration",
                status=status,
                message=message,
                details={
                    "issues": config_issues,
                    "api_configured": bool(self.settings.api.scraper_api_key),
                    "urls_configured": bool(
                        self.settings.api.base_url and self.settings.scraper.target_url
                    ),
                },
                timestamp=datetime.now(),
            )

        except Exception as error:
            return HealthCheck(
                name="configuration",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar configuração: {error}",
                details={"error": str(error)},
                timestamp=datetime.now(),
            )

    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calcula status geral baseado em todas as verificações"""
        if not checks:
            return HealthStatus.UNKNOWN

        # Se alguma verificação crítica falhou
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL

        # Se alguma verificação tem warning
        if any(check.status == HealthStatus.WARNING for check in checks):
            return HealthStatus.WARNING

        # Se todas são healthy
        if all(check.status == HealthStatus.HEALTHY for check in checks):
            return HealthStatus.HEALTHY

        # Caso tenha status unknown
        return HealthStatus.WARNING

    def get_health_summary(self) -> Dict[str, Any]:
        """Retorna resumo de saúde"""
        if not self.checks:
            return {
                "status": "no_checks_run",
                "message": "Nenhuma verificação executada",
            }

        overall_status = self._calculate_overall_status(self.checks)

        return {
            "overall_status": overall_status.value,
            "total_checks": len(self.checks),
            "healthy": len(
                [c for c in self.checks if c.status == HealthStatus.HEALTHY]
            ),
            "warning": len(
                [c for c in self.checks if c.status == HealthStatus.WARNING]
            ),
            "critical": len(
                [c for c in self.checks if c.status == HealthStatus.CRITICAL]
            ),
            "last_check": max(
                self.checks, key=lambda c: c.timestamp
            ).timestamp.isoformat()
            if self.checks
            else None,
        }
