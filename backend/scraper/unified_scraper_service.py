#!/usr/bin/env python3
"""
Serviço Unificado de Scraper DJE + e-SAJ
Combina funcionalidades do multi_date_scraper e scraper_cli com enriquecimento integrado
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import argparse
from dataclasses import dataclass, asdict
from uuid import uuid4
import re

# Adicionar o diretório src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings
from application.services.scraping_orchestrator import ScrapingOrchestrator
from application.services.process_enrichment_service import ProcessEnrichmentService
from application.usecases.extract_publications import ExtractPublicationsUseCase
from application.usecases.save_publications_to_files import (
    SavePublicationsToFilesUseCase,
)
from shared.container import Container
from domain.entities.publication import MonetaryValue, Lawyer
from domain.entities.scraping_execution import ScrapingExecution, ExecutionType

logger = setup_logger(__name__)


@dataclass
class ScraperConfig:
    """Configuração do scraper"""

    start_date: datetime
    end_date: datetime
    search_terms: List[str]
    max_pages: int = 20
    enable_enrichment: bool = True
    save_to_files: bool = True
    save_to_api: bool = False
    progress_file: str = "scraper_progress.json"
    single_date: Optional[str] = None  # Para executar apenas uma data específica


@dataclass
class DateProgress:
    """Progresso de uma data"""

    date: str
    processed: bool = False
    publications_found: int = 0
    publications_enriched: int = 0
    enrichment_errors: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None


class UnifiedScraperService:
    """Serviço unificado de scraping com enriquecimento"""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.container = Container(use_optimized_scraper=False)
        self.progress_data: Dict[str, DateProgress] = {}
        self.settings = get_settings()

        # Carregar ou criar arquivo de progresso
        self._load_progress()

        logger.info("🚀 Serviço Unificado de Scraper inicializado")
        logger.info(
            f"📅 Período: {config.start_date.strftime('%d/%m/%Y')} até {config.end_date.strftime('%d/%m/%Y')}"
        )
        logger.info(f"🔍 Termos de busca: {', '.join(config.search_terms)}")
        logger.info(
            f"✨ Enriquecimento: {'ATIVADO' if config.enable_enrichment else 'DESATIVADO'}"
        )

    def _load_progress(self):
        """Carrega arquivo de progresso se existir"""
        progress_path = Path(self.config.progress_file)

        if progress_path.exists():
            try:
                with open(progress_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for date_str, progress_dict in data.get("dates", {}).items():
                        self.progress_data[date_str] = DateProgress(**progress_dict)
                logger.info(f"📂 Progresso carregado: {len(self.progress_data)} datas")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar progresso: {e}")
                self._initialize_progress()
        else:
            self._initialize_progress()

    def _initialize_progress(self):
        """Inicializa progresso para todas as datas"""
        current_date = self.config.start_date

        while current_date <= self.config.end_date:
            date_str = current_date.strftime("%d/%m/%Y")
            if date_str not in self.progress_data:
                self.progress_data[date_str] = DateProgress(date=date_str)
            current_date += timedelta(days=1)

        logger.info(f"📊 Inicializado progresso para {len(self.progress_data)} datas")

    def _save_progress(self):
        """Salva progresso em arquivo"""
        try:
            progress_dict = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_dates": len(self.progress_data),
                    "processed_dates": sum(
                        1 for p in self.progress_data.values() if p.processed
                    ),
                    "total_publications": sum(
                        p.publications_found for p in self.progress_data.values()
                    ),
                    "total_enriched": sum(
                        p.publications_enriched for p in self.progress_data.values()
                    ),
                },
                "dates": {
                    date: asdict(progress)
                    for date, progress in self.progress_data.items()
                },
            }

            with open(self.config.progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ Erro ao salvar progresso: {e}")

    def _merge_with_esaj_data(self, dje_publication, esaj_data):
        """
        Mescla dados do DJE com dados do e-SAJ, dando preferência TOTAL ao e-SAJ.
        Os dados do DJE são mantidos apenas para campos não encontrados no e-SAJ.
        """
        from dataclasses import replace

        logger.info(
            f"🔄 Mesclando dados e-SAJ para processo {dje_publication.process_number}"
        )

        # Debug: mostrar estrutura completa dos dados e-SAJ
        logger.debug(
            f"📊 Estrutura completa e-SAJ: {list(esaj_data.keys()) if isinstance(esaj_data, dict) else 'Não é dict'}"
        )
        if isinstance(esaj_data, dict):
            for key, value in esaj_data.items():
                if isinstance(value, dict):
                    logger.debug(f"   {key}: {list(value.keys())}")
                else:
                    logger.debug(f"   {key}: {type(value)}")

        # Começar com os dados originais do DJE
        updates = {}

        # 1. VALORES MONETÁRIOS - Preferência total ao e-SAJ
        if esaj_data.get("movements", {}).get("homologation_details"):
            homolog = esaj_data["movements"]["homologation_details"]

            # Valor bruto
            if homolog.get("gross_value"):
                try:
                    value_str = self._clean_monetary_value(homolog["gross_value"])
                    updates["gross_value"] = MonetaryValue.from_real(float(value_str))
                    logger.debug(f"   💰 Valor bruto e-SAJ: {value_str}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao processar valor bruto e-SAJ: {e}")

            # Valor de juros
            if homolog.get("interest_value"):
                try:
                    value_str = self._clean_monetary_value(homolog["interest_value"])
                    updates["interest_value"] = MonetaryValue.from_real(
                        float(value_str)
                    )
                    logger.debug(f"   💰 Juros e-SAJ: {value_str}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao processar juros e-SAJ: {e}")

            # Honorários advocatícios
            if homolog.get("attorney_fees"):
                try:
                    value_str = self._clean_monetary_value(homolog["attorney_fees"])
                    updates["attorney_fees"] = MonetaryValue.from_real(float(value_str))
                    logger.debug(f"   💰 Honorários e-SAJ: {value_str}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao processar honorários e-SAJ: {e}")

            # Valor líquido (se disponível)
            if homolog.get("net_value"):
                try:
                    value_str = self._clean_monetary_value(homolog["net_value"])
                    updates["net_value"] = MonetaryValue.from_real(float(value_str))
                    logger.debug(f"   💰 Valor líquido e-SAJ: {value_str}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao processar valor líquido e-SAJ: {e}")

        # 2. ADVOGADOS - Preferência total ao e-SAJ
        if esaj_data.get("parties", {}).get("lawyers"):
            esaj_lawyers = []
            for lawyer_data in esaj_data["parties"]["lawyers"]:
                if lawyer_data.get("name") and lawyer_data.get("name").strip():
                    esaj_lawyers.append(
                        Lawyer(
                            name=lawyer_data.get("name", "").strip(),
                            oab=lawyer_data.get("oab", "").strip(),
                        )
                    )

            if esaj_lawyers:
                updates["lawyers"] = esaj_lawyers
                logger.debug(f"   ⚖️ {len(esaj_lawyers)} advogados do e-SAJ aplicados")
            # Se não há advogados válidos no e-SAJ, manter os do DJE

        # 3. PARTES DO PROCESSO - Preferência ao e-SAJ
        if esaj_data.get("parties", {}).get("authors"):
            esaj_authors = []
            for author in esaj_data["parties"]["authors"]:
                if isinstance(author, str) and author.strip():
                    esaj_authors.append(author.strip())
                elif isinstance(author, dict) and author.get("name"):
                    esaj_authors.append(author["name"].strip())

            if esaj_authors:
                updates["authors"] = esaj_authors
                logger.debug(f"   👥 {len(esaj_authors)} autores do e-SAJ aplicados")

        # Réu (se disponível no e-SAJ)
        if esaj_data.get("parties", {}).get("defendants"):
            defendants = esaj_data["parties"]["defendants"]
            if defendants and len(defendants) > 0:
                defendant = defendants[0]
                if isinstance(defendant, str) and defendant.strip():
                    updates["defendant"] = defendant.strip()
                elif isinstance(defendant, dict) and defendant.get("name"):
                    updates["defendant"] = defendant["name"].strip()
                logger.debug(
                    f"   🏛️ Réu e-SAJ aplicado: {updates.get('defendant', 'N/A')}"
                )

        # 4. DATAS - Preferência ao e-SAJ
        if esaj_data.get("movements", {}).get("availability_date"):
            try:
                date_str = esaj_data["movements"]["availability_date"]
                # Tentar diferentes formatos de data
                for date_format in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        updates["availability_date"] = datetime.strptime(
                            date_str, date_format
                        )
                        logger.debug(f"   📅 Data disponibilização e-SAJ: {date_str}")
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(
                    f"   ⚠️ Erro ao processar data disponibilização e-SAJ: {e}"
                )

        # Data de publicação (se disponível no e-SAJ)
        if esaj_data.get("movements", {}).get("publication_date"):
            try:
                date_str = esaj_data["movements"]["publication_date"]
                for date_format in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        updates["publication_date"] = datetime.strptime(
                            date_str, date_format
                        )
                        logger.debug(f"   📅 Data publicação e-SAJ: {date_str}")
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao processar data publicação e-SAJ: {e}")

        # 5. CONTEÚDO ENRIQUECIDO - Combinar DJE + e-SAJ
        esaj_content_additions = []

        # Adicionar movimentações importantes do e-SAJ
        if esaj_data.get("movements", {}).get("recent_movements"):
            movements = esaj_data["movements"]["recent_movements"]
            if movements and len(movements) > 0:
                esaj_content_additions.append(
                    f"MOVIMENTAÇÕES E-SAJ: {'; '.join(movements[:3])}"
                )

        # Adicionar informações de homologação
        if esaj_data.get("movements", {}).get("homologation_details", {}).get("status"):
            status = esaj_data["movements"]["homologation_details"]["status"]
            esaj_content_additions.append(f"STATUS HOMOLOGAÇÃO: {status}")

        # Se há conteúdo adicional do e-SAJ, combinar com o DJE
        if esaj_content_additions:
            original_content = dje_publication.content.strip()
            esaj_addition = " | ".join(esaj_content_additions)
            combined_content = f"{original_content} | {esaj_addition}"
            updates["content"] = combined_content
            logger.debug(
                f"   📝 Conteúdo enriquecido com {len(esaj_content_additions)} adições do e-SAJ"
            )

        # 6. METADADOS - Adicionar informações do e-SAJ
        esaj_metadata = {
            "esaj_enriched": True,
            "esaj_timestamp": datetime.now().isoformat(),
            "esaj_process_found": True,
        }

        # Adicionar dados específicos do e-SAJ aos metadados
        if esaj_data.get("process_info"):
            esaj_metadata["esaj_process_info"] = esaj_data["process_info"]

        if esaj_data.get("court_info"):
            esaj_metadata["esaj_court_info"] = esaj_data["court_info"]

        # Combinar metadados existentes com os do e-SAJ
        combined_metadata = {**dje_publication.extraction_metadata, **esaj_metadata}
        updates["extraction_metadata"] = combined_metadata

        # Aplicar todas as atualizações de uma vez
        if updates:
            enriched_publication = replace(dje_publication, **updates)
            logger.debug(
                f"✅ Publicação enriquecida com {len(updates)} campos do e-SAJ"
            )
            return enriched_publication

        logger.debug(
            "📝 Nenhum dado relevante encontrado no e-SAJ - mantendo dados originais do DJE"
        )
        return dje_publication

    def _clean_monetary_value(self, value_str: str) -> str:
        """Limpa string de valor monetário para conversão"""
        if not value_str:
            return "0"

        # Remover símbolos de moeda e limpar
        cleaned = (
            str(value_str)
            .replace("R$", "")
            .replace("$", "")
            .replace(".", "")  # Remover separadores de milhares
            .replace(",", ".")  # Converter vírgula decimal para ponto
            .strip()
        )

        # Se não sobrou nada válido, retornar 0
        if not cleaned or cleaned == ".":
            return "0"

        return cleaned

    def _extract_values_from_dje_content(self, publication):
        """
        Extrai valores monetários e advogados do próprio conteúdo do DJE como fallback
        quando o e-SAJ não está disponível (ex: Playwright não instalado)
        """
        logger.info(
            f"🔄 Extraindo dados do conteúdo DJE para {publication.process_number}"
        )

        content = publication.content
        updates = {}

        try:
            # 1. VALORES MONETÁRIOS
            # Padrão prioritário: "importe total de R$ 13.665,70"
            total_match = re.search(r"importe total de R\$\s*([\d.,]+)", content)
            if total_match:
                gross_value = self._clean_monetary_value(total_match.group(1))
                if gross_value and float(gross_value) > 0:
                    updates["gross_value"] = MonetaryValue.from_real(float(gross_value))
                    logger.info(f"   💰 Valor total DJE: R$ {gross_value}")

            # Fallback: "R$ 13.665,70, composto pelas seguintes parcelas:"
            if not updates.get("gross_value"):
                total_match2 = re.search(
                    r"R\$\s*([\d.,]+),\s*comp[oô]sto pelas seguintes parcelas", content
                )
                if total_match2:
                    gross_value = self._clean_monetary_value(total_match2.group(1))
                    if gross_value and float(gross_value) > 0:
                        updates["gross_value"] = MonetaryValue.from_real(
                            float(gross_value)
                        )
                        logger.info(f"   💰 Valor bruto DJE: R$ {gross_value}")

            # Último fallback: "R$ 12.423,37 - principal bruto"
            if not updates.get("gross_value"):
                principal_match = re.search(
                    r"R\$\s*([\d.,]+)\s*-\s*principal bruto", content
                )
                if principal_match:
                    gross_value = self._clean_monetary_value(principal_match.group(1))
                    if gross_value and float(gross_value) > 0:
                        updates["gross_value"] = MonetaryValue.from_real(
                            float(gross_value)
                        )
                        logger.info(f"   💰 Valor principal DJE: R$ {gross_value}")

            # 2. HONORÁRIOS ADVOCATÍCIOS - Padrões melhorados
            fees_patterns = [
                # Padrão simples: qualquer R$ seguido de honorários
                r"R\$\s*([\d.,]+)[^;]*honor[aá]rios",
                # Padrão específico com espaço: "honorários advocat ícios"
                r"R\$\s*([\d.,]+)\s*-\s*honor[aá]rios\s+[a-z]+\s*[íi]cios",
                # Padrão mais flexível
                r"([\d.,]+)\s*-\s*honor[aá]rios",
                # Padrão reverso: encontrar "honorários" e buscar valor antes
                r"R\$\s*([\d.,]+).*?honor[aá]rios",
            ]

            for pattern in fees_patterns:
                fees_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if fees_match:
                    attorney_fees = self._clean_monetary_value(fees_match.group(1))
                    if attorney_fees and float(attorney_fees) > 0:
                        updates["attorney_fees"] = MonetaryValue.from_real(
                            float(attorney_fees)
                        )
                        logger.info(f"   💰 Honorários DJE: R$ {attorney_fees}")
                        break

            # 3. JUROS - Padrão existente funciona
            if "sem juros moratórios" in content.lower():
                updates["interest_value"] = MonetaryValue.from_real(0)
                logger.info(f"   💰 Juros DJE: R$ 0,00 (sem juros)")
            else:
                # Buscar valores de juros se houver
                juros_match = re.search(r"R\$\s*([\d.,]+)\s*-\s*juros", content)
                if juros_match:
                    interest_value = self._clean_monetary_value(juros_match.group(1))
                    if interest_value and float(interest_value) > 0:
                        updates["interest_value"] = MonetaryValue.from_real(
                            float(interest_value)
                        )
                        logger.info(f"   💰 Juros DJE: R$ {interest_value}")

            # 4. ADVOGADOS - Buscar no conteúdo
            # Padrões comuns: "Advogado:" ou "Advogada:"
            lawyer_patterns = [
                r"Advogad[oa]:\s*([A-ZÁÊÇÕ][a-záêçõ\s]+)",
                r"Advogad[oa]\s+([A-ZÁÊÇÕ][a-záêçõ\s]+)",
                r"Dr[.\s]*([A-ZÁÊÇÕ][a-záêçõ\s]+)",
                r"Dra[.\s]*([A-ZÁÊÇÕ][a-záêçõ\s]+)",
            ]

            found_lawyers = []
            for pattern in lawyer_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    # Limpar o nome
                    name = re.sub(r"\s+", " ", name)  # Normalizar espaços
                    name = name.split("\n")[0].strip()  # Primeira linha apenas

                    if len(name) > 2 and not any(
                        lawyer.name == name for lawyer in found_lawyers
                    ):
                        found_lawyers.append(Lawyer(name=name, oab="OAB/SP"))
                        logger.info(f"   ⚖️ Advogado DJE: {name}")

            if found_lawyers:
                updates["lawyers"] = found_lawyers

            # 5. METADADOS
            dje_metadata = {
                "dje_content_extraction": True,
                "dje_extraction_timestamp": datetime.now().isoformat(),
                "esaj_available": False,
                "fallback_reason": "e-SAJ não disponível (Playwright)",
            }

            # Combinar com metadados existentes
            combined_metadata = {**publication.extraction_metadata, **dje_metadata}
            updates["extraction_metadata"] = combined_metadata

            if updates:
                logger.info(f"✅ Extraídos {len(updates)} campos do conteúdo DJE")
                return updates
            else:
                logger.warning("⚠️ Nenhum dado extraído do conteúdo DJE")
                return {}

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do conteúdo DJE: {e}")
            return {}

    def _apply_dje_fallback(self, publication):
        """
        Aplica enriquecimento usando fallback do conteúdo DJE
        """
        from dataclasses import replace

        logger.info(f"🔄 Aplicando fallback DJE para {publication.process_number}")

        # Extrair dados do conteúdo DJE
        dje_updates = self._extract_values_from_dje_content(publication)

        if dje_updates:
            # Aplicar as atualizações
            enriched_publication = replace(publication, **dje_updates)

            # Log dos valores aplicados
            if enriched_publication.gross_value:
                logger.info(
                    f"   💰 Valor bruto DJE: R$ {enriched_publication.gross_value.to_real()}"
                )
            if enriched_publication.attorney_fees:
                logger.info(
                    f"   💰 Honorários DJE: R$ {enriched_publication.attorney_fees.to_real()}"
                )
            if enriched_publication.interest_value is not None:
                logger.info(
                    f"   💰 Juros DJE: R$ {enriched_publication.interest_value.to_real()}"
                )
            if enriched_publication.lawyers:
                logger.info(f"   ⚖️ Advogados DJE: {len(enriched_publication.lawyers)}")

            logger.info(f"✅ Fallback DJE aplicado para {publication.process_number}")
            return enriched_publication
        else:
            logger.warning(
                f"⚠️ Nenhum dado extraído via fallback DJE para {publication.process_number}"
            )
            return publication

    async def scrape_date(self, date_str: str) -> Dict:
        """Executa scraping para uma data específica"""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"📅 PROCESSANDO DATA: {date_str}")
        logger.info(f"{'=' * 60}")

        progress = self.progress_data[date_str]
        progress.start_time = datetime.now().isoformat()

        stats = {
            "publications_found": 0,
            "publications_enriched": 0,
            "enrichment_errors": 0,
            "publications_saved": 0,
        }

        try:
            # 1. Configurar scraper para data específica
            orchestrator = ScrapingOrchestrator(self.container)

            if hasattr(self.container.web_scraper, "_target_date"):
                self.container.web_scraper._target_date = date_str
            else:
                setattr(self.container.web_scraper, "_target_date", date_str)

            # 2. Extrair publicações
            logger.info(f"\n📄 FASE 1: Extração das publicações")
            extract_usecase = ExtractPublicationsUseCase(self.container.web_scraper)
            publications = []

            try:
                logger.info(
                    f"🔄 Iniciando extração com max_pages={self.config.max_pages}"
                )

                # Timeout de segurança: 30 minutos máximo para extração
                extraction_timeout = 1800  # 30 minutos

                try:
                    async with asyncio.timeout(extraction_timeout):
                        async for publication in extract_usecase.execute(
                            self.config.search_terms, max_pages=self.config.max_pages
                        ):
                            publications.append(publication)
                            stats["publications_found"] += 1

                            if stats["publications_found"] % 10 == 0:
                                logger.info(
                                    f"   📊 {stats['publications_found']} publicações encontradas..."
                                )

                            # Debug: Log adicional a cada 25 publicações para detectar loops
                            if stats["publications_found"] % 25 == 0:
                                logger.warning(
                                    f"🐛 DEBUG: {stats['publications_found']} publicações coletadas até agora..."
                                )

                            # Limite de segurança: máximo 500 publicações por data
                            if stats["publications_found"] >= 500:
                                logger.warning(
                                    f"⚠️ Limite de 500 publicações atingido, parando extração"
                                )
                                break

                except asyncio.TimeoutError:
                    logger.warning(
                        f"⚠️ Timeout de {extraction_timeout/60:.1f} minutos atingido durante extração"
                    )

                logger.info(
                    f"🔄 Extração finalizada, processando {len(publications)} publicações"
                )
            except Exception as e:
                logger.error(f"❌ Erro durante extração: {e}")
                import traceback

                traceback.print_exc()

            logger.info(f"✅ Total extraído: {stats['publications_found']} publicações")

            # 3. Enriquecer publicações (se habilitado)
            enriched_publications = (
                publications  # Lista que será atualizada com dados enriquecidos
            )

            if self.config.enable_enrichment and publications:
                logger.info(f"\n🔍 FASE 2: Enriquecimento com e-SAJ (com fallback DJE)")

                # Lista para armazenar publicações enriquecidas
                enriched_publications = []
                esaj_available = False

                try:
                    # Tentar enriquecimento com e-SAJ
                    async with ProcessEnrichmentService() as enrichment_service:
                        enriched_data_list = (
                            await enrichment_service.enrich_publications(publications)
                        )
                        esaj_available = True
                        logger.info("✅ e-SAJ disponível - usando dados do e-SAJ")

                        # Processar dados enriquecidos do e-SAJ
                        for i, enriched_data in enumerate(enriched_data_list):
                            original_publication = publications[i]

                            if enriched_data:
                                # Verificar se há dados do e-SAJ
                                esaj_data = (
                                    enriched_data.get("esaj_data")
                                    if isinstance(enriched_data, dict)
                                    else None
                                )

                                if (
                                    esaj_data
                                    and isinstance(esaj_data, dict)
                                    and len(esaj_data) > 0
                                ):
                                    stats["publications_enriched"] += 1

                                    logger.info(
                                        f"🔄 Aplicando enriquecimento e-SAJ para processo {original_publication.process_number}"
                                    )

                                    # Mesclar dados priorizando e-SAJ
                                    enriched_publication = self._merge_with_esaj_data(
                                        original_publication, esaj_data
                                    )
                                    enriched_publications.append(enriched_publication)

                                    # Log de valores aplicados
                                    if enriched_publication.gross_value:
                                        logger.info(
                                            f"   💰 Valor bruto e-SAJ: R$ {enriched_publication.gross_value.to_real()}"
                                        )
                                    if enriched_publication.attorney_fees:
                                        logger.info(
                                            f"   💰 Honorários e-SAJ: R$ {enriched_publication.attorney_fees.to_real()}"
                                        )
                                    if enriched_publication.lawyers:
                                        logger.info(
                                            f"   ⚖️ Advogados e-SAJ: {len(enriched_publication.lawyers)}"
                                        )
                                else:
                                    # Fallback para extração DJE
                                    logger.info(
                                        f"🔄 Usando fallback DJE para {original_publication.process_number}"
                                    )
                                    enriched_publication = self._apply_dje_fallback(
                                        original_publication
                                    )
                                    enriched_publications.append(enriched_publication)
                                    stats["publications_enriched"] += 1
                            else:
                                # Fallback para extração DJE
                                logger.info(
                                    f"🔄 Usando fallback DJE para {original_publication.process_number}"
                                )
                                enriched_publication = self._apply_dje_fallback(
                                    original_publication
                                )
                                enriched_publications.append(enriched_publication)
                                stats["publications_enriched"] += 1

                except Exception as e:
                    logger.warning(
                        f"⚠️ e-SAJ não disponível ({e}) - usando fallback DJE"
                    )
                    esaj_available = False

                # Se e-SAJ não está disponível, usar fallback DJE para todas as publicações
                if not esaj_available:
                    logger.info("🔄 Aplicando enriquecimento via fallback DJE")
                    for publication in publications:
                        enriched_publication = self._apply_dje_fallback(publication)
                        enriched_publications.append(enriched_publication)
                        stats["publications_enriched"] += 1

                # Atualizar estatísticas
                if (
                    stats["publications_enriched"] % 10 == 0
                    and stats["publications_enriched"] > 0
                ):
                    logger.info(
                        f"   ✨ {stats['publications_enriched']} publicações enriquecidas..."
                    )

                source_info = "e-SAJ" if esaj_available else "fallback DJE"
                logger.info(
                    f"✅ Enriquecimento concluído via {source_info}: {stats['publications_enriched']} sucessos"
                )

            # 4. Salvar publicações (enriquecidas ou originais)
            # 📌 ÚNICO PONTO DE SALVAMENTO JSON - Consolidado após enriquecimento
            if self.config.save_to_files and enriched_publications:
                logger.info(f"\n💾 FASE 3: Salvamento das publicações")
                logger.info(
                    f"   📊 Salvando {len(enriched_publications)} publicações ({stats['publications_enriched']} enriquecidas)"
                )
                save_usecase = SavePublicationsToFilesUseCase()
                save_stats = await save_usecase.execute(enriched_publications)
                stats["publications_saved"] = save_stats["saved"]
                logger.info(
                    f"✅ Salvamento concluído: {stats['publications_saved']} arquivos"
                )

            # Atualizar progresso
            progress.processed = True
            progress.publications_found = stats["publications_found"]
            progress.publications_enriched = stats["publications_enriched"]
            progress.enrichment_errors = stats["enrichment_errors"]
            progress.end_time = datetime.now().isoformat()

            logger.info(f"\n📊 RESUMO DA DATA {date_str}:")
            logger.info(f"   📄 Publicações encontradas: {stats['publications_found']}")
            logger.info(
                f"   ✨ Publicações enriquecidas: {stats['publications_enriched']}"
            )
            logger.info(f"   💾 Publicações salvas: {stats['publications_saved']}")

        except Exception as e:
            logger.error(f"❌ Erro ao processar data {date_str}: {e}")
            progress.error = str(e)
            import traceback

            traceback.print_exc()

        finally:
            self._save_progress()

        return stats

    async def run(self):
        """Executa o scraping para todas as datas ou data específica"""
        try:
            if self.config.single_date:
                # Executar apenas para data específica
                await self.scrape_date(self.config.single_date)
            else:
                # Executar para todas as datas não processadas
                dates_to_process = [
                    date_str
                    for date_str, progress in self.progress_data.items()
                    if not progress.processed or progress.error
                ]

                # Ordenar datas
                dates_to_process.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))

                logger.info(f"\n🗓️ {len(dates_to_process)} datas para processar")

                for i, date_str in enumerate(dates_to_process, 1):
                    logger.info(f"\n📍 Processando {i}/{len(dates_to_process)}")
                    await self.scrape_date(date_str)

                    # Pequena pausa entre datas
                    if i < len(dates_to_process):
                        await asyncio.sleep(2)

            # Estatísticas finais
            total_publications = sum(
                p.publications_found for p in self.progress_data.values()
            )
            total_enriched = sum(
                p.publications_enriched for p in self.progress_data.values()
            )
            total_processed = sum(1 for p in self.progress_data.values() if p.processed)

            logger.info(f"\n{'=' * 60}")
            logger.info(f"🏁 EXECUÇÃO FINALIZADA")
            logger.info(f"{'=' * 60}")
            logger.info(f"📊 Estatísticas Finais:")
            logger.info(
                f"   📅 Datas processadas: {total_processed}/{len(self.progress_data)}"
            )
            logger.info(f"   📄 Total de publicações: {total_publications}")
            logger.info(f"   ✨ Total enriquecido: {total_enriched}")
            if total_publications > 0:
                logger.info(
                    f"   📈 Taxa de enriquecimento: {(total_enriched / total_publications) * 100:.1f}%"
                )

        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            await self.container.cleanup()


def create_parser():
    """Cria parser de argumentos"""
    parser = argparse.ArgumentParser(
        description="Serviço Unificado de Scraper DJE + e-SAJ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Executar para um período de datas:
  python unified_scraper_service.py --start-date 01/06/2025 --end-date 30/06/2025

  # Executar para uma data específica:
  python unified_scraper_service.py --date 20/06/2025

  # Executar sem enriquecimento:
  python unified_scraper_service.py --date 20/06/2025 --no-enrichment

  # Executar com termos de busca customizados:
  python unified_scraper_service.py --date 20/06/2025 --search-terms "RPV" "precatório" "INSS"
""",
    )

    # Argumentos de data
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--date", help="Data específica para processar (formato: DD/MM/YYYY)"
    )
    date_group.add_argument(
        "--start-date", help="Data inicial do período (formato: DD/MM/YYYY)"
    )

    parser.add_argument(
        "--end-date", help="Data final do período (formato: DD/MM/YYYY, padrão: hoje)"
    )

    # Argumentos de busca
    parser.add_argument(
        "--search-terms",
        nargs="+",
        default=["RPV", "pagamento pelo INSS"],
        help="Termos de busca (padrão: RPV 'pagamento pelo INSS')",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Máximo de páginas por busca (padrão: 20)",
    )

    # Argumentos de funcionalidade
    parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="Desabilita o enriquecimento com e-SAJ",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Não salva arquivos JSON (apenas processa)",
    )

    parser.add_argument(
        "--progress-file",
        default="scraper_progress.json",
        help="Arquivo de progresso (padrão: scraper_progress.json)",
    )

    return parser


async def main():
    """Função principal"""
    parser = create_parser()
    args = parser.parse_args()

    # Configurar datas
    if args.date:
        # Modo data única
        start_date = end_date = datetime.strptime(args.date, "%d/%m/%Y")
        single_date = args.date
    else:
        # Modo período
        start_date = datetime.strptime(args.start_date, "%d/%m/%Y")
        end_date = (
            datetime.strptime(args.end_date, "%d/%m/%Y")
            if args.end_date
            else datetime.now()
        )
        single_date = None

    # Criar configuração
    config = ScraperConfig(
        start_date=start_date,
        end_date=end_date,
        search_terms=args.search_terms,
        max_pages=args.max_pages,
        enable_enrichment=not args.no_enrichment,
        save_to_files=not args.no_save,
        progress_file=args.progress_file,
        single_date=single_date,
    )

    # Executar serviço
    service = UnifiedScraperService(config)
    await service.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⌨️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)
