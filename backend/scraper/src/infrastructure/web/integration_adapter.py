"""
🔗 INTEGRATION ADAPTER - FASE 3

Adapter que integra o Enhanced Parser com o sistema atual:
1. Interface compatível com o scraper existente
2. Configuração automática de dependências
3. Fallback para parser antigo em caso de erro
4. Métricas comparativas de performance
5. Feature flag para ativação gradual
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from domain.entities.publication import Publication
from infrastructure.logging.logger import setup_logger
from infrastructure.web.enhanced_parser_integrated import EnhancedDJEParserIntegrated
from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser

logger = setup_logger(__name__)


class DJEParserIntegrationAdapter:
    """
    Adapter de integração que:
    - Mantém compatibilidade com código existente
    - Permite ativação gradual do novo parser
    - Fornece fallback automático para parser antigo
    - Coleta métricas comparativas
    """

    def __init__(
        self,
        use_enhanced_parser: bool = True,
        fallback_on_error: bool = True,
        enable_metrics: bool = True,
    ):
        # Configurações
        self.use_enhanced_parser = use_enhanced_parser
        self.fallback_on_error = fallback_on_error
        self.enable_metrics = enable_metrics

        # Parsers
        self.enhanced_parser = EnhancedDJEParserIntegrated()
        self.legacy_parser = EnhancedDJEContentParser()

        # Métricas comparativas
        self.metrics = {
            "enhanced_parser": {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_publications": 0,
                "total_time": 0.0,
                "merged_publications": 0,
                "cache_hits": 0,
            },
            "legacy_parser": {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_publications": 0,
                "total_time": 0.0,
            },
            "fallback_activations": 0,
            "start_time": datetime.now(),
        }

        logger.info(f"🔗 DJE Parser Integration Adapter inicializado")
        logger.info(
            f"   🚀 Enhanced Parser: {'ATIVO' if use_enhanced_parser else 'INATIVO'}"
        )
        logger.info(f"   🔄 Fallback: {'ATIVO' if fallback_on_error else 'INATIVO'}")
        logger.info(f"   📊 Métricas: {'ATIVAS' if enable_metrics else 'INATIVAS'}")

    def set_scraper_adapter(self, scraper_adapter):
        """
        Configura adapter do scraper em ambos os parsers
        """
        # Configurar enhanced parser com Page Manager
        self.enhanced_parser.set_scraper_adapter(scraper_adapter)

        # Configurar legacy parser (compatibilidade)
        self.legacy_parser.set_scraper_adapter(scraper_adapter)

        logger.info("🔗 Scraper adapter configurado em ambos os parsers")

    async def parse_multiple_publications_enhanced(
        self,
        content: str,
        source_url: str = "",
        current_page_number: Optional[int] = None,
    ) -> List[Publication]:
        """
        Método principal de extração com integração inteligente

        Fluxo:
        1. Tenta enhanced parser se ativo
        2. Faz fallback para legacy parser se necessário
        3. Coleta métricas de ambos se habilitado
        4. Retorna melhor resultado
        """
        logger.info("🔗 === INICIANDO EXTRAÇÃO VIA INTEGRATION ADAPTER ===")

        publications = []

        if self.use_enhanced_parser:
            # Tentar enhanced parser primeiro
            try:
                publications = await self._execute_enhanced_parser(
                    content, source_url, current_page_number
                )

                if publications:
                    logger.info(
                        f"✅ Enhanced parser bem-sucedido: {len(publications)} publicações"
                    )
                    return publications
                else:
                    logger.warning("⚠️ Enhanced parser não encontrou publicações")

            except Exception as e:
                logger.error(f"❌ Erro no enhanced parser: {e}")
                self.metrics["enhanced_parser"]["failed_calls"] += 1

                if not self.fallback_on_error:
                    return []

        # Fallback para legacy parser
        if self.fallback_on_error or not self.use_enhanced_parser:
            try:
                logger.info("🔄 Ativando fallback para legacy parser...")
                publications = await self._execute_legacy_parser(
                    content, source_url, current_page_number
                )

                if self.use_enhanced_parser:
                    self.metrics["fallback_activations"] += 1

                logger.info(
                    f"🔄 Legacy parser resultado: {len(publications)} publicações"
                )

            except Exception as e:
                logger.error(f"❌ Erro no legacy parser: {e}")
                self.metrics["legacy_parser"]["failed_calls"] += 1

        return publications

    async def _execute_enhanced_parser(
        self, content: str, source_url: str, current_page_number: Optional[int]
    ) -> List[Publication]:
        """
        Executa enhanced parser com métricas
        """
        start_time = datetime.now()

        try:
            self.metrics["enhanced_parser"]["total_calls"] += 1

            publications = (
                await self.enhanced_parser.parse_multiple_publications_enhanced(
                    content, source_url, current_page_number
                )
            )

            # Coletar métricas
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["enhanced_parser"]["total_time"] += execution_time
            self.metrics["enhanced_parser"]["successful_calls"] += 1
            self.metrics["enhanced_parser"]["total_publications"] += len(publications)

            # Coletar estatísticas específicas do enhanced parser
            parser_stats = self.enhanced_parser.get_extraction_statistics()
            self.metrics["enhanced_parser"]["merged_publications"] += parser_stats.get(
                "merged_publications", 0
            )

            if "cache_stats" in parser_stats:
                self.metrics["enhanced_parser"]["cache_hits"] += parser_stats[
                    "cache_stats"
                ].get("hits", 0)

            logger.info(f"⏱️ Enhanced parser executado em {execution_time:.2f}s")

            return publications

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["enhanced_parser"]["total_time"] += execution_time
            self.metrics["enhanced_parser"]["failed_calls"] += 1
            raise e

    async def _execute_legacy_parser(
        self, content: str, source_url: str, current_page_number: Optional[int]
    ) -> List[Publication]:
        """
        Executa legacy parser com métricas
        """
        start_time = datetime.now()

        try:
            self.metrics["legacy_parser"]["total_calls"] += 1

            publications = (
                await self.legacy_parser.parse_multiple_publications_enhanced(
                    content, source_url, current_page_number
                )
            )

            # Coletar métricas
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["legacy_parser"]["total_time"] += execution_time
            self.metrics["legacy_parser"]["successful_calls"] += 1
            self.metrics["legacy_parser"]["total_publications"] += len(publications)

            logger.info(f"⏱️ Legacy parser executado em {execution_time:.2f}s")

            return publications

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["legacy_parser"]["total_time"] += execution_time
            self.metrics["legacy_parser"]["failed_calls"] += 1
            raise e

    def get_comparative_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas comparativas detalhadas
        """
        total_runtime = (datetime.now() - self.metrics["start_time"]).total_seconds()

        # Calcular médias e taxas
        enhanced_metrics = self.metrics["enhanced_parser"]
        legacy_metrics = self.metrics["legacy_parser"]

        enhanced_avg_time = (
            enhanced_metrics["total_time"] / enhanced_metrics["total_calls"]
            if enhanced_metrics["total_calls"] > 0
            else 0
        )
        legacy_avg_time = (
            legacy_metrics["total_time"] / legacy_metrics["total_calls"]
            if legacy_metrics["total_calls"] > 0
            else 0
        )

        enhanced_success_rate = (
            enhanced_metrics["successful_calls"] / enhanced_metrics["total_calls"] * 100
            if enhanced_metrics["total_calls"] > 0
            else 0
        )
        legacy_success_rate = (
            legacy_metrics["successful_calls"] / legacy_metrics["total_calls"] * 100
            if legacy_metrics["total_calls"] > 0
            else 0
        )

        enhanced_pub_rate = (
            enhanced_metrics["total_publications"] / enhanced_metrics["total_calls"]
            if enhanced_metrics["total_calls"] > 0
            else 0
        )
        legacy_pub_rate = (
            legacy_metrics["total_publications"] / legacy_metrics["total_calls"]
            if legacy_metrics["total_calls"] > 0
            else 0
        )

        return {
            "session_info": {
                "total_runtime_seconds": total_runtime,
                "start_time": self.metrics["start_time"].isoformat(),
                "fallback_activations": self.metrics["fallback_activations"],
            },
            "enhanced_parser": {
                **enhanced_metrics,
                "average_execution_time": enhanced_avg_time,
                "success_rate_percent": enhanced_success_rate,
                "publications_per_call": enhanced_pub_rate,
            },
            "legacy_parser": {
                **legacy_metrics,
                "average_execution_time": legacy_avg_time,
                "success_rate_percent": legacy_success_rate,
                "publications_per_call": legacy_pub_rate,
            },
            "comparative_analysis": {
                "time_improvement_percent": (
                    ((legacy_avg_time - enhanced_avg_time) / legacy_avg_time * 100)
                    if legacy_avg_time > 0
                    else 0
                ),
                "publication_rate_improvement": enhanced_pub_rate - legacy_pub_rate,
                "success_rate_improvement": enhanced_success_rate - legacy_success_rate,
                "enhanced_parser_advantages": [
                    "Page Manager para publicações divididas",
                    "Cache inteligente para downloads",
                    "Validação de qualidade automática",
                    "Padrões regex aprimorados",
                ],
            },
        }

    def log_performance_summary(self):
        """
        Log detalhado das métricas de performance
        """
        metrics = self.get_comparative_metrics()

        logger.info("📊 === RESUMO DE PERFORMANCE - INTEGRATION ADAPTER ===")

        # Session info
        session = metrics["session_info"]
        logger.info(f"⏱️ Tempo total de sessão: {session['total_runtime_seconds']:.1f}s")
        logger.info(f"🔄 Ativações de fallback: {session['fallback_activations']}")

        # Enhanced parser
        enhanced = metrics["enhanced_parser"]
        logger.info(f"\n🚀 ENHANCED PARSER:")
        logger.info(
            f"   📞 Chamadas: {enhanced['total_calls']} (✅ {enhanced['successful_calls']}, ❌ {enhanced['failed_calls']})"
        )
        logger.info(
            f"   📋 Publicações: {enhanced['total_publications']} ({enhanced['publications_per_call']:.1f}/chamada)"
        )
        logger.info(f"   ⏱️ Tempo médio: {enhanced['average_execution_time']:.2f}s")
        logger.info(f"   ✅ Taxa de sucesso: {enhanced['success_rate_percent']:.1f}%")
        logger.info(f"   🔄 Merges realizados: {enhanced['merged_publications']}")
        logger.info(f"   💾 Cache hits: {enhanced['cache_hits']}")

        # Legacy parser
        legacy = metrics["legacy_parser"]
        if legacy["total_calls"] > 0:
            logger.info(f"\n🔄 LEGACY PARSER:")
            logger.info(
                f"   📞 Chamadas: {legacy['total_calls']} (✅ {legacy['successful_calls']}, ❌ {legacy['failed_calls']})"
            )
            logger.info(
                f"   📋 Publicações: {legacy['total_publications']} ({legacy['publications_per_call']:.1f}/chamada)"
            )
            logger.info(f"   ⏱️ Tempo médio: {legacy['average_execution_time']:.2f}s")
            logger.info(f"   ✅ Taxa de sucesso: {legacy['success_rate_percent']:.1f}%")

        # Análise comparativa
        comparative = metrics["comparative_analysis"]
        if legacy["total_calls"] > 0:
            logger.info(f"\n🔬 ANÁLISE COMPARATIVA:")
            logger.info(
                f"   ⚡ Melhoria de tempo: {comparative['time_improvement_percent']:.1f}%"
            )
            logger.info(
                f"   📈 Melhoria na taxa de publicações: {comparative['publication_rate_improvement']:+.1f}"
            )
            logger.info(
                f"   📊 Melhoria na taxa de sucesso: {comparative['success_rate_improvement']:+.1f}%"
            )

    def configure_enhanced_parser(self, **kwargs):
        """
        Permite configuração dinâmica do enhanced parser
        """
        if "quality_threshold" in kwargs:
            self.enhanced_parser.quality_threshold = kwargs["quality_threshold"]
            logger.info(
                f"🎯 Quality threshold configurado: {kwargs['quality_threshold']}"
            )

        if "max_process_search_distance" in kwargs:
            self.enhanced_parser.max_process_search_distance = kwargs[
                "max_process_search_distance"
            ]
            logger.info(
                f"🔍 Max search distance configurado: {kwargs['max_process_search_distance']}"
            )

    def enable_enhanced_parser(self):
        """Ativa enhanced parser"""
        self.use_enhanced_parser = True
        logger.info("🚀 Enhanced parser ATIVADO")

    def disable_enhanced_parser(self):
        """Desativa enhanced parser (força legacy)"""
        self.use_enhanced_parser = False
        logger.info("🔄 Enhanced parser DESATIVADO - usando apenas legacy")

    def enable_fallback(self):
        """Ativa fallback automático"""
        self.fallback_on_error = True
        logger.info("🔄 Fallback automático ATIVADO")

    def disable_fallback(self):
        """Desativa fallback automático"""
        self.fallback_on_error = False
        logger.info("⚠️ Fallback automático DESATIVADO")

    def reset_metrics(self):
        """Reseta todas as métricas"""
        self.metrics = {
            "enhanced_parser": {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_publications": 0,
                "total_time": 0.0,
                "merged_publications": 0,
                "cache_hits": 0,
            },
            "legacy_parser": {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_publications": 0,
                "total_time": 0.0,
            },
            "fallback_activations": 0,
            "start_time": datetime.now(),
        }

        # Resetar estatísticas dos parsers
        if hasattr(self.enhanced_parser, "reset_statistics"):
            self.enhanced_parser.reset_statistics()

        logger.info("📊 Métricas resetadas")

    def get_current_parser_mode(self) -> str:
        """Retorna modo atual do parser"""
        if self.use_enhanced_parser:
            return "enhanced" + (" + fallback" if self.fallback_on_error else "")
        else:
            return "legacy_only"

    def __repr__(self):
        return f"DJEParserIntegrationAdapter(mode={self.get_current_parser_mode()})"
