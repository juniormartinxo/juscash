"""
🚀 ENHANCED DJE PARSER INTEGRADO - FASE 3

Parser aprimorado que integra:
1. Page Manager (Fase 2) - Para publicações divididas entre páginas
2. Content Merger (Fase 2) - Para merge inteligente de conteúdo
3. Enhanced patterns - Das melhorias propostas
4. Validação robusta - Score de qualidade e logging detalhado

Fluxo de extração:
1. Busca termos RPV/INSS no conteúdo
2. Localiza processo correspondente (com busca para trás)
3. Se necessário, baixa página anterior e faz merge
4. Extrai dados estruturados com validação
5. Aplica score de qualidade e filtros
"""

import re
import unicodedata
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger
from infrastructure.web.page_manager import DJEPageManager, PublicationContentMerger

logger = setup_logger(__name__)


class EnhancedDJEParserIntegrated:
    """
    Parser DJE integrado com Page Manager e melhorias avançadas

    Features:
    - Integração completa com Page Manager
    - Merge automático de publicações divididas
    - Padrões regex aprimorados
    - Validação de qualidade com scoring
    - Logging detalhado para troubleshooting
    - Performance monitoring
    """

    # Padrões regex compilados otimizados
    PROCESS_PATTERN = re.compile(
        r"Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", re.IGNORECASE
    )

    # Padrões RPV/INSS aprimorados e específicos
    RPV_PATTERNS = [
        re.compile(r"\bRPV\b", re.IGNORECASE),
        re.compile(r"requisição\s+de\s+pequeno\s+valor", re.IGNORECASE),
        re.compile(r"pagamento\s+pelo\s+INSS", re.IGNORECASE),
        re.compile(r"pagamento\s+de\s+benefício", re.IGNORECASE),
        re.compile(r"expedição\s+de\s+RPV", re.IGNORECASE),
        re.compile(r"INSS.*?pagar", re.IGNORECASE),
        re.compile(r"benefício\s+previdenciário", re.IGNORECASE),
    ]

    # Padrão aprimorado para autores "- NOME - Vistos"
    AUTHOR_PATTERN = re.compile(
        r"-\s+([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.]{2,80}?)\s+-\s+(?:Vistos|Visto)",
        re.IGNORECASE | re.MULTILINE,
    )

    # Padrões para advogados aprimorados
    LAWYER_PATTERNS = [
        re.compile(
            r"ADV\.\s+([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.]{2,60}?)\s*\(\s*OAB\s+(\d+)(?:/\w+)?\)",
            re.IGNORECASE,
        ),
        re.compile(
            r"ADVOGAD[OA]\s+([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.]{2,60}?)\s*\(\s*OAB\s+(\d+)(?:/\w+)?\)",
            re.IGNORECASE,
        ),
        re.compile(
            r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.]{2,60}?)\s*\(\s*OAB\s+(\d+)(?:/\w+)?\)",
            re.IGNORECASE,
        ),
    ]

    # Padrões monetários específicos para RPV/INSS
    MONETARY_PATTERNS = {
        "gross_value": [
            re.compile(
                r"valor\s+(?:principal|bruto|total|devido|da\s+RPV)[:\s]*R\$?\s*([\d.,]+)",
                re.IGNORECASE,
            ),
            re.compile(r"principal[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(
                r"(?:quantia|importância)\s+de\s+R\$?\s*([\d.,]+)", re.IGNORECASE
            ),
            re.compile(r"valor\s+de\s+R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "net_value": [
            re.compile(r"valor\s+líquido[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"líquido[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"a\s+ser\s+pago[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "interest": [
            re.compile(r"juros\s+moratórios[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"correção\s+monetária[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"atualização[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "fees": [
            re.compile(
                r"honorários\s+advocatícios[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE
            ),
            re.compile(r"honorários[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
    }

    def __init__(self):
        self.scraper_adapter = None
        self.page_manager = None
        self.content_merger = None

        # Configurações de qualidade
        self.quality_threshold = 0.7
        self.max_process_search_distance = 3000  # chars

        # Estatísticas
        self.stats = {
            "total_rpv_found": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "merged_publications": 0,
            "cache_hits": 0,
            "quality_rejections": 0,
        }

        logger.info("🚀 Enhanced DJE Parser Integrado inicializado")

    def set_scraper_adapter(self, scraper_adapter):
        """
        Configura adapter do scraper e inicializa managers auxiliares
        """
        self.scraper_adapter = scraper_adapter
        self.page_manager = DJEPageManager(scraper_adapter)
        self.content_merger = PublicationContentMerger()

        logger.info(
            "🔗 Scraper adapter configurado - Page Manager e Content Merger ativos"
        )

    async def parse_multiple_publications_enhanced(
        self,
        content: str,
        source_url: str = "",
        current_page_number: Optional[int] = None,
    ) -> List[Publication]:
        """
        Método principal de extração integrada

        Args:
            content: Conteúdo HTML/texto da página
            source_url: URL da página atual
            current_page_number: Número da página atual (para Page Manager)

        Returns:
            Lista de publicações extraídas e validadas
        """
        logger.info("🔍 === INICIANDO EXTRAÇÃO INTEGRADA ===")
        logger.info(f"📄 Página: {current_page_number or 'desconhecida'}")
        logger.info(
            f"🔗 URL: {source_url[:100]}..." if source_url else "🔗 URL: não informada"
        )

        publications = []

        try:
            # Pré-processamento do conteúdo
            normalized_content = self._normalize_text(content)
            logger.info(f"📏 Conteúdo normalizado: {len(normalized_content)} chars")

            # 1. Buscar todas as ocorrências de RPV/INSS
            rpv_occurrences = self._find_all_rpv_occurrences(normalized_content)
            self.stats["total_rpv_found"] = len(rpv_occurrences)

            if not rpv_occurrences:
                logger.info("❌ Nenhuma ocorrência de RPV/INSS encontrada")
                return publications

            logger.info(
                f"✅ Encontradas {len(rpv_occurrences)} ocorrências de RPV/INSS"
            )

            # 2. Processar cada ocorrência
            for i, rpv_occurrence in enumerate(rpv_occurrences):
                logger.info(
                    f"\n📋 === PROCESSANDO OCORRÊNCIA {i + 1}/{len(rpv_occurrences)} ==="
                )
                logger.info(
                    f"🎯 Termo: '{rpv_occurrence['term']}' na posição {rpv_occurrence['position']}"
                )

                try:
                    publication = await self._extract_publication_for_occurrence(
                        normalized_content,
                        rpv_occurrence,
                        source_url,
                        current_page_number,
                    )

                    if publication:
                        publications.append(publication)
                        self.stats["successful_extractions"] += 1
                        logger.info(
                            f"✅ Publicação extraída: {publication.process_number}"
                        )
                    else:
                        self.stats["failed_extractions"] += 1
                        logger.warning(f"⚠️ Falha na extração da ocorrência {i + 1}")

                except Exception as e:
                    self.stats["failed_extractions"] += 1
                    logger.error(f"❌ Erro ao processar ocorrência {i + 1}: {e}")
                    continue

            # 3. Log de estatísticas finais
            self._log_extraction_stats()

            logger.info(f"🎉 === EXTRAÇÃO CONCLUÍDA ===")
            logger.info(f"📊 Total extraído: {len(publications)} publicações")

            return publications

        except Exception as e:
            logger.error(f"❌ Erro crítico na extração integrada: {e}")
            return publications

    def _find_all_rpv_occurrences(self, content: str) -> List[Dict[str, Any]]:
        """
        Encontra todas as ocorrências de termos RPV/INSS no conteúdo
        """
        occurrences = []

        for pattern in self.RPV_PATTERNS:
            for match in pattern.finditer(content):
                occurrences.append(
                    {
                        "term": match.group(0),
                        "position": match.start(),
                        "end_position": match.end(),
                        "pattern": pattern.pattern,
                        "context": content[
                            max(0, match.start() - 100) : match.end() + 100
                        ],
                    }
                )

        # Ordenar por posição e remover duplicatas próximas
        occurrences.sort(key=lambda x: x["position"])

        # Filtrar duplicatas dentro de 30 caracteres
        filtered = []
        for occ in occurrences:
            if not filtered or (occ["position"] - filtered[-1]["position"]) > 30:
                filtered.append(occ)

        logger.debug(f"🔍 Ocorrências RPV/INSS encontradas: {len(filtered)}")
        for i, occ in enumerate(filtered):
            logger.debug(f"   {i + 1}. '{occ['term']}' em {occ['position']}")

        return filtered

    async def _extract_publication_for_occurrence(
        self,
        content: str,
        rpv_occurrence: Dict[str, Any],
        source_url: str,
        current_page_number: Optional[int],
    ) -> Optional[Publication]:
        """
        Extrai uma publicação para uma ocorrência específica de RPV/INSS
        Implementa lógica completa com Page Manager
        """
        rpv_position = rpv_occurrence["position"]
        working_content = content
        content_source = "current_page"

        # 1. Buscar processo antes da posição do RPV
        process_info = self._find_process_before_position(working_content, rpv_position)

        if not process_info:
            logger.info(
                f"🔄 Processo não encontrado na página atual - tentando página anterior"
            )

            # Tentar página anterior se disponível
            if (
                current_page_number
                and current_page_number > 1
                and self.page_manager
                and self.content_merger
            ):
                try:
                    # Obter página anterior via Page Manager
                    previous_content = (
                        await self.page_manager.get_previous_page_content(
                            source_url, current_page_number
                        )
                    )

                    if previous_content:
                        logger.info("📥 Página anterior obtida - fazendo merge")

                        # Fazer merge usando Content Merger
                        merged_content = (
                            self.content_merger.merge_cross_page_publication(
                                previous_content, content, rpv_position
                            )
                        )

                        # Validar qualidade do merge
                        if self.content_merger.validate_merged_content(
                            merged_content, [rpv_occurrence["term"]]
                        ):
                            working_content = merged_content
                            content_source = "merged_pages"
                            self.stats["merged_publications"] += 1

                            # Buscar processo no conteúdo merged
                            process_info = self._find_process_before_position(
                                working_content, rpv_position
                            )

                            logger.info(
                                f"✅ Merge bem-sucedido - processo {'encontrado' if process_info else 'não encontrado'}"
                            )
                        else:
                            logger.warning(
                                "❌ Merge inválido - usando conteúdo original"
                            )

                except Exception as e:
                    logger.error(f"❌ Erro ao obter/mergear página anterior: {e}")

        if not process_info:
            logger.warning("❌ Processo não encontrado mesmo com tentativa de merge")
            return None

        logger.info(
            f"📋 Processo encontrado: {process_info['process_number']} (fonte: {content_source})"
        )

        # 2. Determinar fim da publicação
        publication_end = self._find_publication_end(
            working_content, process_info["start_position"]
        )

        # 3. Extrair conteúdo completo da publicação
        publication_content = working_content[
            process_info["start_position"] : publication_end
        ]

        logger.info(f"📏 Conteúdo da publicação: {len(publication_content)} chars")

        # 4. Extrair dados estruturados
        structured_data = self._extract_structured_data(
            publication_content, process_info["process_number"]
        )

        if not structured_data:
            logger.warning("❌ Falha na extração de dados estruturados")
            return None

        # 5. Validar qualidade dos dados extraídos
        quality_score = self._calculate_extraction_quality(
            structured_data, publication_content
        )

        if quality_score < self.quality_threshold:
            logger.warning(
                f"❌ Qualidade insuficiente: {quality_score:.2f} < {self.quality_threshold}"
            )
            self.stats["quality_rejections"] += 1
            return None

        logger.info(f"✅ Qualidade aprovada: {quality_score:.2f}")

        # 6. Criar objeto Publication
        publication = self._create_publication_object(structured_data, source_url)

        return publication

    def _find_process_before_position(
        self, content: str, position: int
    ) -> Optional[Dict[str, Any]]:
        """
        Busca o processo mais próximo ANTES da posição especificada
        """
        # Limitar busca a uma distância razoável
        search_start = max(0, position - self.max_process_search_distance)
        search_content = content[search_start:position]

        # Buscar todos os processos na região de busca
        process_matches = list(self.PROCESS_PATTERN.finditer(search_content))

        if not process_matches:
            return None

        # Pegar o processo mais próximo (último na lista)
        last_match = process_matches[-1]
        process_number = last_match.group(1)

        # Ajustar posição para o conteúdo original
        actual_start = search_start + last_match.start()

        logger.debug(
            f"🔍 Processo encontrado: {process_number} na posição {actual_start}"
        )

        return {
            "process_number": process_number,
            "start_position": actual_start,
            "end_position": search_start + last_match.end(),
            "match_object": last_match,
        }

    def _find_publication_end(self, content: str, start_position: int) -> int:
        """
        Encontra o fim da publicação atual
        """
        # Procurar próximo processo após a posição inicial
        search_content = content[
            start_position + 100 :
        ]  # Skip inicial para evitar o processo atual

        next_process_match = self.PROCESS_PATTERN.search(search_content)

        if next_process_match:
            # Fim é onde começa o próximo processo
            end_position = start_position + 100 + next_process_match.start()
        else:
            # Se não há próximo processo, usar o resto do conteúdo
            end_position = len(content)

        return end_position

    def _extract_structured_data(
        self, content: str, process_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai todos os dados estruturados da publicação
        """
        try:
            # Extrair componentes principais
            authors = self._extract_authors(content)
            lawyers = self._extract_lawyers(content)
            monetary_values = self._extract_monetary_values(content)
            dates = self._extract_dates(content)

            # Validar dados mínimos
            if not authors:
                logger.warning("⚠️ Nenhum autor encontrado no padrão '- NOME - Vistos'")
                return None

            structured_data = {
                "process_number": process_number,
                "authors": authors,
                "lawyers": lawyers,
                "monetary_values": monetary_values,
                "dates": dates,
                "raw_content": content,
            }

            logger.debug(
                f"📊 Dados extraídos: {len(authors)} autores, {len(lawyers)} advogados"
            )

            return structured_data

        except Exception as e:
            logger.error(f"❌ Erro na extração de dados estruturados: {e}")
            return None

    def _extract_authors(self, content: str) -> List[str]:
        """
        Extrai autores no formato '- NOME - Vistos'
        """
        authors = []

        for match in self.AUTHOR_PATTERN.finditer(content):
            author_name = self._clean_author_name(match.group(1))
            if author_name and len(author_name) > 2:
                authors.append(author_name)

        # Remover duplicatas mantendo ordem
        unique_authors = []
        for author in authors:
            if author not in unique_authors:
                unique_authors.append(author)

        return unique_authors

    def _extract_lawyers(self, content: str) -> List[Lawyer]:
        """
        Extrai advogados com OAB
        """
        lawyers = []

        for pattern in self.LAWYER_PATTERNS:
            for match in pattern.finditer(content):
                name = self._clean_lawyer_name(match.group(1))
                oab = match.group(2)

                if name and oab:
                    lawyer = Lawyer(name=name, oab_number=oab)

                    # Evitar duplicatas
                    if not any(l.oab_number == oab for l in lawyers):
                        lawyers.append(lawyer)

        return lawyers

    def _extract_monetary_values(
        self, content: str
    ) -> Dict[str, Optional[MonetaryValue]]:
        """
        Extrai valores monetários categorizados
        """
        values = {}

        for value_type, patterns in self.MONETARY_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    value_str = match.group(1)
                    decimal_value = self._parse_monetary_string(value_str)

                    if decimal_value:
                        values[value_type] = MonetaryValue(
                            amount=decimal_value, currency="BRL"
                        )
                        break  # Primeira ocorrência válida

        return values

    def _extract_dates(self, content: str) -> Dict[str, Optional[datetime]]:
        """
        Extrai datas relevantes
        """
        dates = {}

        # Padrões de data mais comuns no DJE
        date_patterns = [
            re.compile(
                r"São\s+Paulo,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", re.IGNORECASE
            ),
            re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})"),
        ]

        month_names = {
            "janeiro": 1,
            "fevereiro": 2,
            "março": 3,
            "abril": 4,
            "maio": 5,
            "junho": 6,
            "julho": 7,
            "agosto": 8,
            "setembro": 9,
            "outubro": 10,
            "novembro": 11,
            "dezembro": 12,
        }

        for pattern in date_patterns:
            match = pattern.search(content)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(2).isdigit():
                            # Formato DD/MM/YYYY
                            day, month, year = (
                                int(match.group(1)),
                                int(match.group(2)),
                                int(match.group(3)),
                            )
                        else:
                            # Formato DD de MONTH de YYYY
                            day = int(match.group(1))
                            month = month_names.get(match.group(2).lower(), 1)
                            year = int(match.group(3))

                        dates["publication_date"] = datetime(year, month, day)
                        break
                except (ValueError, KeyError):
                    continue

        return dates

    def _calculate_extraction_quality(
        self, structured_data: Dict[str, Any], content: str
    ) -> float:
        """
        Calcula score de qualidade da extração (0.0 a 1.0)
        """
        score = 0.0

        # Processo válido (20%)
        if structured_data.get("process_number"):
            score += 0.2

        # Autores encontrados (30%)
        authors = structured_data.get("authors", [])
        if authors:
            score += 0.3

        # Advogados com OAB (20%)
        lawyers = structured_data.get("lawyers", [])
        if lawyers:
            score += 0.2

        # Valores monetários (20%)
        monetary_values = structured_data.get("monetary_values", {})
        if any(monetary_values.values()):
            score += 0.2

        # Datas válidas (10%)
        dates = structured_data.get("dates", {})
        if any(dates.values()):
            score += 0.1

        return min(score, 1.0)

    def _create_publication_object(
        self, structured_data: Dict[str, Any], source_url: str
    ) -> Publication:
        """
        Cria objeto Publication a partir dos dados estruturados
        """
        monetary_values = structured_data.get("monetary_values", {})
        dates = structured_data.get("dates", {})

        return Publication(
            process_number=structured_data["process_number"],
            authors=structured_data.get("authors", []),
            lawyers=structured_data.get("lawyers", []),
            gross_value=monetary_values.get("gross_value"),
            net_value=monetary_values.get("net_value"),
            publication_date=dates.get("publication_date"),
            availability_date=dates.get("availability_date", datetime.now()),
            source_url=source_url,
            raw_content=structured_data.get("raw_content", ""),
        )

    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto removendo caracteres especiais e padronizando espaços
        """
        # Remover caracteres de controle
        text = re.sub(r"[\r\n\t]+", " ", text)

        # Normalizar espaços múltiplos
        text = re.sub(r"\s+", " ", text)

        # Normalizar caracteres Unicode
        text = unicodedata.normalize("NFKD", text)

        return text.strip()

    def _clean_author_name(self, name: str) -> str:
        """
        Limpa e normaliza nome do autor
        """
        # Remover espaços extras e caracteres especiais
        name = re.sub(r"\s+", " ", name.strip())
        name = re.sub(r"[^\w\s\.]", "", name)

        # Capitalizar corretamente
        name = " ".join(word.capitalize() for word in name.split())

        return name

    def _clean_lawyer_name(self, name: str) -> str:
        """
        Limpa e normaliza nome do advogado
        """
        return self._clean_author_name(name)

    def _parse_monetary_string(self, value_str: str) -> Optional[Decimal]:
        """
        Converte string monetária para Decimal
        """
        try:
            # Remover caracteres não numéricos exceto vírgula e ponto
            clean_value = re.sub(r"[^\d,.]", "", value_str)

            # Lidar com formato brasileiro (vírgula como decimal)
            if "," in clean_value and "." in clean_value:
                # Formato 1.234.567,89
                clean_value = clean_value.replace(".", "").replace(",", ".")
            elif "," in clean_value:
                # Formato 1234,89
                clean_value = clean_value.replace(",", ".")

            return Decimal(clean_value)

        except (InvalidOperation, ValueError):
            return None

    def _log_extraction_stats(self):
        """
        Log das estatísticas de extração
        """
        logger.info("📊 === ESTATÍSTICAS DE EXTRAÇÃO ===")
        logger.info(f"🎯 RPV/INSS encontrados: {self.stats['total_rpv_found']}")
        logger.info(
            f"✅ Extrações bem-sucedidas: {self.stats['successful_extractions']}"
        )
        logger.info(f"❌ Extrações falhadas: {self.stats['failed_extractions']}")
        logger.info(f"🔄 Publicações merged: {self.stats['merged_publications']}")
        logger.info(f"📊 Rejeições por qualidade: {self.stats['quality_rejections']}")

        if self.page_manager:
            cache_stats = self.page_manager.get_cache_stats()
            logger.info(f"💾 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")
            logger.info(f"📥 Downloads realizados: {cache_stats['downloads_made']}")

    def get_extraction_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas da extração
        """
        stats = self.stats.copy()

        if self.page_manager:
            stats["cache_stats"] = self.page_manager.get_cache_stats()

        if self.content_merger:
            stats["merge_stats"] = self.content_merger.get_merge_statistics()

        return stats

    def reset_statistics(self):
        """
        Reseta estatísticas para nova sessão
        """
        self.stats = {
            "total_rpv_found": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "merged_publications": 0,
            "cache_hits": 0,
            "quality_rejections": 0,
        }

        if self.page_manager:
            self.page_manager.clear_cache()

        logger.info("📊 Estatísticas resetadas")
