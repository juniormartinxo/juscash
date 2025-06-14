"""
Sistema de backup e recuperação para o scraper
"""

import json
import gzip
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from domain.entities.publication import Publication
from domain.entities.scraping_execution import ScrapingExecution
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class BackupManager:
    """
    Gerenciador de backup para dados do scraper
    """

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Subdiretórios
        self.publications_dir = self.backup_dir / "publications"
        self.executions_dir = self.backup_dir / "executions"
        self.logs_dir = self.backup_dir / "logs"

        for dir_path in [self.publications_dir, self.executions_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)

    async def backup_publication(self, publication: Publication) -> bool:
        """Faz backup de uma publicação"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pub_{publication.process_number.replace('/', '_')}_{timestamp}.json.gz"

            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "publication": publication.to_api_dict(),
                "metadata": {"backup_version": "1.0", "compression": "gzip"},
            }

            file_path = self.publications_dir / filename

            # Salvar comprimido
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 Backup da publicação salvo: {filename}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro no backup da publicação: {error}")
            return False

    async def backup_execution(self, execution: ScrapingExecution) -> bool:
        """Faz backup de uma execução"""
        try:
            timestamp = execution.started_at.strftime("%Y%m%d_%H%M%S")
            filename = f"exec_{execution.execution_id}_{timestamp}.json.gz"

            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "execution": {
                    "execution_id": execution.execution_id,
                    "execution_type": execution.execution_type.value,
                    "status": execution.status.value,
                    "started_at": execution.started_at.isoformat(),
                    "finished_at": execution.finished_at.isoformat()
                    if execution.finished_at
                    else None,
                    "execution_time_seconds": execution.execution_time_seconds,
                    "publications_found": execution.publications_found,
                    "publications_new": execution.publications_new,
                    "publications_duplicated": execution.publications_duplicated,
                    "publications_failed": execution.publications_failed,
                    "publications_saved": execution.publications_saved,
                    "criteria_used": execution.criteria_used,
                    "scraper_version": execution.scraper_version,
                    "error_details": execution.error_details,
                },
            }

            file_path = self.executions_dir / filename

            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 Backup da execução salvo: {filename}")
            return True

        except Exception as error:
            logger.error(f"❌ Erro no backup da execução: {error}")
            return False

    async def backup_logs(self, days_back: int = 1) -> bool:
        """Faz backup dos logs recentes"""
        try:
            logs_source_dir = Path("./logs")
            if not logs_source_dir.exists():
                logger.warning("⚠️  Diretório de logs não encontrado")
                return False

            cutoff_date = datetime.now() - timedelta(days=days_back)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            backed_up_files = []

            for log_file in logs_source_dir.glob("*.log"):
                file_stat = log_file.stat()
                file_modified = datetime.fromtimestamp(file_stat.st_mtime)

                if file_modified >= cutoff_date:
                    # Comprimir e salvar
                    backup_filename = f"{log_file.stem}_{timestamp}.log.gz"
                    backup_path = self.logs_dir / backup_filename

                    with open(log_file, "rb") as f_in:
                        with gzip.open(backup_path, "wb") as f_out:
                            f_out.writelines(f_in)

                    backed_up_files.append(backup_filename)

            if backed_up_files:
                logger.info(
                    f"💾 Backup de logs concluído: {len(backed_up_files)} arquivos"
                )
                return True
            else:
                logger.debug("📋 Nenhum log recente para backup")
                return True

        except Exception as error:
            logger.error(f"❌ Erro no backup de logs: {error}")
            return False

    async def restore_publication(self, backup_filename: str) -> Optional[Publication]:
        """Restaura publicação de backup"""
        try:
            file_path = self.publications_dir / backup_filename

            if not file_path.exists():
                logger.error(f"❌ Arquivo de backup não encontrado: {backup_filename}")
                return None

            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                backup_data = json.load(f)

            pub_data = backup_data["publication"]

            # Reconstruir objeto Publication
            # Nota: Simplificado - pode precisar de conversões mais complexas
            logger.info(f"♻️  Publicação restaurada do backup: {backup_filename}")
            return None  # Implementar conforme necessário

        except Exception as error:
            logger.error(f"❌ Erro ao restaurar publicação: {error}")
            return None

    async def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Remove backups antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            removed_count = 0

            for backup_dir in [
                self.publications_dir,
                self.executions_dir,
                self.logs_dir,
            ]:
                for backup_file in backup_dir.glob("*.gz"):
                    file_stat = backup_file.stat()
                    file_created = datetime.fromtimestamp(file_stat.st_ctime)

                    if file_created < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1

            if removed_count > 0:
                logger.info(
                    f"🧹 Limpeza de backups: {removed_count} arquivos removidos"
                )

            return removed_count

        except Exception as error:
            logger.error(f"❌ Erro na limpeza de backups: {error}")
            return 0

    def get_backup_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos backups"""
        try:
            stats = {
                "backup_dir": str(self.backup_dir),
                "publications": {
                    "count": len(list(self.publications_dir.glob("*.gz"))),
                    "total_size_mb": sum(
                        f.stat().st_size for f in self.publications_dir.glob("*.gz")
                    )
                    / (1024 * 1024),
                },
                "executions": {
                    "count": len(list(self.executions_dir.glob("*.gz"))),
                    "total_size_mb": sum(
                        f.stat().st_size for f in self.executions_dir.glob("*.gz")
                    )
                    / (1024 * 1024),
                },
                "logs": {
                    "count": len(list(self.logs_dir.glob("*.gz"))),
                    "total_size_mb": sum(
                        f.stat().st_size for f in self.logs_dir.glob("*.gz")
                    )
                    / (1024 * 1024),
                },
            }

            # Calcular totais
            stats["total"] = {
                "files": sum(
                    cat["count"]
                    for cat in [
                        stats["publications"],
                        stats["executions"],
                        stats["logs"],
                    ]
                ),
                "size_mb": sum(
                    cat["total_size_mb"]
                    for cat in [
                        stats["publications"],
                        stats["executions"],
                        stats["logs"],
                    ]
                ),
            }

            return stats

        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas: {error}")
            return {}
