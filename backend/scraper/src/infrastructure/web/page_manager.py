"""
🔄 DJE Page Manager - Gerenciamento Inteligente de Páginas PDF

Resolve o problema de publicações divididas entre páginas através de:
1. Download automático de páginas anteriores
2. Cache em memória para evitar re-downloads
3. Merge inteligente de conteúdo dividido
4. Validação de qualidade do merge
"""

import re
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import parse_qs, urlparse
from datetime import datetime

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class DJEPageManager:
    """
    Gerenciador inteligente de páginas PDF do DJE-SP

    Features:
    - Download automático de páginas anteriores quando necessário
    - Cache em memória para evitar downloads duplicados
    - Estatísticas de performance (cache hit/miss)
    - Limpeza automática de cache
    """

    def __init__(self, scraper_adapter):
        self.scraper_adapter = scraper_adapter
        self.page_cache: Dict[str, str] = {}  # Cache de páginas: {page_key: content}
        self.cache_stats = {"hits": 0, "misses": 0, "downloads": 0, "cache_size": 0}

        logger.info("📄 DJEPageManager inicializado")

    async def get_previous_page_content(
        self, current_url: str, current_page: int
    ) -> Optional[str]:
        """
        Obtém conteúdo da página anterior com cache inteligente

        Args:
            current_url: URL da página atual
            current_page: Número da página atual

        Returns:
            Conteúdo da página anterior ou None se não conseguir obter
        """
        if current_page <= 1:
            logger.debug("📄 Já está na primeira página, não há página anterior")
            return None

        previous_page = current_page - 1
        cache_key = self._generate_cache_key(current_url, previous_page)

        # Verificar cache primeiro
        if cache_key in self.page_cache:
            self.cache_stats["hits"] += 1
            logger.info(f"✅ Cache HIT para página {previous_page}")
            return self.page_cache[cache_key]

        # Cache miss - fazer download
        self.cache_stats["misses"] += 1
        logger.info(f"📥 Cache MISS - Baixando página {previous_page}")

        try:
            previous_url = self._build_previous_page_url(current_url, previous_page)

            if not previous_url:
                logger.error(
                    f"❌ Não foi possível construir URL da página {previous_page}"
                )
                return None

            logger.info(f"📥 Baixando página anterior: {previous_page}")
            logger.debug(f"🔗 URL: {previous_url}")

            # Download da página anterior
            content = await self._download_pdf_page_content(previous_url)

            if content:
                # Adicionar ao cache
                self.page_cache[cache_key] = content
                self.cache_stats["downloads"] += 1
                self.cache_stats["cache_size"] = len(self.page_cache)

                logger.info(
                    f"✅ Página {previous_page} baixada e armazenada no cache ({len(content)} chars)"
                )
                logger.info(
                    f"📊 Cache stats: {self.cache_stats['hits']} hits, {self.cache_stats['misses']} misses"
                )

                return content
            else:
                logger.warning(f"⚠️ Conteúdo vazio para página {previous_page}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao baixar página {previous_page}: {e}")
            return None

    def _build_previous_page_url(
        self, current_url: str, target_page: int
    ) -> Optional[str]:
        """
        Constrói URL da página anterior baseada na URL atual

        Exemplo de URL DJE:
        https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710
        """
        try:
            # Usar regex para substituir nuSeqpagina
            pattern = r"nuSeqpagina=(\d+)"
            match = re.search(pattern, current_url)

            if match:
                previous_url = re.sub(
                    pattern, f"nuSeqpagina={target_page}", current_url
                )
                logger.debug(f"🔧 URL construída: {previous_url}")
                return previous_url
            else:
                logger.error(
                    f"❌ Padrão nuSeqpagina não encontrado na URL: {current_url}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao construir URL da página anterior: {e}")
            return None

    async def _download_pdf_page_content(self, url: str) -> Optional[str]:
        """
        Baixa e extrai conteúdo de uma página PDF específica
        """
        try:
            # Abrir nova aba no browser
            page = await self.scraper_adapter.browser.new_page()

            try:
                # Configurar timeouts
                page.set_default_timeout(30000)

                # Navegar para a URL
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Aguardar carregamento
                await asyncio.sleep(2)

                # Tentar aguardar networkidle
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    logger.debug("⏰ Timeout no networkidle para página anterior")

                # Extrair conteúdo HTML
                content = await page.content()

                if content and len(content) > 100:
                    logger.debug(
                        f"✅ Conteúdo extraído da página: {len(content)} chars"
                    )
                    return content
                else:
                    logger.warning("⚠️ Conteúdo muito pequeno ou vazio")
                    return None

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"❌ Erro ao baixar conteúdo da página {url}: {e}")
            return None

    def _generate_cache_key(self, url: str, page_number: int) -> str:
        """
        Gera chave única para cache baseada na URL e número da página
        """
        # Extrair parâmetros relevantes da URL para criar chave única
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Usar parâmetros críticos para gerar chave
            volume = query_params.get("cdVolume", [""])[0]
            diario = query_params.get("nuDiario", [""])[0]
            caderno = query_params.get("cdCaderno", [""])[0]

            cache_key = f"page_{volume}_{diario}_{caderno}_{page_number}"
            return cache_key

        except Exception as e:
            logger.debug(f"Erro ao gerar chave de cache: {e}")
            # Fallback para chave simples
            return f"page_{page_number}_{hash(url) % 10000}"

    def extract_page_number_from_url(self, url: str) -> Optional[int]:
        """
        Extrai número da página da URL
        """
        try:
            match = re.search(r"nuSeqpagina=(\d+)", url)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.debug(f"Erro ao extrair número da página: {e}")
        return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas do cache
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "downloads_made": self.cache_stats["downloads"],
            "cache_size": self.cache_stats["cache_size"],
            "cache_memory_usage": sum(
                len(content) for content in self.page_cache.values()
            ),
            "cached_pages": list(self.page_cache.keys()),
        }

    def clear_cache(self):
        """
        Limpa cache de páginas e reseta estatísticas
        """
        cache_size_before = len(self.page_cache)
        self.page_cache.clear()

        # Manter estatísticas históricas, apenas resetar tamanho
        self.cache_stats["cache_size"] = 0

        logger.info(f"🧹 Cache limpo: {cache_size_before} páginas removidas")

    def optimize_cache(self, max_cache_size: int = 50):
        """
        Otimiza cache removendo páginas antigas se exceder limite
        """
        if len(self.page_cache) <= max_cache_size:
            return

        # Remover páginas mais antigas (implementação simples - FIFO)
        pages_to_remove = len(self.page_cache) - max_cache_size
        oldest_keys = list(self.page_cache.keys())[:pages_to_remove]

        for key in oldest_keys:
            del self.page_cache[key]

        self.cache_stats["cache_size"] = len(self.page_cache)
        logger.info(f"🔧 Cache otimizado: {pages_to_remove} páginas removidas")


