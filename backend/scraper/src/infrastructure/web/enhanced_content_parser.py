"""
Parser Aprimorado para Relatórios DJE-SP
Segue instruções específicas para extração de autores baseada em padrões RPV/INSS
"""

import re
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger
from infrastructure.web.content_parser import DJEContentParser

logger = setup_logger(__name__)


class EnhancedDJEContentParser(DJEContentParser):
    """
    Parser aprimorado que segue instruções específicas para extração de autores
    baseada nos padrões "RPV" e "pagamento pelo INSS"
    """

    def __init__(self):
        super().__init__()
        self.scraper_adapter = None  # Será injetado para download de páginas anteriores

    def set_scraper_adapter(self, scraper_adapter):
        """Injeta o scraper adapter para download de páginas anteriores"""
        self.scraper_adapter = scraper_adapter

    async def parse_multiple_publications_enhanced(
        self, content: str, source_url: str = "", current_page_number: int = None
    ) -> List[Publication]:
        """
        Extrai múltiplas publicações seguindo as instruções específicas:
        1. Busca por "RPV" ou "pagamento pelo INSS"
        2. Localiza início do processo com "Processo NUMERO_DO_PROCESSO"
        3. Extrai autores no formato "- NOME_DO_AUTOR - Vistos"
        4. Baixa página anterior se necessário
        """
        logger.info("🔍 Iniciando extração aprimorada de autores")
        publications = []

        try:
            # Passo 1: Buscar por "RPV" ou "pagamento pelo INSS"
            rpv_inss_matches = self._find_rpv_inss_occurrences(content)

            if not rpv_inss_matches:
                logger.info(
                    "❌ Nenhuma ocorrência de 'RPV' ou 'pagamento pelo INSS' encontrada"
                )
                return []

            logger.info(
                f"✅ Encontradas {len(rpv_inss_matches)} ocorrências de RPV/INSS"
            )

            # Passo 2-6: Para cada ocorrência, extrair processo e autores
            for match_info in rpv_inss_matches:
                publication = await self._extract_publication_from_match(
                    content, match_info, source_url, current_page_number
                )
                if publication:
                    publications.append(publication)

            logger.info(
                f"✅ Extraídas {len(publications)} publicações com padrão aprimorado"
            )
            return publications

        except Exception as error:
            logger.error(f"❌ Erro na extração aprimorada: {error}")
            return []

    def _find_rpv_inss_occurrences(self, content: str) -> List[Dict[str, Any]]:
        """
        Passo 1: Busca por "RPV" ou "pagamento pelo INSS" no relatório
        """
        matches = []

        # Padrões para buscar RPV e pagamento pelo INSS
        rpv_pattern = re.compile(r"\bRPV\b", re.IGNORECASE)
        inss_payment_pattern = re.compile(r"pagamento\s+pelo\s+INSS", re.IGNORECASE)

        # Buscar todas as ocorrências de RPV
        for match in rpv_pattern.finditer(content):
            matches.append(
                {
                    "type": "RPV",
                    "position": match.start(),
                    "text": match.group(),
                    "context": content[max(0, match.start() - 100) : match.end() + 100],
                }
            )

        # Buscar todas as ocorrências de "pagamento pelo INSS"
        for match in inss_payment_pattern.finditer(content):
            matches.append(
                {
                    "type": "pagamento pelo INSS",
                    "position": match.start(),
                    "text": match.group(),
                    "context": content[max(0, match.start() - 100) : match.end() + 100],
                }
            )

        # Ordenar por posição no documento
        matches.sort(key=lambda x: x["position"])

        logger.info(f"🔍 Encontradas {len(matches)} ocorrências de RPV/INSS")
        for i, match in enumerate(matches):
            logger.debug(f"   {i+1}. {match['type']} na posição {match['position']}")

        return matches

    async def _extract_publication_from_match(
        self,
        content: str,
        match_info: Dict[str, Any],
        source_url: str,
        current_page_number: int,
    ) -> Optional[Publication]:
        """
        Passos 2-6: Extrai publicação completa a partir de uma ocorrência RPV/INSS
        """
        try:
            match_position = match_info["position"]

            # Passo 2: Localizar início do processo "Processo NUMERO_DO_PROCESSO"
            process_start_info = self._find_process_start(content, match_position)

            if not process_start_info:
                logger.warning(
                    f"⚠️ Não foi possível localizar início do processo para {match_info['type']}"
                )

                # Passo 4: Se não encontrou, tentar baixar página anterior
                if current_page_number and self.scraper_adapter:
                    logger.info("🔄 Tentando baixar página anterior...")
                    previous_content = await self._download_previous_page(
                        current_page_number
                    )
                    if previous_content:
                        # Buscar processo na página anterior
                        process_start_info = self._find_process_start_in_previous(
                            previous_content, content, match_position
                        )

                if not process_start_info:
                    return None

            # Passo 3: Determinar fim do processo
            process_end_position = self._find_process_end(
                content, process_start_info["end_position"]
            )

            # Extrair conteúdo completo do processo
            if process_start_info.get("from_previous"):
                # Processo começou na página anterior
                process_content = (
                    process_start_info["previous_content"]
                    + content[:process_end_position]
                )
            else:
                # Processo está na página atual
                process_content = content[
                    process_start_info["start_position"] : process_end_position
                ]

            # Passo 5-6: Extrair autores no formato "- NOME_DO_AUTOR - Vistos"
            authors = self._extract_authors_enhanced_pattern(process_content)

            if not authors:
                logger.warning(
                    f"⚠️ Nenhum autor encontrado no padrão '- NOME - Vistos' para processo {process_start_info.get('process_number', 'desconhecido')}"
                )
                return None

            # Extrair outros dados do processo
            process_number = process_start_info.get("process_number")
            if not process_number:
                process_number = self._extract_process_number(process_content)

            if not process_number:
                logger.warning("⚠️ Número do processo não encontrado")
                return None

            # Extrair dados complementares
            publication_date = self._extract_publication_date(process_content)
            availability_date = (
                self._extract_availabilityDate(process_content) or datetime.now()
            )
            lawyers = self._extract_lawyers(process_content)
            monetary_values = self._extract_all_monetary_values(process_content)

            # Criar publicação
            publication = Publication(
                process_number=process_number,
                publication_date=publication_date,
                availability_date=availability_date,
                authors=authors,
                lawyers=lawyers,
                gross_value=monetary_values.get("gross"),
                net_value=monetary_values.get("net"),
                interest_value=monetary_values.get("interest"),
                attorney_fees=monetary_values.get("fees"),
                content=process_content,
                extraction_metadata={
                    "extraction_date": datetime.now().isoformat(),
                    "source_url": source_url,
                    "extraction_method": "enhanced_rpv_inss_pattern",
                    "match_type": match_info["type"],
                    "match_position": match_position,
                    "process_spans_pages": process_start_info.get(
                        "from_previous", False
                    ),
                    "text_length": len(process_content),
                },
            )

            logger.info(
                f"✅ Publicação extraída: {process_number} - Autores: {', '.join(authors)}"
            )
            return publication

        except Exception as error:
            logger.error(f"❌ Erro ao extrair publicação: {error}")
            return None

    def _find_process_start(
        self, content: str, match_position: int
    ) -> Optional[Dict[str, Any]]:
        """
        Passo 2: Localiza início do processo "Processo NUMERO_DO_PROCESSO"
        Busca para trás a partir da posição da ocorrência RPV/INSS
        """
        # Padrão para "Processo NUMERO_DO_PROCESSO"
        process_pattern = re.compile(
            r"Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", re.IGNORECASE
        )

        # Buscar para trás a partir da posição da ocorrência
        search_start = max(0, match_position - 5000)  # Buscar até 5000 chars para trás
        search_content = content[
            search_start : match_position + 1000
        ]  # Incluir um pouco à frente

        # Encontrar todas as ocorrências de processo na área de busca
        process_matches = list(process_pattern.finditer(search_content))

        if not process_matches:
            logger.debug(
                "🔍 Nenhum 'Processo NUMERO' encontrado antes da ocorrência RPV/INSS"
            )
            return None

        # Pegar o último processo antes da ocorrência (mais próximo)
        last_process = process_matches[-1]
        process_number = last_process.group(1)

        # Calcular posições absolutas
        absolute_start = search_start + last_process.start()
        absolute_end = search_start + last_process.end()

        logger.debug(
            f"✅ Processo encontrado: {process_number} na posição {absolute_start}"
        )

        return {
            "process_number": process_number,
            "start_position": absolute_start,
            "end_position": absolute_end,
            "from_previous": False,
        }

    def _find_process_end(self, content: str, start_position: int) -> int:
        """
        Passo 3: Determina fim do processo (próximo "Processo NUMERO" ou fim do documento)
        """
        # Buscar próximo processo a partir da posição atual
        process_pattern = re.compile(
            r"Processo\s+\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", re.IGNORECASE
        )

        search_content = content[start_position + 50 :]  # Pular o processo atual
        next_process = process_pattern.search(search_content)

        if next_process:
            end_position = start_position + 50 + next_process.start()
            logger.debug(
                f"✅ Fim do processo na posição {end_position} (próximo processo)"
            )
        else:
            end_position = len(content)
            logger.debug(
                f"✅ Fim do processo no final do documento (posição {end_position})"
            )

        return end_position

    async def _download_previous_page(self, current_page_number: int) -> Optional[str]:
        """
        Passo 4: Baixa página anterior (nuSeqpagina - 1) se necessário
        """
        if not self.scraper_adapter or current_page_number <= 1:
            return None

        try:
            logger.info(f"📥 Baixando página anterior: {current_page_number - 1}")

            # Construir URL da página anterior
            # Assumindo que a URL atual tem nuSeqpagina=X, mudamos para X-1
            previous_page_number = current_page_number - 1

            # Aqui você precisaria implementar a lógica específica para baixar
            # a página anterior baseada no padrão de URL do DJE-SP
            # Por enquanto, retorno None para indicar que não foi implementado

            logger.warning("⚠️ Download de página anterior não implementado ainda")
            return None

        except Exception as error:
            logger.error(f"❌ Erro ao baixar página anterior: {error}")
            return None

    def _find_process_start_in_previous(
        self, previous_content: str, current_content: str, match_position: int
    ) -> Optional[Dict[str, Any]]:
        """
        Busca início do processo na página anterior quando não encontrado na atual
        """
        # Implementar lógica para encontrar processo que começou na página anterior
        # e continua na página atual

        logger.warning("⚠️ Busca em página anterior não implementada ainda")
        return None

    def _extract_authors_enhanced_pattern(self, process_content: str) -> List[str]:
        """
        Passo 5-6: Extrai autores no formato "- NOME_DO_AUTOR - Vistos"
        """
        authors = []

        # Padrão específico: "- NOME_DO_AUTOR - Vistos"
        author_pattern = re.compile(
            r"-\s+([^-]+?)\s+-\s+Vistos", re.IGNORECASE | re.MULTILINE
        )

        matches = author_pattern.findall(process_content)

        for match in matches:
            author_name = self._clean_author_name(match)
            if (
                author_name and len(author_name) > 2
            ):  # Nome deve ter pelo menos 3 caracteres
                authors.append(author_name)
                logger.debug(f"✅ Autor extraído: '{author_name}'")

        # Remover duplicatas mantendo ordem
        unique_authors = []
        for author in authors:
            if author not in unique_authors:
                unique_authors.append(author)

        logger.info(
            f"✅ Extraídos {len(unique_authors)} autores únicos no padrão '- NOME - Vistos'"
        )

        return unique_authors

    def _clean_author_name(self, name: str) -> str:
        """
        Limpa e normaliza nome do autor
        """
        if not name:
            return ""

        # Remover espaços extras
        name = re.sub(r"\s+", " ", name.strip())

        # Remover caracteres especiais no início/fim
        name = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", name)

        # Converter para formato título (primeira letra maiúscula)
        name = name.title()

        # Filtrar nomes muito curtos ou inválidos
        if len(name) < 3:
            return ""

        # Filtrar palavras que não são nomes
        invalid_words = [
            "vistos",
            "processo",
            "inss",
            "instituto",
            "nacional",
            "seguro",
            "social",
        ]
        if name.lower() in invalid_words:
            return ""

        return name


# Função para alertar sobre edge cases
def alert_edge_case(message: str):
    """
    Alerta sobre edge cases ou dificuldades na extração
    """
    logger.warning(f"🚨 EDGE CASE DETECTADO: {message}")
    print(f"🚨 EDGE CASE: {message}")
