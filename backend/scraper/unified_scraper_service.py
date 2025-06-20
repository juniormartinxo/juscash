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

            async for publication in extract_usecase.execute(
                self.config.search_terms, max_pages=self.config.max_pages
            ):
                publications.append(publication)
                stats["publications_found"] += 1

                if stats["publications_found"] % 10 == 0:
                    logger.info(
                        f"   📊 {stats['publications_found']} publicações encontradas..."
                    )

            logger.info(f"✅ Total extraído: {stats['publications_found']} publicações")

            # 3. Enriquecer publicações (se habilitado)
            if self.config.enable_enrichment and publications:
                logger.info(f"\n🔍 FASE 2: Enriquecimento com e-SAJ")

                async with ProcessEnrichmentService() as enrichment_service:
                    enriched_data_list = await enrichment_service.enrich_publications(
                        publications
                    )

                    # Processar dados enriquecidos
                    for i, enriched_data in enumerate(enriched_data_list):
                        if enriched_data and enriched_data.get("esaj_data"):
                            stats["publications_enriched"] += 1

                            # Atualizar publicação com dados do e-SAJ
                            publication = publications[i]
                            esaj_data = enriched_data["esaj_data"]

                            # Atualizar valores monetários
                            if esaj_data.get("movements", {}).get(
                                "homologation_details"
                            ):
                                homolog = esaj_data["movements"]["homologation_details"]

                                if homolog.get("gross_value"):
                                    try:
                                        value_str = (
                                            homolog["gross_value"]
                                            .replace("R$", "")
                                            .replace(".", "")
                                            .replace(",", ".")
                                            .strip()
                                        )
                                        publication.gross_value = (
                                            MonetaryValue.from_real(float(value_str))
                                        )
                                    except:
                                        pass

                                if homolog.get("interest_value"):
                                    try:
                                        value_str = (
                                            homolog["interest_value"]
                                            .replace("R$", "")
                                            .replace(".", "")
                                            .replace(",", ".")
                                            .strip()
                                        )
                                        publication.interest_value = (
                                            MonetaryValue.from_real(float(value_str))
                                        )
                                    except:
                                        pass

                                if homolog.get("attorney_fees"):
                                    try:
                                        value_str = (
                                            homolog["attorney_fees"]
                                            .replace("R$", "")
                                            .replace(".", "")
                                            .replace(",", ".")
                                            .strip()
                                        )
                                        publication.attorney_fees = (
                                            MonetaryValue.from_real(float(value_str))
                                        )
                                    except:
                                        pass

                            # Atualizar advogados
                            if esaj_data.get("parties", {}).get("lawyers"):
                                publication.lawyers = [
                                    Lawyer(
                                        name=lawyer.get("name", ""),
                                        oab=lawyer.get("oab", ""),
                                    )
                                    for lawyer in esaj_data["parties"]["lawyers"]
                                ]

                            # Atualizar data de disponibilidade
                            if esaj_data.get("movements", {}).get("availability_date"):
                                try:
                                    publication.availability_date = datetime.strptime(
                                        esaj_data["movements"]["availability_date"],
                                        "%d/%m/%Y",
                                    )
                                except:
                                    pass
                        else:
                            stats["enrichment_errors"] += 1

                    if (
                        stats["publications_enriched"] % 10 == 0
                        and stats["publications_enriched"] > 0
                    ):
                        logger.info(
                            f"   ✨ {stats['publications_enriched']} publicações enriquecidas..."
                        )

                logger.info(
                    f"✅ Enriquecimento concluído: {stats['publications_enriched']} sucessos, {stats['enrichment_errors']} falhas"
                )

            # 4. Salvar publicações
            if self.config.save_to_files and publications:
                logger.info(f"\n💾 FASE 3: Salvamento das publicações")
                save_usecase = SavePublicationsToFilesUseCase()
                save_stats = await save_usecase.execute(publications)
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
