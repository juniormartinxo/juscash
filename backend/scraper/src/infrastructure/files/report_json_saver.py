"""
Módulo para salvar publicações como arquivos JSON
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from domain.entities.publication import Publication
from infrastructure.config.report_settings import get_report_settings
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ReportJsonSaver:
    """
    Classe responsável por salvar publicações como arquivos JSON
    seguindo o modelo Publication do Prisma
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o salvador de relatórios JSON

        Args:
            output_dir: Diretório onde os arquivos JSON serão salvos (opcional)
        """
        # Carregar configurações
        self.settings = get_report_settings()

        # Usar diretório personalizado ou das configurações
        dir_path = output_dir or self.settings.output_directory
        self.output_dir = Path(dir_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Criar subdiretório para JSONs
        self.json_dir = Path("/app/reports/json")  # Path absoluto
        self.json_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 Diretório de JSONs: {self.output_dir}")

        # Não criar subdiretórios por data
        self.daily_json_dir = self.json_dir

        logger.info(f"📁 Diretório de JSONs: {self.json_dir}")

    async def save_publication_json(self, publication: Publication) -> Optional[str]:
        """
        Salva uma publicação como arquivo JSON

        Args:
            publication: Publicação a ser salva

        Returns:
            Caminho do arquivo salvo ou None se houve erro
        """
        try:
            # Gerar nome do arquivo usando o número do processo
            safe_process_number = publication.process_number.replace("/", "_").replace(
                ".", "_"
            )
            filename = f"{safe_process_number}.json"
            file_path = self.daily_json_dir / filename

            # Converter publicação para formato JSON compatível com o modelo Prisma
            json_data = self._publication_to_prisma_json(publication)

            # Salvar arquivo JSON
            async with asyncio.Lock():  # Evitar conflitos de escrita
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 JSON salvo: {filename}")
            return str(file_path)

        except Exception as error:
            logger.error(
                f"❌ Erro ao salvar JSON para {publication.process_number}: {error}"
            )
            return None

    def _publication_to_prisma_json(self, publication: Publication) -> Dict[str, Any]:
        """
        Converte uma publicação para o formato JSON compatível com o modelo Prisma

        Args:
            publication: Publicação para converter

        Returns:
            Dicionário com os dados no formato do modelo Prisma
        """
        # Formatar datas para ISO 8601 (YYYY-MM-DD)
        def format_date(dt: Optional[datetime]) -> Optional[str]:
            if dt:
                return dt.date().isoformat()
            return None

        # Converter advogados para formato JSON
        lawyers_json = None
        if publication.lawyers:
            lawyers_json = [
                {"name": lawyer.name, "oab": lawyer.oab} 
                for lawyer in publication.lawyers
            ]

        # Criar o objeto JSON seguindo o modelo Prisma
        json_data = {
            "process_number": publication.process_number,
            "publication_date": (
                format_date(publication.publication_date)
                if publication.publication_date
                else ""
            ),
            "availability_date": (
                format_date(publication.availability_date)
                if publication.availability_date
                else ""
            ),
            "authors": publication.authors if publication.authors else [],
            "defendant": (
                publication.defendant
                if publication.defendant
                else "Instituto Nacional do Seguro Social - INSS"
            ),
            "lawyers": lawyers_json if lawyers_json else [],
            "gross_value": (
                publication.gross_value.amount_cents if publication.gross_value else 0
            ),
            "net_value": (
                publication.net_value.amount_cents if publication.net_value else 0
            ),
            "interest_value": (
                publication.interest_value.amount_cents
                if publication.interest_value
                else 0
            ),
            "attorney_fees": (
                publication.attorney_fees.amount_cents
                if publication.attorney_fees
                else 0
            ),
            "content": publication.content,
            "status": publication.status if publication.status else "NOVA",
            "scraping_source": (
                publication.scraping_source if publication.scraping_source else "DJE-SP"
            ),
            "caderno": publication.caderno if publication.caderno else "3",
            "instancia": publication.instancia if publication.instancia else "1",
            "local": publication.local if publication.local else "Capital",
            "parte": publication.parte if publication.parte else "1",
            "extraction_metadata": (
                publication.extraction_metadata
                if publication.extraction_metadata
                else None
            ),
            "scraping_execution_id": None,  # Será None pois não estamos mais usando o banco
        }

        return json_data

    def get_json_stats(self) -> Dict[str, int]:
        """
        Obtém estatísticas dos arquivos JSON salvos

        Returns:
            Dicionário com estatísticas
        """
        try:
            json_files = list(self.daily_json_dir.glob("*.json"))
            return {
                "total_json_files": len(json_files),
                "directory": str(self.daily_json_dir)
            }
        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas de JSON: {error}")
            return {"total_json_files": 0, "directory": str(self.daily_json_dir)}
