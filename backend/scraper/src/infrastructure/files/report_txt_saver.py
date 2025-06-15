"""
Módulo para salvar relatórios extraídos como arquivos TXT
"""

import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from domain.entities.publication import Publication
from infrastructure.config.report_settings import get_report_settings
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ReportTxtSaver:
    """
    Classe responsável por salvar relatórios extraídos como arquivos TXT
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o salvador de relatórios

        Args:
            output_dir: Diretório onde os relatórios serão salvos (opcional)
        """
        # Carregar configurações
        self.settings = get_report_settings()

        # Usar diretório personalizado ou das configurações
        dir_path = output_dir or self.settings.output_directory
        self.output_dir = Path(dir_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Criar subdiretórios por data se configurado
        if self.settings.organize_by_date:
            today = datetime.now().strftime(self.settings.date_format)
            self.daily_dir = self.output_dir / today
            self.daily_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.daily_dir = self.output_dir

        logger.info(f"📁 Diretório de relatórios: {self.output_dir}")
        logger.info(f"📅 Relatórios do dia: {self.daily_dir}")
        logger.info(
            f"⚙️ Salvamento {'habilitado' if self.settings.enabled else 'desabilitado'}"
        )

    async def save_publication_report(self, publication: Publication) -> Optional[str]:
        """
        Salva uma publicação como arquivo TXT

        Args:
            publication: Publicação a ser salva

        Returns:
            Caminho do arquivo salvo ou None se houve erro
        """
        # Verificar se o salvamento está habilitado
        if not self.settings.enabled:
            logger.debug(f"🚫 Salvamento de relatórios desabilitado")
            return None

        try:
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]  # HH:MM:SS_mmm
            safe_process_number = publication.process_number.replace("/", "_").replace(
                ".", "_"
            )
            filename = f"relatorio_{safe_process_number}_{timestamp}.txt"
            file_path = self.daily_dir / filename

            # Gerar conteúdo do relatório
            report_content = await self._generate_report_content(publication)

            # Salvar arquivo
            async with asyncio.Lock():  # Evitar conflitos de escrita
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(report_content)

            logger.info(f"💾 Relatório salvo: {filename}")
            return str(file_path)

        except Exception as error:
            logger.error(
                f"❌ Erro ao salvar relatório para {publication.process_number}: {error}"
            )
            return None

    async def _generate_report_content(self, publication: Publication) -> str:
        """
        Gera o conteúdo do relatório em formato TXT

        Args:
            publication: Publicação para gerar o relatório

        Returns:
            Conteúdo do relatório formatado
        """
        try:
            # Cabeçalho
            report_lines = [
                "RELATÓRIO DE PUBLICAÇÃO EXTRAÍDA - DJE-SP",
                "=" * 80,
                f"Data de Extração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                f"Sistema: JusCash Scraper",
                "=" * 80,
                "",
            ]

            # Informações do processo
            report_lines.extend(
                [
                    "INFORMAÇÕES DO PROCESSO",
                    "-" * 40,
                    f"Número do Processo: {publication.process_number}",
                    f"Data de Publicação: {publication.publication_date.strftime('%d/%m/%Y') if publication.publication_date else 'Não informada'}",
                    f"Data de Disponibilização: {publication.availability_date.strftime('%d/%m/%Y %H:%M:%S')}",
                    "",
                ]
            )

            # Partes do processo
            report_lines.extend(
                ["PARTES DO PROCESSO", "-" * 40, f"Réu: {publication.defendant}", ""]
            )

            # Autores
            if publication.authors:
                report_lines.extend(
                    [
                        "AUTORES:",
                        *[f"  - {author}" for author in publication.authors],
                        "",
                    ]
                )

            # Advogados
            if publication.lawyers:
                report_lines.extend(
                    [
                        "ADVOGADOS:",
                        *[
                            f"  - {lawyer.name} (OAB: {lawyer.oab})"
                            for lawyer in publication.lawyers
                        ],
                        "",
                    ]
                )

            # Valores monetários
            values_section = ["VALORES MONETÁRIOS", "-" * 40]
            has_values = False

            if publication.gross_value:
                values_section.append(
                    f"Valor Bruto: R$ {publication.gross_value.to_real():.2f}"
                )
                has_values = True

            if publication.net_value:
                values_section.append(
                    f"Valor Líquido: R$ {publication.net_value.to_real():.2f}"
                )
                has_values = True

            if publication.interest_value:
                values_section.append(
                    f"Juros: R$ {publication.interest_value.to_real():.2f}"
                )
                has_values = True

            if publication.attorney_fees:
                values_section.append(
                    f"Honorários Advocatícios: R$ {publication.attorney_fees.to_real():.2f}"
                )
                has_values = True

            if has_values:
                report_lines.extend(values_section)
                report_lines.append("")
            else:
                report_lines.extend(
                    [
                        "VALORES MONETÁRIOS",
                        "-" * 40,
                        "Nenhum valor monetário identificado",
                        "",
                    ]
                )

            # Conteúdo da publicação
            report_lines.extend(
                [
                    "CONTEÚDO COMPLETO DA PUBLICAÇÃO",
                    "-" * 80,
                    (
                        publication.content
                        if publication.content
                        else "Conteúdo não disponível"
                    ),
                    "",
                    "-" * 80,
                    "",
                ]
            )

            # Metadados de extração
            if publication.extraction_metadata:
                report_lines.extend(
                    [
                        "METADADOS DE EXTRAÇÃO",
                        "-" * 40,
                    ]
                )

                for key, value in publication.extraction_metadata.items():
                    if key == "extraction_date":
                        try:
                            # Tentar converter para datetime e formatar
                            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                            formatted_value = dt.strftime("%d/%m/%Y %H:%M:%S")
                        except:
                            formatted_value = str(value)
                    else:
                        formatted_value = str(value)

                    report_lines.append(
                        f"{key.replace('_', ' ').title()}: {formatted_value}"
                    )

                report_lines.append("")

            # Informações do sistema
            report_lines.extend(
                [
                    "INFORMAÇÕES DO SISTEMA",
                    "-" * 40,
                    f"Status: {publication.status}",
                    f"Fonte de Scraping: {publication.scraping_source}",
                    f"Caderno: {publication.caderno}",
                    f"Instância: {publication.instancia}",
                    f"Local: {publication.local}",
                    f"Parte: {publication.parte}",
                    "",
                ]
            )

            # Rodapé
            report_lines.extend(
                [
                    "=" * 80,
                    f"Relatório gerado automaticamente pelo JusCash Scraper",
                    f"Arquivo: {datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "=" * 80,
                ]
            )

            return "\n".join(report_lines)

        except Exception as error:
            logger.error(f"❌ Erro ao gerar conteúdo do relatório: {error}")
            return f"ERRO: Não foi possível gerar o relatório para o processo {publication.process_number}\nErro: {error}"

    def get_daily_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos relatórios salvos hoje

        Returns:
            Estatísticas do dia
        """
        try:
            txt_files = list(self.daily_dir.glob("relatorio_*.txt"))

            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_reports": len(txt_files),
                "directory": str(self.daily_dir),
                "files": [f.name for f in txt_files[-10:]],  # Últimos 10 arquivos
            }
        except Exception as error:
            logger.error(f"❌ Erro ao obter estatísticas: {error}")
            return {"error": str(error)}

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """
        Remove relatórios antigos

        Args:
            days_to_keep: Número de dias para manter os relatórios
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            for date_dir in self.output_dir.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if dir_date < cutoff_date:
                            # Remove o diretório e todos os arquivos
                            import shutil

                            shutil.rmtree(date_dir)
                            logger.info(f"🗑️ Diretório removido: {date_dir.name}")
                    except ValueError:
                        # Não é um diretório de data válido, pular
                        continue

        except Exception as error:
            logger.error(f"❌ Erro na limpeza de relatórios antigos: {error}")
