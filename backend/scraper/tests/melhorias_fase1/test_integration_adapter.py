"""
🧪 TESTES INTEGRAÇÃO - FASE 3

Testes abrangentes para:
1. Integration Adapter (enhanced + legacy)
2. Enhanced Parser Integrado
3. Comparação de performance
4. Fallback automático
5. Métricas detalhadas
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import das classes a serem testadas
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.web.integration_adapter import DJEParserIntegrationAdapter
from infrastructure.web.enhanced_parser_integrated import EnhancedDJEParserIntegrated
from domain.entities.publication import Publication, Lawyer, MonetaryValue


class TestIntegrationAdapter:
    """Testes para DJEParserIntegrationAdapter"""

    @pytest.fixture
    def mock_scraper_adapter(self):
        """Mock completo do scraper adapter"""
        mock_adapter = Mock()
        mock_browser = Mock()
        mock_page = AsyncMock()

        # Configurar mocks do browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = """
        <html><body>
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita
        RPV para pagamento pelo INSS do valor de R$ 5.450,30.
        ADV. MARIA OLIVEIRA COSTA (OAB 123456/SP).
        </body></html>
        """

        mock_adapter.browser = mock_browser
        return mock_adapter

    @pytest.fixture
    def integration_adapter(self, mock_scraper_adapter):
        """Instância do Integration Adapter para testes"""
        adapter = DJEParserIntegrationAdapter(
            use_enhanced_parser=True, fallback_on_error=True, enable_metrics=True
        )
        adapter.set_scraper_adapter(mock_scraper_adapter)
        return adapter

    @pytest.fixture
    def sample_dje_content(self):
        """Conteúdo DJE simulado para testes"""
        return """
        Diário da Justiça Eletrônico - Tribunal de Justiça do Estado de São Paulo
        Caderno 3 - Judicial - 1ª Instância - Capital
        Data de Disponibilização: 17/03/2025
        
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença contra a Fazenda Pública
        - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita RPV para pagamento pelo INSS 
        do valor de R$ 5.450,30 referente a benefício previdenciário atrasado. Considerando 
        a documentação apresentada e o valor dentro do limite legal, DEFIRO o pedido de 
        expedição de Requisição de Pequeno Valor. ADV. MARIA OLIVEIRA COSTA (OAB 123456/SP). 
        Valor principal: R$ 5.450,30. Juros moratórios: R$ 150,20. Honorários advocatícios: 
        R$ 545,03. Valor líquido: R$ 5.055,07. Intimem-se. São Paulo, 17 de março de 2025.
        
        Processo 7654321-12.2024.8.26.0002 - Mandado de Segurança
        - PEDRO SOUZA ALMEIDA - Vistos. Trata-se de mandado de segurança...
        """

    def test_initialization(self, integration_adapter):
        """Testa inicialização do Integration Adapter"""
        assert integration_adapter.use_enhanced_parser is True
        assert integration_adapter.fallback_on_error is True
        assert integration_adapter.enable_metrics is True

        # Verificar se parsers foram criados
        assert integration_adapter.enhanced_parser is not None
        assert integration_adapter.legacy_parser is not None

        # Verificar se métricas foram inicializadas
        assert "enhanced_parser" in integration_adapter.metrics
        assert "legacy_parser" in integration_adapter.metrics

    def test_parser_mode_methods(self, integration_adapter):
        """Testa métodos de configuração do parser"""
        # Estado inicial
        assert integration_adapter.get_current_parser_mode() == "enhanced + fallback"

        # Desabilitar enhanced parser
        integration_adapter.disable_enhanced_parser()
        assert integration_adapter.get_current_parser_mode() == "legacy_only"

        # Reabilitar enhanced parser
        integration_adapter.enable_enhanced_parser()
        assert integration_adapter.get_current_parser_mode() == "enhanced + fallback"

        # Desabilitar fallback
        integration_adapter.disable_fallback()
        assert integration_adapter.get_current_parser_mode() == "enhanced"

    @pytest.mark.asyncio
    async def test_enhanced_parser_success(
        self, integration_adapter, sample_dje_content
    ):
        """Testa execução bem-sucedida do enhanced parser"""
        with patch.object(
            integration_adapter.enhanced_parser, "parse_multiple_publications_enhanced"
        ) as mock_parse:
            # Mock retornando publicação válida
            mock_publication = Mock(spec=Publication)
            mock_publication.process_number = "1234567-89.2024.8.26.0001"
            mock_parse.return_value = [mock_publication]

            # Mock das estatísticas
            with patch.object(
                integration_adapter.enhanced_parser, "get_extraction_statistics"
            ) as mock_stats:
                mock_stats.return_value = {
                    "merged_publications": 1,
                    "cache_stats": {"hits": 2},
                }

                # Executar
                result = await integration_adapter.parse_multiple_publications_enhanced(
                    sample_dje_content, "http://test.com", 1
                )

                # Verificar resultado
                assert len(result) == 1
                assert result[0].process_number == "1234567-89.2024.8.26.0001"

                # Verificar métricas
                assert (
                    integration_adapter.metrics["enhanced_parser"]["total_calls"] == 1
                )
                assert (
                    integration_adapter.metrics["enhanced_parser"]["successful_calls"]
                    == 1
                )
                assert (
                    integration_adapter.metrics["enhanced_parser"]["total_publications"]
                    == 1
                )

    @pytest.mark.asyncio
    async def test_fallback_activation(self, integration_adapter, sample_dje_content):
        """Testa ativação do fallback quando enhanced parser falha"""
        with patch.object(
            integration_adapter.enhanced_parser, "parse_multiple_publications_enhanced"
        ) as mock_enhanced:
            # Enhanced parser falha
            mock_enhanced.side_effect = Exception("Enhanced parser error")

            with patch.object(
                integration_adapter.legacy_parser,
                "parse_multiple_publications_enhanced",
            ) as mock_legacy:
                # Legacy parser succeed
                mock_publication = Mock(spec=Publication)
                mock_publication.process_number = "fallback-result"
                mock_legacy.return_value = [mock_publication]

                # Executar
                result = await integration_adapter.parse_multiple_publications_enhanced(
                    sample_dje_content, "http://test.com", 1
                )

                # Verificar que fallback foi ativado
                assert len(result) == 1
                assert result[0].process_number == "fallback-result"

                # Verificar métricas
                assert (
                    integration_adapter.metrics["enhanced_parser"]["failed_calls"] == 1
                )
                assert (
                    integration_adapter.metrics["legacy_parser"]["successful_calls"]
                    == 1
                )
                assert integration_adapter.metrics["fallback_activations"] == 1

    def test_comparative_metrics_calculation(self, integration_adapter):
        """Testa cálculo de métricas comparativas"""
        # Simular dados de métricas
        integration_adapter.metrics["enhanced_parser"].update(
            {
                "total_calls": 10,
                "successful_calls": 9,
                "failed_calls": 1,
                "total_publications": 15,
                "total_time": 20.0,
                "merged_publications": 3,
                "cache_hits": 12,
            }
        )

        integration_adapter.metrics["legacy_parser"].update(
            {
                "total_calls": 5,
                "successful_calls": 4,
                "failed_calls": 1,
                "total_publications": 6,
                "total_time": 15.0,
            }
        )

        integration_adapter.metrics["fallback_activations"] = 2

        # Obter métricas
        metrics = integration_adapter.get_comparative_metrics()

        # Verificar cálculos
        assert metrics["enhanced_parser"]["success_rate_percent"] == 90.0
        assert metrics["enhanced_parser"]["publications_per_call"] == 1.5
        assert metrics["enhanced_parser"]["average_execution_time"] == 2.0

        assert metrics["legacy_parser"]["success_rate_percent"] == 80.0
        assert metrics["legacy_parser"]["publications_per_call"] == 1.2
        assert metrics["legacy_parser"]["average_execution_time"] == 3.0

    def test_reset_metrics(self, integration_adapter):
        """Testa reset de métricas"""
        # Simular dados
        integration_adapter.metrics["enhanced_parser"]["total_calls"] = 10
        integration_adapter.metrics["legacy_parser"]["total_calls"] = 5
        integration_adapter.metrics["fallback_activations"] = 3

        # Reset
        integration_adapter.reset_metrics()

        # Verificar reset
        assert integration_adapter.metrics["enhanced_parser"]["total_calls"] == 0
        assert integration_adapter.metrics["legacy_parser"]["total_calls"] == 0
        assert integration_adapter.metrics["fallback_activations"] == 0


class TestEnhancedParserIntegrated:
    """Testes específicos para EnhancedDJEParserIntegrated"""

    @pytest.fixture
    def enhanced_parser(self):
        """Instância do Enhanced Parser"""
        return EnhancedDJEParserIntegrated()

    def test_initialization(self, enhanced_parser):
        """Testa inicialização do enhanced parser"""
        assert enhanced_parser.quality_threshold == 0.7
        assert enhanced_parser.max_process_search_distance == 3000
        assert enhanced_parser.stats["total_rpv_found"] == 0

    def test_rpv_patterns_detection(self, enhanced_parser):
        """Testa detecção de padrões RPV/INSS"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Teste
        Texto com RPV aqui.
        Outro texto com pagamento pelo INSS.
        Mais texto com requisição de pequeno valor.
        """

        occurrences = enhanced_parser._find_all_rpv_occurrences(content)

        assert len(occurrences) == 3
        terms = [occ["term"] for occ in occurrences]
        assert "RPV" in terms

    def test_author_extraction(self, enhanced_parser):
        """Testa extração de autores"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Teste
        - JOÃO DA SILVA SANTOS - Vistos. Texto aqui.
        - MARIA OLIVEIRA COSTA - Visto. Mais texto.
        """

        authors = enhanced_parser._extract_authors(content)

        assert len(authors) == 2

    def test_quality_calculation(self, enhanced_parser):
        """Testa cálculo de qualidade da extração"""
        # Dados completos (alta qualidade)
        complete_data = {
            "process_number": "1234567-89.2024.8.26.0001",
            "authors": ["João Silva"],
            "lawyers": [Mock(oab_number="123456")],
            "monetary_values": {"gross_value": Mock()},
            "dates": {"publication_date": datetime.now()},
        }

        quality = enhanced_parser._calculate_extraction_quality(complete_data, "")
        assert quality >= 0.9  # Qualidade alta

    def test_text_normalization(self, enhanced_parser):
        """Testa normalização de texto"""
        messy_text = "  Texto\tcom\n\nmuitos   espaços\r\n  "
        normalized = enhanced_parser._normalize_text(messy_text)

        assert normalized == "Texto com muitos espaços"


if __name__ == "__main__":
    # Executar testes específicos se necessário
    pytest.main([__file__, "-v"])