class PublicationContentMerger:
    """
    Gerenciador para merge inteligente de publicações divididas entre páginas

    Features:
    - Encontra último processo na página anterior
    - Merge com validação de qualidade
    - Detecção de termos RPV/INSS no conteúdo merged
    - Logs detalhados do processo de merge
    """

    def __init__(self):
        self.PROCESS_PATTERN = re.compile(
            r"Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", re.IGNORECASE
        )

        # Padrões para validação de merge
        self.RPV_PATTERNS = [
            re.compile(r"\bRPV\b", re.IGNORECASE),
            re.compile(r"requisição\s+de\s+pequeno\s+valor", re.IGNORECASE),
            re.compile(r"pagamento\s+pelo\s+INSS", re.IGNORECASE),
        ]

        logger.info("🔄 PublicationContentMerger inicializado")

    def merge_cross_page_publication(
        self,
        previous_page_content: str,
        current_page_content: str,
        rpv_position_in_current: int,
    ) -> str:
        """
        Faz merge inteligente de uma publicação dividida entre duas páginas

        Args:
            previous_page_content: Conteúdo da página anterior
            current_page_content: Conteúdo da página atual
            rpv_position_in_current: Posição do termo RPV na página atual

        Returns:
            Conteúdo completo da publicação merged
        """
        logger.info("🔄 Iniciando merge de publicação dividida entre páginas")

        try:
            # 1. Encontrar o último processo na página anterior
            last_process_in_previous = self._find_last_process_in_content(
                previous_page_content
            )

            if not last_process_in_previous:
                logger.warning("⚠️ Último processo não encontrado na página anterior")
                return current_page_content

            logger.info(
                f"📋 Último processo encontrado: {last_process_in_previous['process_number']}"
            )

            # 2. Extrair conteúdo da página anterior a partir do último processo
            previous_part = previous_page_content[
                last_process_in_previous["start_pos"] :
            ]

            # 3. Extrair conteúdo da página atual até antes do primeiro processo (se houver)
            first_process_in_current = self._find_first_process_in_content(
                current_page_content
            )

            if first_process_in_current:
                # Se há um processo na página atual, usar conteúdo até esse processo
                current_part = current_page_content[
                    : first_process_in_current["start_pos"]
                ]
                logger.info(
                    f"📋 Primeiro processo na página atual: {first_process_in_current['process_number']}"
                )
            else:
                # Se não há processo na página atual, usar toda a página
                current_part = current_page_content
                logger.info(
                    "📋 Nenhum processo na página atual - usando todo o conteúdo"
                )

            # 4. Fazer merge
            merged_content = previous_part + "\n" + current_part

            logger.info(
                f"✅ Merge concluído: {len(previous_part)} + {len(current_part)} = {len(merged_content)} chars"
            )

            # 5. Log detalhado para debugging
            self._log_merge_details(
                last_process_in_previous,
                first_process_in_current,
                len(previous_part),
                len(current_part),
            )

            return merged_content

        except Exception as e:
            logger.error(f"❌ Erro no merge de páginas: {e}")
            return current_page_content

    def _find_last_process_in_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Encontra o último processo no conteúdo
        """
        matches = list(self.PROCESS_PATTERN.finditer(content))

        if matches:
            last_match = matches[-1]
            process_number = last_match.group(1)
            start_pos = last_match.start()

            logger.debug(
                f"🔍 Último processo encontrado: {process_number} na posição {start_pos}"
            )

            return {
                "process_number": process_number,
                "start_pos": start_pos,
                "match": last_match,
            }

        logger.debug("🔍 Nenhum processo encontrado no conteúdo")
        return None

    def _find_first_process_in_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Encontra o primeiro processo no conteúdo
        """
        match = self.PROCESS_PATTERN.search(content)

        if match:
            process_number = match.group(1)
            start_pos = match.start()

            logger.debug(
                f"🔍 Primeiro processo encontrado: {process_number} na posição {start_pos}"
            )

            return {
                "process_number": process_number,
                "start_pos": start_pos,
                "match": match,
            }

        logger.debug("🔍 Nenhum processo encontrado no conteúdo")
        return None

    def validate_merged_content(
        self, merged_content: str, expected_rpv_terms: List[str]
    ) -> bool:
        """
        Valida se o conteúdo merged contém os termos RPV esperados e tem qualidade adequada

        Args:
            merged_content: Conteúdo após merge
            expected_rpv_terms: Lista de termos que devem estar presentes

        Returns:
            True se o merge é válido, False caso contrário
        """
        logger.info("🔍 Validando qualidade do merge")

        # 1. Verificar se conteúdo não está vazio ou muito pequeno
        if not merged_content or len(merged_content.strip()) < 50:
            logger.warning("❌ Merge inválido: conteúdo muito pequeno")
            return False

        # 2. Verificar se contém pelo menos um termo RPV
        rpv_found = False
        for pattern in self.RPV_PATTERNS:
            if pattern.search(merged_content):
                rpv_found = True
                break

        if not rpv_found:
            logger.warning("❌ Merge inválido: nenhum termo RPV encontrado")
            return False

        # 3. Verificar se contém número de processo válido
        process_found = self.PROCESS_PATTERN.search(merged_content)
        if not process_found:
            logger.warning("❌ Merge inválido: nenhum número de processo encontrado")
            return False

        # 4. Verificações adicionais de qualidade
        quality_score = self._calculate_content_quality(merged_content)

        if quality_score < 0.7:  # 70% de qualidade mínima
            logger.warning(f"❌ Merge inválido: qualidade baixa ({quality_score:.2f})")
            return False

        logger.info(f"✅ Merge válido: qualidade {quality_score:.2f}")
        return True

    def _calculate_content_quality(self, content: str) -> float:
        """
        Calcula score de qualidade do conteúdo (0.0 a 1.0)
        """
        score = 0.0

        # Verificar presença de elementos esperados
        if self.PROCESS_PATTERN.search(content):
            score += 0.3  # 30% por ter processo

        if any(pattern.search(content) for pattern in self.RPV_PATTERNS):
            score += 0.3  # 30% por ter RPV

        # Verificar presença de advogado
        if re.search(r"ADV\.|advogado", content, re.IGNORECASE):
            score += 0.2  # 20% por ter advogado

        # Verificar valores monetários
        if re.search(r"R\$\s*[\d.,]+", content):
            score += 0.2  # 20% por ter valores

        return min(score, 1.0)

    def _log_merge_details(
        self,
        last_process: Dict[str, Any],
        first_process: Optional[Dict[str, Any]],
        previous_length: int,
        current_length: int,
    ):
        """
        Log detalhado do processo de merge para debugging
        """
        logger.debug("📊 Detalhes do merge:")
        logger.debug(
            f"   📋 Último processo página anterior: {last_process['process_number']}"
        )

        if first_process:
            logger.debug(
                f"   📋 Primeiro processo página atual: {first_process['process_number']}"
            )
        else:
            logger.debug("📋 Nenhum processo na página atual")

        logger.debug(f"   📏 Tamanho conteúdo anterior: {previous_length} chars")
        logger.debug(f"   📏 Tamanho conteúdo atual: {current_length} chars")
        logger.debug(
            f"   📏 Tamanho total merged: {previous_length + current_length} chars"
        )

    def get_merge_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de merge (placeholder para implementação futura)
        """
        return {
            "total_merges": 0,
            "successful_merges": 0,
            "failed_merges": 0,
            "average_merge_size": 0,
        }
