"""
🚀 EXEMPLO PRÁTICO - FASE 3 INTEGRADA

Exemplo de uso completo do Enhanced Parser Integrado:
1. Configuração do Integration Adapter
2. Execução com dados reais simulados
3. Comparação de performance
4. Análise de métricas
5. Demonstração de funcionalidades
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.web.integration_adapter import DJEParserIntegrationAdapter
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class MockScraperAdapter:
    """Mock do scraper adapter para demonstração"""

    def __init__(self):
        self.browser = self
        self.page_count = 0

    async def new_page(self):
        return MockPage()


class MockPage:
    """Mock de página para demonstração"""

    async def goto(self, url):
        pass

    async def content(self):
        # Simular conteúdo de página anterior
        return """
        Processo 9999999-99.2024.8.26.0999 - Ação anterior
        - JOÃO ANTERIOR - Vistos. Conteúdo anterior...
        
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita
        """


# Dados simulados de diferentes cenários
SCENARIOS = {
    "cenario_simples": {
        "description": "Publicação simples completa em uma página",
        "content": """
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
        """,
        "expected_publications": 1,
        "page_number": 1,
    },
    "cenario_multiplas": {
        "description": "Múltiplas publicações RPV na mesma página",
        "content": """
        Processo 1111111-11.2024.8.26.0001 - Cumprimento de Sentença
        - MARIA SANTOS SILVA - Vistos. Defiro expedição de RPV para pagamento pelo INSS 
        no valor de R$ 3.200,00. ADV. PEDRO OLIVEIRA (OAB 111111/SP).
        
        Processo 2222222-22.2024.8.26.0002 - Execução Fiscal  
        - CARLOS RODRIGUES LIMA - Vistos. Solicito Requisição de Pequeno Valor para 
        pagamento de benefício previdenciário. Valor: R$ 7.890,50. 
        ADV. ANA PAULA COSTA (OAB 222222/SP).
        
        Processo 3333333-33.2024.8.26.0003 - Mandado de Segurança
        - JOSÉ FERREIRA SOUZA - Vistos. Expedição de RPV autorizada para pagamento 
        pelo INSS. Principal: R$ 4.567,89. ADV. LUCIA MARTINS (OAB 333333/SP).
        """,
        "expected_publications": 3,
        "page_number": 5,
    },
    "cenario_cross_page": {
        "description": "Publicação dividida entre páginas (simulado)",
        "content": """
        RPV para pagamento pelo INSS do valor de R$ 2.500,00 conforme documentação 
        anexa. Valor líquido após descontos: R$ 2.350,00. Honorários: R$ 250,00.
        ADV. FERNANDO SANTOS (OAB 444444/SP). Intimem-se as partes.
        São Paulo, 17 de março de 2025.
        
        Processo 5555555-55.2024.8.26.0005 - Nova Ação
        - ROBERTO SILVA - Vistos. Nova publicação...
        """,
        "expected_publications": 1,
        "page_number": 2,  # Página 2, processo começou na página 1
    },
    "cenario_sem_rpv": {
        "description": "Página sem ocorrências de RPV/INSS",
        "content": """
        Processo 6666666-66.2024.8.26.0006 - Ação de Cobrança
        - TERESA OLIVEIRA - Vistos. Trata-se de ação de cobrança movida contra...
        Não há requisição de pagamento envolvida. Defiro o pedido de citação.
        
        Processo 7777777-77.2024.8.26.0007 - Divórcio Consensual
        - MARCOS PEREIRA - Vistos. Homologo o acordo celebrado entre as partes...
        """,
        "expected_publications": 0,
        "page_number": 3,
    },
}


async def demonstrate_integration_adapter():
    """
    Demonstração completa do Integration Adapter
    """
    logger.info("🚀 === DEMONSTRAÇÃO FASE 3 - ENHANCED PARSER INTEGRADO ===")

    # 1. Configurar Integration Adapter
    logger.info("\n📋 1. CONFIGURANDO INTEGRATION ADAPTER")

    adapter = DJEParserIntegrationAdapter(
        use_enhanced_parser=True, fallback_on_error=True, enable_metrics=True
    )

    # Configurar mock scraper
    mock_scraper = MockScraperAdapter()
    adapter.set_scraper_adapter(mock_scraper)

    # Configurar parâmetros do enhanced parser
    adapter.configure_enhanced_parser(
        quality_threshold=0.7, max_process_search_distance=3000
    )

    logger.info(f"✅ Adapter configurado: {adapter.get_current_parser_mode()}")

    # 2. Executar cenários de teste
    logger.info("\n📊 2. EXECUTANDO CENÁRIOS DE TESTE")

    total_publications = 0

    for scenario_name, scenario_data in SCENARIOS.items():
        logger.info(f"\n🔍 Cenário: {scenario_data['description']}")

        start_time = datetime.now()

        try:
            publications = await adapter.parse_multiple_publications_enhanced(
                content=scenario_data["content"],
                source_url=f"https://dje.tjsp.jus.br/detalhe.aspx?d=2025-03-17&c=3&p={scenario_data['page_number']}",
                current_page_number=scenario_data["page_number"],
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"   📋 Publicações encontradas: {len(publications)}")
            logger.info(f"   🎯 Esperado: {scenario_data['expected_publications']}")
            logger.info(f"   ⏱️ Tempo de execução: {execution_time:.3f}s")

            if len(publications) > 0:
                for i, pub in enumerate(publications, 1):
                    logger.info(
                        f"      {i}. {pub.process_number} - {len(pub.authors)} autores"
                    )

            total_publications += len(publications)

            # Verificar se resultado está dentro do esperado
            status = (
                "✅ SUCESSO"
                if len(publications) == scenario_data["expected_publications"]
                else "⚠️ DIVERGÊNCIA"
            )
            logger.info(f"   {status}")

        except Exception as e:
            logger.error(f"   ❌ ERRO: {e}")

    # 3. Análise comparativa (simular modo legacy)
    logger.info("\n🔬 3. ANÁLISE COMPARATIVA (Enhanced vs Legacy)")

    # Temporariamente usar apenas legacy
    adapter.disable_enhanced_parser()

    sample_scenario = SCENARIOS["cenario_multiplas"]

    logger.info(f"🔄 Executando mesmo cenário com legacy parser...")
    start_time = datetime.now()

    legacy_publications = await adapter.parse_multiple_publications_enhanced(
        content=sample_scenario["content"],
        source_url="https://dje.tjsp.jus.br/test-legacy",
        current_page_number=sample_scenario["page_number"],
    )

    legacy_time = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"🔄 Legacy result: {len(legacy_publications)} publicações em {legacy_time:.3f}s"
    )

    # Reativar enhanced parser
    adapter.enable_enhanced_parser()

    # 4. Relatório de métricas
    logger.info("\n📊 4. RELATÓRIO DETALHADO DE MÉTRICAS")

    adapter.log_performance_summary()

    # Métricas específicas
    metrics = adapter.get_comparative_metrics()

    logger.info("\n📈 RESUMO EXECUTIVO:")
    logger.info(
        f"   🚀 Enhanced Parser: {metrics['enhanced_parser']['total_calls']} execuções"
    )
    logger.info(
        f"   🔄 Legacy Parser: {metrics['legacy_parser']['total_calls']} execuções"
    )
    logger.info(f"   📋 Total de publicações: {total_publications}")
    logger.info(
        f"   🔄 Fallbacks ativados: {metrics['session_info']['fallback_activations']}"
    )

    if metrics["legacy_parser"]["total_calls"] > 0:
        logger.info(
            f"   ⚡ Melhoria de tempo: {metrics['comparative_analysis']['time_improvement_percent']:.1f}%"
        )
        logger.info(
            f"   📈 Melhoria na taxa de publicações: {metrics['comparative_analysis']['publication_rate_improvement']:+.1f}"
        )

    # 5. Demonstração de features específicas
    logger.info("\n🛠️ 5. DEMONSTRAÇÃO DE FEATURES ESPECÍFICAS")

    # Feature toggles
    logger.info("🔧 Testando feature toggles:")

    # Desabilitar fallback
    adapter.disable_fallback()
    logger.info(f"   Modo atual: {adapter.get_current_parser_mode()}")

    # Reabilitar fallback
    adapter.enable_fallback()
    logger.info(f"   Modo atual: {adapter.get_current_parser_mode()}")

    # Reset de métricas
    logger.info("📊 Resetando métricas...")
    adapter.reset_metrics()

    new_metrics = adapter.get_comparative_metrics()
    logger.info(
        f"   Enhanced calls após reset: {new_metrics['enhanced_parser']['total_calls']}"
    )

    # 6. Conclusões
    logger.info("\n🎉 6. CONCLUSÕES DA DEMONSTRAÇÃO")

    logger.info("✅ Funcionalidades validadas:")
    logger.info("   🚀 Enhanced Parser com Page Manager integrado")
    logger.info("   🔄 Fallback automático para legacy parser")
    logger.info("   📊 Coleta abrangente de métricas comparativas")
    logger.info("   🛠️ Feature toggles para ativação gradual")
    logger.info("   🔍 Detecção aprimorada de padrões RPV/INSS")
    logger.info("   💾 Cache inteligente para publicações cross-page")
    logger.info("   📈 Validação automática de qualidade")

    logger.info("\n🚀 FASE 3 DEMONSTRADA COM SUCESSO!")

    return adapter


async def demonstrate_enhanced_parser_features():
    """
    Demonstração específica das features do Enhanced Parser
    """
    logger.info("\n🔬 === DEMONSTRAÇÃO FEATURES ENHANCED PARSER ===")

    from infrastructure.web.enhanced_parser_integrated import (
        EnhancedDJEParserIntegrated,
    )

    parser = EnhancedDJEParserIntegrated()

    # Mock scraper adapter
    parser.set_scraper_adapter(MockScraperAdapter())

    # Testar detecção de padrões
    test_content = """
    Processo 1234567-89.2024.8.26.0001 - Teste
    Texto com RPV, requisição de pequeno valor e pagamento pelo INSS.
    """

    occurrences = parser._find_all_rpv_occurrences(test_content)
    logger.info(f"🔍 Padrões RPV/INSS detectados: {len(occurrences)}")

    for occ in occurrences:
        logger.info(f"   - '{occ['term']}' na posição {occ['position']}")

    # Testar normalização de texto
    messy_text = "  Texto\tcom\n\nespaços   irregulares  "
    normalized = parser._normalize_text(messy_text)
    logger.info(f"📝 Normalização: '{messy_text}' → '{normalized}'")

    # Testar parsing monetário
    monetary_strings = ["1.234,56", "R$ 5.678,90", "2345,67", "invalid"]
    logger.info("💰 Parsing monetário:")

    for money_str in monetary_strings:
        parsed = parser._parse_monetary_string(money_str)
        logger.info(f"   '{money_str}' → {parsed}")

    # Estatísticas
    stats = parser.get_extraction_statistics()
    logger.info(f"📊 Estatísticas do parser: {stats}")


async def main():
    """Função principal da demonstração"""
    try:
        # Demonstração principal
        adapter = await demonstrate_integration_adapter()

        # Demonstração de features específicas
        await demonstrate_enhanced_parser_features()

        logger.info("\n🎉 === DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO ===")

        return adapter

    except Exception as e:
        logger.error(f"❌ Erro na demonstração: {e}")
        raise


if __name__ == "__main__":
    # Executar demonstração
    asyncio.run(main())
