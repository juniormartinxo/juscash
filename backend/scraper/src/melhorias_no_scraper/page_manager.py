"""
Gerenciador de páginas para lidar com publicações divididas entre múltiplas páginas PDF
"""

import re
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import parse_qs, urlparse

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class DJEPageManager:
    """
    Gerencia o download e processamento de páginas PDF sequenciais do DJE
    Para casos onde publicações estão divididas entre páginas
    """

    def __init__(self, scraper_adapter):
        self.scraper_adapter = scraper_adapter
        self.page_cache = {}  # Cache para evitar downloads desnecessários
        
    async def get_previous_page_content(self, current_url: str, current_page: int) -> Optional[str]:
        """
        Baixa e extrai conteúdo da página anterior
        
        Args:
            current_url: URL da página atual
            current_page: Número da página atual
            
        Returns:
            Conteúdo da página anterior ou None se não conseguir baixar
        """
        if current_page <= 1:
            logger.info("📄 Já está na primeira página, não há página anterior")
            return None
            
        previous_page = current_page - 1
        cache_key = f"page_{previous_page}"
        
        # Verificar cache primeiro
        if cache_key in self.page_cache:
            logger.info(f"📋 Usando página {previous_page} do cache")
            return self.page_cache[cache_key]
        
        try:
            # Construir URL da página anterior
            previous_url = self._build_previous_page_url(current_url, previous_page)
            
            if not previous_url:
                logger.error(f"❌ Não foi possível construir URL da página {previous_page}")
                return None
            
            logger.info(f"📥 Baixando página anterior: {previous_page}")
            logger.debug(f"🔗 URL: {previous_url}")
            
            # Baixar página anterior usando o mesmo método do scraper
            content = await self._download_pdf_page_content(previous_url)
            
            if content:
                # Adicionar ao cache
                self.page_cache[cache_key] = content
                logger.info(f"✅ Página {previous_page} baixada e armazenada no cache ({len(content)} chars)")
                return content
            else:
                logger.warning(f"⚠️ Conteúdo vazio para página {previous_page}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao baixar página {previous_page}: {e}")
            return None

    def _build_previous_page_url(self, current_url: str, target_page: int) -> Optional[str]:
        """
        Constrói URL da página anterior baseada na URL atual
        
        Exemplo de URL DJE:
        https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710
        """
        try:
            # Usar regex para substituir nuSeqpagina
            pattern = r'nuSeqpagina=(\d+)'
            match = re.search(pattern, current_url)
            
            if match:
                previous_url = re.sub(pattern, f'nuSeqpagina={target_page}', current_url)
                logger.debug(f"🔧 URL construída: {previous_url}")
                return previous_url
            else:
                logger.error(f"❌ Padrão nuSeqpagina não encontrado na URL: {current_url}")
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
                    logger.debug(f"✅ Conteúdo extraído da página: {len(content)} chars")
                    return content
                else:
                    logger.warning("⚠️ Conteúdo muito pequeno ou vazio")
                    return None
                    
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"❌ Erro ao baixar conteúdo da página {url}: {e}")
            return None

    def extract_page_number_from_url(self, url: str) -> Optional[int]:
        """
        Extrai número da página da URL
        """
        try:
            match = re.search(r'nuSeqpagina=(\d+)', url)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.debug(f"Erro ao extrair número da página: {e}")
        return None

    def clear_cache(self):
        """Limpa cache de páginas"""
        self.page_cache.clear()
        logger.info("🧹 Cache de páginas limpo")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return {
            "cached_pages": len(self.page_cache),
            "cache_size_chars": sum(len(content) for content in self.page_cache.values()),
            "cached_page_numbers": [int(key.split("_")[1]) for key in self.page_cache.keys()]
        }


class PublicationContentMerger:
    """
    Lida com a lógica de merge de conteúdo de publicações divididas entre páginas
    """

    def __init__(self):
        self.PROCESS_PATTERN = re.compile(r'Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', re.IGNORECASE)

    def merge_cross_page_publication(
        self, 
        previous_page_content: str, 
        current_page_content: str,
        rpv_position_in_current: int
    ) -> str:
        """
        Faz merge de uma publicação que está dividida entre duas páginas
        
        Args:
            previous_page_content: Conteúdo da página anterior
            current_page_content: Conteúdo da página atual  
            rpv_position_in_current: Posição do termo RPV na página atual
            
        Returns:
            Conteúdo completo da publicação merged
        """
        try:
            # 1. Encontrar o último processo na página anterior
            last_process_in_previous = self._find_last_process_in_content(previous_page_content)
            
            if not last_process_in_previous:
                logger.warning("⚠️ Último processo não encontrado na página anterior")
                return current_page_content
            
            # 2. Extrair conteúdo da página anterior a partir do último processo
            previous_part = previous_page_content[last_process_in_previous['start_pos']:]
            
            # 3. Extrair conteúdo da página atual até antes do primeiro processo (se houver)
            first_process_in_current = self._find_first_process_in_content(current_page_content)
            
            if first_process_in_current:
                current_part = current_page_content[:first_process_in_current['start_pos']]
            else:
                current_part = current_page_content
            
            # 4. Fazer merge
            merged_content = previous_part + "\n" + current_part
            
            logger.info(f"✅ Merge concluído: {len(previous_part)} + {len(current_part)} = {len(merged_content)} chars")
            
            return merged_content
            
        except Exception as e:
            logger.error(f"❌ Erro no merge de páginas: {e}")
            return current_page_content

    def _find_last_process_in_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Encontra o último processo no conteúdo"""
        matches = list(self.PROCESS_PATTERN.finditer(content))
        
        if matches:
            last_match = matches[-1]
            return {
                'process_number': last_match.group(1),
                'start_pos': last_match.start(),
                'match': last_match
            }
        
        return None

    def _find_first_process_in_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Encontra o primeiro processo no conteúdo"""
        match = self.PROCESS_PATTERN.search(content)
        
        if match:
            return {
                'process_number': match.group(1),
                'start_pos': match.start(),
                'match': match
            }
        
        return None

    def validate_merged_content(self, merged_content: str, expected_rpv_terms: list) -> bool:
        """
        Valida se o conteúdo merged contém os termos RPV esperados
        """
        content_lower = merged_content.lower()
        
        # Verificar se contém pelo menos um dos termos RPV
        rpv_found = any(term.lower() in content_lower for term in ['rpv', 'pagamento pelo inss'])
        
        # Verificar se contém pelo menos um processo
        process_found = bool(self.PROCESS_PATTERN.search(merged_content))
        
        is_valid = rpv_found and process_found
        
        if is_valid:
            logger.info("✅ Conteúdo merged validado com sucesso")
        else:
            logger.warning(f"⚠️ Validação falhou - RPV: {rpv_found}, Processo: {process_found}")
        
        return is_valid
