"""
Serviço para enriquecimento de publicações com dados detalhados do e-SAJ
Consulta processos individuais e armazena informações complementares
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.publication import Publication
from infrastructure.web.esaj_process_scraper import ESAJProcessScraper
from infrastructure.logging.logger import setup_logger
from playwright.async_api import async_playwright, Browser

logger = setup_logger(__name__)


class ProcessEnrichmentService:
    """
    Serviço para enriquecer publicações com dados detalhados do processo
    """

    def __init__(self, publication_repository: Optional[Any] = None):
        self.publication_repository = publication_repository
        self.browser: Optional[Browser] = None
        self.esaj_scraper: Optional[ESAJProcessScraper] = None

    async def __aenter__(self):
        """Context manager para inicializar browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.esaj_scraper = ESAJProcessScraper(self.browser)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager para fechar browser"""
        if self.browser:
            await self.browser.close()

    async def enrich_publications(
        self, publications: List[Publication]
    ) -> List[Dict[str, Any]]:
        """
        Enriquece lista de publicações com dados detalhados do e-SAJ

        Args:
            publications: Lista de publicações para enriquecer

        Returns:
            Lista de dados enriquecidos
        """
        logger.info(
            f"🔍 Iniciando enriquecimento de {len(publications)} publicações..."
        )

        enriched_data = []

        for i, publication in enumerate(publications, 1):
            logger.info(
                f"📋 Processando publicação {i}/{len(publications)}: {publication.process_number}"
            )

            try:
                # Extrair dados detalhados do processo
                process_data = await self.esaj_scraper.scrape_process_details(
                    publication.process_number
                )

                if process_data:
                    # Combinar dados da publicação com dados do processo
                    enriched_item = await self._combine_publication_data(
                        publication, process_data
                    )

                    # Salvar no banco de dados
                    await self._save_enriched_data(enriched_item)

                    enriched_data.append(enriched_item)
                    logger.info(
                        f"✅ Publicação {publication.process_number} enriquecida com sucesso"
                    )
                else:
                    logger.warning(
                        f"⚠️ Não foi possível extrair dados do processo: {publication.process_number}"
                    )

                # Delay entre requisições para evitar sobrecarga
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(
                    f"❌ Erro ao enriquecer publicação {publication.process_number}: {e}"
                )
                continue

        logger.info(
            f"✅ Enriquecimento concluído: {len(enriched_data)}/{len(publications)} publicações processadas"
        )
        return enriched_data

    async def _combine_publication_data(
        self, publication: Publication, process_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combina dados da publicação DJE com dados detalhados do processo
        """
        logger.info(f"🔗 Combinando dados para processo: {publication.process_number}")

        # Dados base da publicação DJE
        enriched_data = {
            # Identificação
            "process_number": publication.process_number,
            "extraction_timestamp": datetime.now().isoformat(),
            # Dados do DJE (publicação original)
            "dje_data": {
                "content": publication.content,
                "publication_date": publication.publication_date.isoformat()
                if publication.publication_date
                else None,
                "availability_date": publication.availability_date.isoformat()
                if publication.availability_date
                else None,
                "gross_value": float(publication.gross_value.to_real())
                if publication.gross_value
                else None,
                "interest_value": float(publication.interest_value.to_real())
                if publication.interest_value
                else None,
                "attorney_fees": float(publication.attorney_fees.to_real())
                if publication.attorney_fees
                else None,
                "lawyers": [
                    {"name": lawyer.name, "oab": lawyer.oab}
                    for lawyer in publication.lawyers
                ],
            },
            # Dados detalhados do e-SAJ
            "esaj_data": process_data,
            # Dados consolidados (combinação inteligente)
            "consolidated_data": await self._consolidate_data(
                publication, process_data
            ),
        }

        return enriched_data

    async def _consolidate_data(
        self, publication: Publication, process_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consolida dados do DJE com dados do e-SAJ, priorizando fontes mais confiáveis
        """
        logger.info("📊 Consolidando dados de múltiplas fontes...")

        consolidated = {
            "process_number": publication.process_number,
            "publication_date": None,
            "availability_date": None,
            "gross_value": None,
            "interest_value": None,
            "attorney_fees": None,
            "content": publication.content,
            "parties": {"authors": [], "lawyers": []},
            "data_sources": {
                "dje_available": True,
                "esaj_available": process_data is not None,
                "consolidation_strategy": "esaj_priority",  # e-SAJ tem prioridade por ser mais detalhado
            },
        }

        # 1. Datas - priorizar e-SAJ se disponível
        if process_data and process_data.get("movements"):
            movements = process_data["movements"]

            # Data de publicação
            if movements.get("publication_date"):
                consolidated["publication_date"] = movements["publication_date"]
                consolidated["data_sources"]["publication_date_source"] = "esaj"
            elif publication.publication_date:
                consolidated["publication_date"] = (
                    publication.publication_date.isoformat()
                )
                consolidated["data_sources"]["publication_date_source"] = "dje"

            # Data de disponibilidade
            if movements.get("availability_date"):
                consolidated["availability_date"] = movements["availability_date"]
                consolidated["data_sources"]["availability_date_source"] = "esaj"
            elif publication.availability_date:
                consolidated["availability_date"] = (
                    publication.availability_date.isoformat()
                )
                consolidated["data_sources"]["availability_date_source"] = "dje"
        else:
            # Usar dados do DJE se e-SAJ não disponível
            if publication.publication_date:
                consolidated["publication_date"] = (
                    publication.publication_date.isoformat()
                )
                consolidated["data_sources"]["publication_date_source"] = "dje"
            if publication.availability_date:
                consolidated["availability_date"] = (
                    publication.availability_date.isoformat()
                )
                consolidated["data_sources"]["availability_date_source"] = "dje"

        # 2. Valores monetários - priorizar e-SAJ se disponível
        if process_data and process_data.get("movements", {}).get(
            "homologation_details"
        ):
            homolog = process_data["movements"]["homologation_details"]

            consolidated["gross_value"] = homolog.get("gross_value") or (
                float(publication.gross_value.to_real())
                if publication.gross_value
                else None
            )
            consolidated["interest_value"] = homolog.get("interest_value") or (
                float(publication.interest_value.to_real())
                if publication.interest_value
                else None
            )
            consolidated["attorney_fees"] = homolog.get("attorney_fees") or (
                float(publication.attorney_fees.to_real())
                if publication.attorney_fees
                else None
            )
            consolidated["data_sources"]["monetary_values_source"] = "esaj_priority"
        else:
            # Usar dados do DJE
            consolidated["gross_value"] = (
                float(publication.gross_value.to_real())
                if publication.gross_value
                else None
            )
            consolidated["interest_value"] = (
                float(publication.interest_value.to_real())
                if publication.interest_value
                else None
            )
            consolidated["attorney_fees"] = (
                float(publication.attorney_fees.to_real())
                if publication.attorney_fees
                else None
            )
            consolidated["data_sources"]["monetary_values_source"] = "dje_only"

        # 3. Partes e advogados - combinar dados
        if process_data and process_data.get("parties"):
            parties = process_data["parties"]
            consolidated["parties"]["authors"] = parties.get("authors", [])
            consolidated["parties"]["lawyers"] = parties.get("lawyers", [])
            consolidated["data_sources"]["parties_source"] = "esaj"

        # Adicionar advogados do DJE se não estiverem no e-SAJ
        dje_lawyers = [
            {"name": lawyer.name, "oab": lawyer.oab} for lawyer in publication.lawyers
        ]
        if dje_lawyers and not consolidated["parties"]["lawyers"]:
            consolidated["parties"]["lawyers"] = dje_lawyers
            consolidated["data_sources"]["parties_source"] = "dje_fallback"

        return consolidated

    async def _save_enriched_data(self, enriched_data: Dict[str, Any]) -> None:
        """
        Salva dados enriquecidos no banco de dados
        """
        logger.info(
            f"💾 Salvando dados enriquecidos para processo: {enriched_data['process_number']}"
        )

        try:
            # Aqui você implementaria a lógica para salvar no banco
            # Por enquanto, apenas logamos os dados

            process_number = enriched_data["process_number"]
            consolidated = enriched_data["consolidated_data"]

            logger.info(f"📋 Dados consolidados para {process_number}:")
            logger.info(
                f"   📅 Data publicação: {consolidated.get('publication_date')} (fonte: {consolidated['data_sources'].get('publication_date_source', 'N/A')})"
            )
            logger.info(
                f"   📅 Data disponibilidade: {consolidated.get('availability_date')} (fonte: {consolidated['data_sources'].get('availability_date_source', 'N/A')})"
            )
            logger.info(
                f"   💰 Valor bruto: R$ {consolidated.get('gross_value', 0):,.2f}"
            )
            logger.info(f"   💰 Juros: R$ {consolidated.get('interest_value', 0):,.2f}")
            logger.info(
                f"   💰 Honorários: R$ {consolidated.get('attorney_fees', 0):,.2f}"
            )
            logger.info(f"   👥 Autores: {len(consolidated['parties']['authors'])}")
            logger.info(f"   👨‍💼 Advogados: {len(consolidated['parties']['lawyers'])}")

            # TODO: Implementar salvamento real no banco de dados
            # await self.publication_repository.save_enriched_data(enriched_data)

        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados enriquecidos: {e}")
            raise

    async def enrich_single_publication(
        self, publication: Publication
    ) -> Optional[Dict[str, Any]]:
        """
        Enriquece uma única publicação com dados detalhados

        Args:
            publication: Publicação para enriquecer

        Returns:
            Dados enriquecidos ou None se erro
        """
        logger.info(f"🔍 Enriquecendo publicação única: {publication.process_number}")

        try:
            # Extrair dados detalhados do processo
            process_data = await self.esaj_scraper.scrape_process_details(
                publication.process_number
            )

            if process_data:
                # Combinar dados
                enriched_item = await self._combine_publication_data(
                    publication, process_data
                )

                # Salvar no banco
                await self._save_enriched_data(enriched_item)

                logger.info(
                    f"✅ Publicação {publication.process_number} enriquecida com sucesso"
                )
                return enriched_item
            else:
                logger.warning(
                    f"⚠️ Não foi possível extrair dados do processo: {publication.process_number}"
                )
                return None

        except Exception as e:
            logger.error(
                f"❌ Erro ao enriquecer publicação {publication.process_number}: {e}"
            )
            return None
