"""
Configurações específicas para salvamento de relatórios TXT
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ReportSettings:
    """
    Configurações para salvamento de relatórios TXT
    """

    # Diretório de saída
    output_directory: str = "./reports/txt"

    # Habilitar/desabilitar salvamento
    enabled: bool = True

    # Formato do nome do arquivo
    filename_format: str = "{process_number}.txt"

    # Incluir metadados no relatório
    include_metadata: bool = True

    # Incluir valores monetários
    include_monetary_values: bool = True

    # Incluir conteúdo completo da publicação
    include_full_content: bool = True

    # Dias para manter relatórios antigos
    cleanup_days: int = 30

    # Habilitar limpeza automática
    auto_cleanup: bool = True

    # Separador de seções no relatório
    section_separator: str = "-" * 40

    # Separador principal
    main_separator: str = "=" * 80

    # Encoding para os arquivos
    file_encoding: str = "utf-8"

    # Criar subdiretórios por data
    organize_by_date: bool = True

    # Formato de data para subdiretórios
    date_format: str = "%Y-%m-%d"


def get_report_settings() -> ReportSettings:
    """
    Obtém configurações de relatório a partir de variáveis de ambiente
    ou valores padrão

    Returns:
        Configurações de relatório
    """
    return ReportSettings(
        output_directory=os.getenv("REPORT_OUTPUT_DIR", "./reports/txt"),
        enabled=os.getenv("REPORT_ENABLED", "true").lower() == "true",
        filename_format=os.getenv("REPORT_FILENAME_FORMAT", "{process_number}.txt"),
        include_metadata=os.getenv("REPORT_INCLUDE_METADATA", "true").lower() == "true",
        include_monetary_values=os.getenv("REPORT_INCLUDE_VALUES", "true").lower()
        == "true",
        include_full_content=os.getenv("REPORT_INCLUDE_CONTENT", "true").lower()
        == "true",
        cleanup_days=int(os.getenv("REPORT_CLEANUP_DAYS", "30")),
        auto_cleanup=os.getenv("REPORT_AUTO_CLEANUP", "true").lower() == "true",
        file_encoding=os.getenv("REPORT_ENCODING", "utf-8"),
        organize_by_date=os.getenv("REPORT_ORGANIZE_BY_DATE", "true").lower() == "true",
        date_format=os.getenv("REPORT_DATE_FORMAT", "%Y-%m-%d"),
    )
