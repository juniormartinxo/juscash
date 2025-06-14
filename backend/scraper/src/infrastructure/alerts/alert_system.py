"""
Sistema de alertas e notificações para o scraper
"""

import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class AlertLevel(Enum):
    """Níveis de alerta"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Tipos de alerta"""

    SCRAPING_FAILED = "scraping_failed"
    API_CONNECTION_ERROR = "api_connection_error"
    LOW_SUCCESS_RATE = "low_success_rate"
    HIGH_ERROR_RATE = "high_error_rate"
    SYSTEM_PERFORMANCE = "system_performance"
    CONFIG_CHANGED = "config_changed"
    BACKUP_FAILED = "backup_failed"


@dataclass
class Alert:
    """Representação de um alerta"""

    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertSystem:
    """
    Sistema de alertas e notificações
    """

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertType, List[Callable]] = {}
        self.email_config: Optional[Dict[str, str]] = None
        self.alert_rules: Dict[str, Any] = self._setup_default_rules()

    def _setup_default_rules(self) -> Dict[str, Any]:
        """Configura regras padrão de alerta"""
        return {
            "max_errors_per_hour": 10,
            "min_success_rate_percent": 70,
            "max_response_time_seconds": 60,
            "max_memory_usage_mb": 1024,
            "max_cpu_usage_percent": 80,
            "alert_cooldown_minutes": 15,  # Evitar spam de alertas
        }

    def configure_email(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
    ) -> None:
        """Configura envio de email para alertas"""
        self.email_config = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "to_emails": to_emails,
        }
        logger.info("📧 Configuração de email para alertas ativada")

    def add_alert_handler(
        self, alert_type: AlertType, handler: Callable[[Alert], None]
    ) -> None:
        """Adiciona handler customizado para tipo de alerta"""
        if alert_type not in self.alert_handlers:
            self.alert_handlers[alert_type] = []

        self.alert_handlers[alert_type].append(handler)
        logger.debug(f"🔔 Handler adicionado para {alert_type.value}")

    async def create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        details: Dict[str, Any] = None,
    ) -> Alert:
        """Cria e processa novo alerta"""

        alert_id = f"{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = Alert(
            id=alert_id,
            type=alert_type,
            level=level,
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
        )

        # Verificar cooldown para evitar spam
        if self._should_suppress_alert(alert):
            logger.debug(f"🔇 Alerta suprimido por cooldown: {alert.id}")
            return alert

        self.alerts.append(alert)

        # Log do alerta
        level_icon = {
            AlertLevel.INFO: "ℹ️ ",
            AlertLevel.WARNING: "⚠️ ",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨",
        }

        logger_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }

        logger_func[level](f"{level_icon[level]} ALERTA: {title} - {message}")

        # Processar alerta
        await self._process_alert(alert)

        return alert

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Verifica se alerta deve ser suprimido por cooldown"""
        cooldown_minutes = self.alert_rules["alert_cooldown_minutes"]
        cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)

        # Verificar alertas recentes do mesmo tipo
        recent_alerts = [
            a for a in self.alerts if a.type == alert.type and a.timestamp > cutoff_time
        ]

        return len(recent_alerts) > 0

    async def _process_alert(self, alert: Alert) -> None:
        """Processa alerta através dos handlers"""

        # Handlers customizados
        if alert.type in self.alert_handlers:
            for handler in self.alert_handlers[alert.type]:
                try:
                    handler(alert)
                except Exception as error:
                    logger.error(f"❌ Erro em handler de alerta: {error}")

        # Handler de email
        if self.email_config and alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            await self._send_email_alert(alert)

    async def _send_email_alert(self, alert: Alert) -> bool:
        """Envia alerta por email"""
        if not self.email_config:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])
            msg["Subject"] = f"[DJE Scraper] {alert.level.value.upper()}: {alert.title}"

            # Corpo do email
            body = f"""
            Alerta do DJE Scraper
            
            Tipo: {alert.type.value}
            Nível: {alert.level.value.upper()}
            Timestamp: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
            
            Título: {alert.title}
            Mensagem: {alert.message}
            
            Detalhes:
            {self._format_alert_details(alert.details)}
            
            ---
            Sistema de Monitoramento DJE Scraper
            """

            msg.attach(MIMEText(body, "plain"))

            # Enviar email
            with smtplib.SMTP(
                self.email_config["smtp_host"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["username"], self.email_config["password"]
                )
                server.send_message(msg)

            logger.info(f"📧 Email de alerta enviado: {alert.id}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro ao enviar email de alerta: {error}")
            return False

    def _format_alert_details(self, details: Dict[str, Any]) -> str:
        """Formata detalhes do alerta para exibição"""
        if not details:
            return "Nenhum detalhe adicional"

        formatted = []
        for key, value in details.items():
            formatted.append(f"  {key}: {value}")

        return "\n".join(formatted)

    def resolve_alert(self, alert_id: str) -> bool:
        """Marca alerta como resolvido"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"✅ Alerta resolvido: {alert_id}")
                return True

        return False

    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos (não resolvidos)"""
        return [alert for alert in self.alerts if not alert.resolved]

    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Retorna alertas por tipo"""
        return [alert for alert in self.alerts if alert.type == alert_type]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Retorna alertas por nível"""
        return [alert for alert in self.alerts if alert.level == level]

    def get_alert_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Retorna estatísticas de alertas"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]

        stats = {
            "total_alerts": len(recent_alerts),
            "active_alerts": len([a for a in recent_alerts if not a.resolved]),
            "by_level": {},
            "by_type": {},
            "resolution_rate": 0,
        }

        # Por nível
        for level in AlertLevel:
            count = len([a for a in recent_alerts if a.level == level])
            stats["by_level"][level.value] = count

        # Por tipo
        for alert_type in AlertType:
            count = len([a for a in recent_alerts if a.type == alert_type])
            stats["by_type"][alert_type.value] = count

        # Taxa de resolução
        total_count = len(recent_alerts)
        resolved_count = len([a for a in recent_alerts if a.resolved])

        if total_count > 0:
            stats["resolution_rate"] = (resolved_count / total_count) * 100

        return stats

    def cleanup_old_alerts(self, retention_days: int = 30) -> int:
        """Remove alertas antigos"""
        cutoff_time = datetime.now() - timedelta(days=retention_days)

        old_alerts = [a for a in self.alerts if a.timestamp < cutoff_time]
        self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]

        removed_count = len(old_alerts)
        if removed_count > 0:
            logger.info(f"🧹 Alertas antigos removidos: {removed_count}")

        return removed_count


# Instância global do sistema de alertas
alert_system = AlertSystem()


# Funções de conveniência
async def alert_scraping_failed(error_message: str, details: Dict[str, Any] = None):
    """Alerta para falha no scraping"""
    await alert_system.create_alert(
        AlertType.SCRAPING_FAILED,
        AlertLevel.ERROR,
        "Falha no Scraping",
        f"O processo de scraping falhou: {error_message}",
        details,
    )


async def alert_api_connection_error(api_url: str, error_message: str):
    """Alerta para erro de conexão com API"""
    await alert_system.create_alert(
        AlertType.API_CONNECTION_ERROR,
        AlertLevel.ERROR,
        "Erro de Conexão com API",
        f"Falha ao conectar com a API {api_url}: {error_message}",
        {"api_url": api_url, "error": error_message},
    )


async def alert_low_success_rate(success_rate: float, threshold: float):
    """Alerta para baixa taxa de sucesso"""
    await alert_system.create_alert(
        AlertType.LOW_SUCCESS_RATE,
        AlertLevel.WARNING,
        "Taxa de Sucesso Baixa",
        f"Taxa de sucesso atual ({success_rate:.1f}%) está abaixo do limite ({threshold:.1f}%)",
        {"success_rate": success_rate, "threshold": threshold},
    )


async def alert_high_performance_usage(
    metric: str, current_value: float, threshold: float
):
    """Alerta para alto uso de recursos"""
    await alert_system.create_alert(
        AlertType.SYSTEM_PERFORMANCE,
        AlertLevel.WARNING,
        "Alto Uso de Recursos",
        f"{metric} está em {current_value:.1f}%, acima do limite de {threshold:.1f}%",
        {"metric": metric, "current_value": current_value, "threshold": threshold},
    )
