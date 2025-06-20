"""
Orquestrador principal do processo de scraping
"""

import subprocess
import asyncio
import sys
import os
from pathlib import Path
from typing import List
from datetime import datetime, timedelta
from uuid import uuid4

from application.usecases.extract_publications import ExtractPublicationsUseCase
from application.usecases.save_publications_to_files import (
    SavePublicationsToFilesUseCase,
)
from domain.entities.scraping_execution import ScrapingExecution, ExecutionType
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ScrapingOrchestrator:
    """
    Orquestra todo o processo de scraping diário
    Agora usa o scraping.py que funciona completamente
    """

    def __init__(self, container):
        self.container = container
        # Manter os use cases para compatibilidade, mas usar scraping.py como método principal
        self.extract_usecase = ExtractPublicationsUseCase(container.web_scraper)
        self.save_usecase = SavePublicationsToFilesUseCase()

    async def execute_daily_scraping(self) -> ScrapingExecution:
        """
        Executa o processo completo de scraping diário usando o scraping.py
        """
        execution = ScrapingExecution(
            execution_id=str(uuid4()),
            execution_type=ExecutionType.SCHEDULED,
            criteria_used={
                "search_terms": ["RPV", "pagamento pelo INSS"],
                "caderno": "3",
                "instancia": "1",
                "local": "Capital",
                "parte": "1",
                "method": "scraping_py_integration",
            },
        )

        try:
            logger.info(f"🚀 Iniciando execução diária {execution.execution_id}")

            # Usar scraping.py para fazer o scraping real
            result = await self._execute_scraping_py()

            if result["success"]:
                execution.publications_found = result.get("publications_found", 0)
                execution.publications_saved = result.get("publications_saved", 0)
                execution.publications_failed = result.get("publications_failed", 0)
                execution.publications_new = result.get("publications_saved", 0)
                execution.publications_duplicated = 0

                execution.mark_as_completed()
                logger.info(
                    f"✅ Execução {execution.execution_id} concluída com sucesso"
                )
                logger.info(
                    f"📤 {execution.publications_found} publicações encontradas"
                )
                logger.info(f"💾 {execution.publications_saved} publicações salvas")
            else:
                raise Exception(
                    f"Falha no scraping.py: {result.get('error', 'Erro desconhecido')}"
                )

        except Exception as error:
            logger.error(f"❌ Erro na execução {execution.execution_id}: {error}")
            execution.mark_as_failed(
                {"error": str(error), "type": type(error).__name__}
            )

        # Salvar informações da execução (logs locais)
        if hasattr(self.container, "scraping_repository"):
            await self.container.scraping_repository.save_scraping_execution(execution)

        return execution

    async def _execute_scraping_py(self) -> dict:
        """
        Executa o scraping.py para fazer o scraping real
        """
        try:
            # Data atual (para execução no mesmo dia)
            today = datetime.now()
            date_str = today.strftime("%Y-%m-%d")

            # Caminho para o scraping.py
            scraper_dir = Path(__file__).parent.parent.parent.parent
            scraping_py_path = scraper_dir / "scraping.py"

            if not scraping_py_path.exists():
                raise FileNotFoundError(
                    f"scraping.py não encontrado em: {scraping_py_path}"
                )

            logger.info(f"📅 Executando scraping para data: {date_str}")
            logger.info(f"📄 Usando script: {scraping_py_path}")

            # Comando para executar o scraping.py
            cmd = [
                sys.executable,  # python
                str(scraping_py_path),
                "run",
                "--start-date",
                date_str,
                "--end-date",
                date_str,
                "--headless",  # Sempre headless no agendamento
            ]

            logger.info(f"🔄 Executando comando: {' '.join(cmd)}")

            # Executar o comando
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(scraper_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(os.environ), "PYTHONPATH": str(scraper_dir)},
            )

            stdout, stderr = await process.communicate()

            # Logs do processo
            if stdout:
                stdout_text = stdout.decode("utf-8", errors="ignore")
                logger.info(f"📊 Output do scraping.py:\n{stdout_text}")

                # Extrair estatísticas do output
                stats = self._parse_scraping_output(stdout_text)
            else:
                stats = {
                    "publications_found": 0,
                    "publications_saved": 0,
                    "publications_failed": 0,
                }

            if stderr:
                stderr_text = stderr.decode("utf-8", errors="ignore")
                logger.warning(f"⚠️ Stderr do scraping.py:\n{stderr_text}")

            # Verificar código de saída
            if process.returncode == 0:
                logger.info("✅ scraping.py executado com sucesso")
                return {"success": True, **stats}
            else:
                error_msg = f"scraping.py falhou com código {process.returncode}"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as error:
            logger.error(f"❌ Erro ao executar scraping.py: {error}")
            return {"success": False, "error": str(error)}

    def _parse_scraping_output(self, output: str) -> dict:
        """
        Extrai estatísticas do output do scraping.py
        """
        import re

        stats = {
            "publications_found": 0,
            "publications_saved": 0,
            "publications_failed": 0,
        }

        try:
            # Buscar padrões no output
            # Exemplo: "📄 Publicações encontradas: 25"
            found_match = re.search(r"Publicações encontradas:\s*(\d+)", output)
            if found_match:
                stats["publications_found"] = int(found_match.group(1))

            # Exemplo: "✅ Publicações salvas: 20"
            saved_match = re.search(r"Publicações salvas:\s*(\d+)", output)
            if saved_match:
                stats["publications_saved"] = int(saved_match.group(1))

            # Exemplo: "❌ Falhas: 5"
            failed_match = re.search(r"Falhas:\s*(\d+)", output)
            if failed_match:
                stats["publications_failed"] = int(failed_match.group(1))

            logger.info(f"📊 Estatísticas extraídas: {stats}")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair estatísticas: {e}")

        return stats

    # Manter método original como fallback
    async def execute_daily_scraping_original(self) -> ScrapingExecution:
        """
        Método original usando DJEScraperAdapter (manter como fallback)
        """
        execution = ScrapingExecution(
            execution_id=str(uuid4()),
            execution_type=ExecutionType.SCHEDULED,
            criteria_used={
                "search_terms": ["RPV", "pagamento pelo INSS"],
                "caderno": "3",
                "instancia": "1",
                "local": "Capital",
                "parte": "1",
                "method": "original_adapter",
            },
        )

        try:
            logger.info(f"🚀 Iniciando execução original {execution.execution_id}")

            # Termos de busca obrigatórios
            search_terms = ["RPV", "pagamento pelo INSS"]

            # Extrair publicações
            publications = []
            async for publication in self.extract_usecase.execute(
                search_terms, max_pages=20
            ):
                publications.append(publication)
                execution.publications_found += 1

            # Salvar publicações em JSON
            if publications:
                save_stats = await self.save_usecase.execute(publications)
                execution.publications_new = save_stats["saved"]
                execution.publications_failed = save_stats["failed"]
                execution.publications_saved = save_stats["saved"]
                execution.publications_duplicated = 0

                # Log das estatísticas
                file_stats = self.save_usecase.get_file_stats()
                logger.info(f"📊 Estatísticas dos arquivos: {file_stats}")

            execution.mark_as_completed()
            logger.info(f"✅ Execução original {execution.execution_id} concluída")

        except Exception as error:
            logger.error(
                f"❌ Erro na execução original {execution.execution_id}: {error}"
            )
            execution.mark_as_failed(
                {"error": str(error), "type": type(error).__name__}
            )

        return execution
