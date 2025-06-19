"""
🧪 TESTES UNITÁRIOS - DJE PAGE MANAGER (FASE 2)

Testes abrangentes para:
1. DJEPageManager (cache, download de páginas)
2. PublicationContentMerger (merge de conteúdo)
3. Validação de qualidade de merge
4. Performance e métricas
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import das classes a serem testadas
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.web.page_manager import DJEPageManager, PublicationContentMerger


class TestDJEPageManager:
    """Testes para DJEPageManager"""

    @pytest.fixture
    def mock_scraper_adapter(self):
        """Mock do scraper adapter"""
        mock_adapter = Mock()
        mock_browser = Mock()
        mock_adapter.browser = mock_browser
        return mock_adapter

    @pytest.fixture
    def page_manager(self, mock_scraper_adapter):
        """Instância do PageManager para testes"""
        return DJEPageManager(mock_scraper_adapter)

    def test_initialization(self, page_manager):
        """Testa inicialização do PageManager"""
        assert page_manager.page_cache == {}
        assert page_manager.cache_stats["hits"] == 0
        assert page_manager.cache_stats["misses"] == 0
        assert page_manager.cache_stats["downloads"] == 0
        assert page_manager.cache_stats["cache_size"] == 0

    def test_generate_cache_key(self, page_manager):
        """Testa geração de chave de cache"""
        url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710"
        page_number = 3709

        cache_key = page_manager._generate_cache_key(url, page_number)
        expected_key = "page_19_4092_12_3709"

        assert cache_key == expected_key

    def test_generate_cache_key_fallback(self, page_manager):
        """Testa fallback da geração de chave de cache"""
        url = "https://invalid-url-without-params"
        page_number = 1

        cache_key = page_manager._generate_cache_key(url, page_number)

        # Deve usar fallback
        assert cache_key.startswith("page_1_")
        assert len(cache_key) > 10

    def test_build_previous_page_url(self, page_manager):
        """Testa construção de URL da página anterior"""
        current_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710"
        target_page = 3709

        previous_url = page_manager._build_previous_page_url(current_url, target_page)
        expected_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3709"

        assert previous_url == expected_url

    def test_build_previous_page_url_invalid(self, page_manager):
        """Testa construção de URL com URL inválida"""
        current_url = "https://invalid-url"
        target_page = 1

        previous_url = page_manager._build_previous_page_url(current_url, target_page)

        assert previous_url is None

    def test_extract_page_number_from_url(self, page_manager):
        """Testa extração do número da página da URL"""
        url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710"

        page_number = page_manager.extract_page_number_from_url(url)

        assert page_number == 3710

    def test_extract_page_number_invalid_url(self, page_manager):
        """Testa extração com URL inválida"""
        url = "https://invalid-url"

        page_number = page_manager.extract_page_number_from_url(url)

        assert page_number is None

    @pytest.mark.asyncio
    async def test_get_previous_page_content_first_page(self, page_manager):
        """Testa tentativa de obter página anterior na primeira página"""
        result = await page_manager.get_previous_page_content("http://example.com", 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_previous_page_content_cache_hit(self, page_manager):
        """Testa cache hit"""
        # Adicionar item ao cache manualmente
        cache_key = page_manager._generate_cache_key(
            "http://example.com?nuSeqpagina=2", 1
        )
        expected_content = "cached content"
        page_manager.page_cache[cache_key] = expected_content

        result = await page_manager.get_previous_page_content(
            "http://example.com?nuSeqpagina=2", 2
        )

        assert result == expected_content
        assert page_manager.cache_stats["hits"] == 1
        assert page_manager.cache_stats["misses"] == 0

    @pytest.mark.asyncio
    async def test_get_previous_page_content_cache_miss(self, page_manager):
        """Testa cache miss com download bem-sucedido"""
        # Mock do download
        with patch.object(
            page_manager, "_download_pdf_page_content", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = "downloaded content"

            url = "http://example.com?nuSeqpagina=2"
            result = await page_manager.get_previous_page_content(url, 2)

            assert result == "downloaded content"
            assert page_manager.cache_stats["hits"] == 0
            assert page_manager.cache_stats["misses"] == 1
            assert page_manager.cache_stats["downloads"] == 1

            # Verificar se foi adicionado ao cache
            cache_key = page_manager._generate_cache_key(url, 1)
            assert page_manager.page_cache[cache_key] == "downloaded content"

    def test_get_cache_stats(self, page_manager):
        """Testa estatísticas do cache"""
        # Simular algumas operações
        page_manager.cache_stats["hits"] = 5
        page_manager.cache_stats["misses"] = 3
        page_manager.cache_stats["downloads"] = 3
        page_manager.page_cache["key1"] = "content1"
        page_manager.page_cache["key2"] = "content2"

        stats = page_manager.get_cache_stats()

        assert stats["cache_hits"] == 5
        assert stats["cache_misses"] == 3
        assert stats["total_requests"] == 8
        assert stats["hit_rate_percent"] == 62.5
        assert stats["downloads_made"] == 3
        assert stats["cache_size"] == 2
        assert "key1" in stats["cached_pages"]
        assert "key2" in stats["cached_pages"]

    def test_clear_cache(self, page_manager):
        """Testa limpeza do cache"""
        # Adicionar alguns itens ao cache
        page_manager.page_cache["key1"] = "content1"
        page_manager.page_cache["key2"] = "content2"
        page_manager.cache_stats["cache_size"] = 2

        page_manager.clear_cache()

        assert len(page_manager.page_cache) == 0
        assert page_manager.cache_stats["cache_size"] == 0

    def test_optimize_cache(self, page_manager):
        """Testa otimização do cache"""
        # Adicionar itens acima do limite
        for i in range(60):
            page_manager.page_cache[f"key{i}"] = f"content{i}"

        page_manager.optimize_cache(max_cache_size=50)

        assert len(page_manager.page_cache) == 50
        # Deve manter os itens mais recentes (implementação FIFO)
        assert "key59" in page_manager.page_cache
        assert "key0" not in page_manager.page_cache


class TestPublicationContentMerger:
    """Testes para PublicationContentMerger"""

    @pytest.fixture
    def merger(self):
        """Instância do ContentMerger para testes"""
        return PublicationContentMerger()

    def test_initialization(self, merger):
        """Testa inicialização do ContentMerger"""
        assert merger.PROCESS_PATTERN is not None
        assert len(merger.RPV_PATTERNS) == 3

    def test_find_last_process_in_content(self, merger):
        """Testa busca do último processo no conteúdo"""
        content = """
        Processo 1111111-11.2024.8.26.0001 - Primeiro processo
        Algum texto aqui
        Processo 2222222-22.2024.8.26.0002 - Segundo processo
        Mais texto
        Processo 3333333-33.2024.8.26.0003 - Último processo
        """

        result = merger._find_last_process_in_content(content)

        assert result is not None
        assert result["process_number"] == "3333333-33.2024.8.26.0003"
        assert "Último processo" in content[result["start_pos"] :]

    def test_find_first_process_in_content(self, merger):
        """Testa busca do primeiro processo no conteúdo"""
        content = """
        Algum texto inicial
        Processo 1111111-11.2024.8.26.0001 - Primeiro processo
        Processo 2222222-22.2024.8.26.0002 - Segundo processo
        """

        result = merger._find_first_process_in_content(content)

        assert result is not None
        assert result["process_number"] == "1111111-11.2024.8.26.0001"
        assert result["start_pos"] > 0

    def test_find_process_no_match(self, merger):
        """Testa busca quando não há processos"""
        content = "Texto sem processos"

        result_last = merger._find_last_process_in_content(content)
        result_first = merger._find_first_process_in_content(content)

        assert result_last is None
        assert result_first is None

    def test_merge_cross_page_publication_success(self, merger):
        """Testa merge bem-sucedido entre páginas"""
        previous_content = """
        Processo 1111111-11.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA - Vistos. O requerente solicita
        """

        current_content = """
        RPV para pagamento pelo INSS do valor de R$ 5.000,00. DEFIRO.
        ADV. MARIA SANTOS (OAB 123456/SP).
        
        Processo 2222222-22.2024.8.26.0002 - Outro processo
        """

        result = merger.merge_cross_page_publication(
            previous_content, current_content, 0
        )

        assert "Processo 1111111-11.2024.8.26.0001" in result
        assert "RPV para pagamento pelo INSS" in result
        assert "Processo 2222222-22.2024.8.26.0002" not in result
        assert len(result) > len(current_content)

    def test_merge_cross_page_no_process_in_previous(self, merger):
        """Testa merge quando não há processo na página anterior"""
        previous_content = "Texto sem processos"
        current_content = "RPV para pagamento pelo INSS"

        result = merger.merge_cross_page_publication(
            previous_content, current_content, 0
        )

        # Deve retornar apenas o conteúdo atual
        assert result == current_content

    def test_calculate_content_quality_high(self, merger):
        """Testa cálculo de qualidade alta"""
        content = """
        Processo 1111111-11.2024.8.26.0001 - Cumprimento
        RPV para pagamento pelo INSS do valor de R$ 5.000,00
        ADV. MARIA SANTOS (OAB 123456/SP)
        """

        quality = merger._calculate_content_quality(content)

        assert quality >= 0.8  # Deve ter alta qualidade

    def test_calculate_content_quality_low(self, merger):
        """Testa cálculo de qualidade baixa"""
        content = "Texto simples sem elementos esperados"

        quality = merger._calculate_content_quality(content)

        assert quality <= 0.3  # Deve ter baixa qualidade

    def test_validate_merged_content_valid(self, merger):
        """Testa validação de conteúdo merged válido"""
        content = """
        Processo 1111111-11.2024.8.26.0001 - Cumprimento de Sentença
        RPV para pagamento pelo INSS do valor de R$ 5.000,00
        ADV. MARIA SANTOS (OAB 123456/SP)
        Valor líquido: R$ 4.500,00
        """

        is_valid = merger.validate_merged_content(content, ["RPV", "INSS"])

        assert is_valid is True

    def test_validate_merged_content_invalid_empty(self, merger):
        """Testa validação de conteúdo vazio"""
        content = ""

        is_valid = merger.validate_merged_content(content, ["RPV"])

        assert is_valid is False

    def test_validate_merged_content_invalid_no_rpv(self, merger):
        """Testa validação sem termos RPV"""
        content = """
        Processo 1111111-11.2024.8.26.0001 - Algum processo
        Texto sem RPV ou INSS
        """

        is_valid = merger.validate_merged_content(content, ["RPV"])

        assert is_valid is False

    def test_validate_merged_content_invalid_no_process(self, merger):
        """Testa validação sem número de processo"""
        content = "RPV para pagamento pelo INSS sem processo"

        is_valid = merger.validate_merged_content(content, ["RPV"])

        assert is_valid is False

    def test_get_merge_statistics(self, merger):
        """Testa obtenção de estatísticas de merge"""
        stats = merger.get_merge_statistics()

        assert "total_merges" in stats
        assert "successful_merges" in stats
        assert "failed_merges" in stats
        assert "average_merge_size" in stats


class TestIntegrationPageManager:
    """Testes de integração entre PageManager e ContentMerger"""

    @pytest.fixture
    def mock_scraper_adapter(self):
        """Mock completo do scraper adapter"""
        mock_adapter = Mock()
        mock_browser = Mock()
        mock_page = AsyncMock()

        # Configurar mocks
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = """
        <html>
        <body>
        Processo 1111111-11.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA - Vistos. O requerente solicita
        </body>
        </html>
        """

        mock_adapter.browser = mock_browser
        return mock_adapter

    @pytest.fixture
    def integrated_system(self, mock_scraper_adapter):
        """Sistema integrado para testes"""
        page_manager = DJEPageManager(mock_scraper_adapter)
        content_merger = PublicationContentMerger()
        return page_manager, content_merger

    @pytest.mark.asyncio
    async def test_integrated_workflow(self, integrated_system):
        """Testa workflow integrado completo"""
        page_manager, content_merger = integrated_system

        # Simular obtenção de página anterior
        current_url = "http://example.com?nuSeqpagina=2"
        previous_content = await page_manager.get_previous_page_content(current_url, 2)

        if previous_content:
            # Simular merge com conteúdo atual
            current_content = "RPV para pagamento pelo INSS do valor de R$ 5.000,00"
            merged_content = content_merger.merge_cross_page_publication(
                previous_content, current_content, 0
            )

            # Validar resultado
            assert len(merged_content) > 0
            assert "Processo" in merged_content or "RPV" in merged_content

    def test_performance_cache_efficiency(self, integrated_system):
        """Testa eficiência do cache"""
        page_manager, _ = integrated_system

        # Simular múltiplas requisições
        for i in range(10):
            cache_key = f"test_key_{i % 3}"  # Repetir algumas chaves
            page_manager.page_cache[cache_key] = f"content_{i}"

        stats = page_manager.get_cache_stats()

        # Verificar que cache está funcionando
        assert stats["cache_size"] == 3  # Apenas 3 chaves únicas
        assert len(page_manager.page_cache) == 3


if __name__ == "__main__":
    # Executar testes específicos se necessário
    pytest.main([__file__, "-v"])
