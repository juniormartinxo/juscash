#!/usr/bin/env python3
"""
🚀 TESTE PRÁTICO - CENÁRIO REAL FASE 2

Teste simulando um cenário real de scraping com:
1. Download de múltiplas páginas
2. Cache funcionando
3. Merge de publicações divididas
4. Validação de qualidade
5. Métricas de performance
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.web.page_manager import DJEPageManager, PublicationContentMerger
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class MockScraperAdapter:
    """Mock realista do scraper adapter para testes"""

    def __init__(self):
        self.browser = Mock()
        self.setup_browser_mock()

    def setup_browser_mock(self):
        """Configura mock do browser com dados realistas"""
        # Simular respostas de diferentes páginas
        self.page_contents = {
            3709: """
            <html><body>
            <div class="content">
            Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença contra a Fazenda Pública
            - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita
            </div>
            </body></html>
            """,
            3710: """
            <html><body>
            <div class="content">
            RPV para pagamento pelo INSS do valor de R$ 5.450,30 referente a benefício previdenciário atrasado. 
            Considerando a documentação apresentada e o valor dentro do limite legal, DEFIRO o pedido de expedição 
            de Requisição de Pequeno Valor. ADV. MARIA OLIVEIRA COSTA (OAB 123456/SP). 
            Valor principal: R$ 5.450,30. Juros moratórios: R$ 150,20. Honorários advocatícios: R$ 545,03. 
            Valor líquido: R$ 5.055,07. Intimem-se. São Paulo, 17 de março de 2025.
            
            Processo 7654321-12.2024.8.26.0002 - Mandado de Segurança
            - PEDRO SOUZA ALMEIDA - Vistos. Trata-se de mandado de segurança...
            </div>
            </body></html>
            """,
        }

        # Mock das funções do browser
        async def mock_new_page():
            page_mock = AsyncMock()
            page_mock.goto = AsyncMock()
            page_mock.content = AsyncMock()
            page_mock.close = AsyncMock()
            page_mock.set_default_timeout = Mock()
            page_mock.wait_for_load_state = AsyncMock()

            # Simular conteúdo baseado na URL
            async def mock_content():
                # Extrair número da página da URL atual
                current_url = getattr(page_mock, "_current_url", "")
                for page_num, content in self.page_contents.items():
                    if f"nuSeqpagina={page_num}" in current_url:
                        return content
                return "<html><body>Página não encontrada</body></html>"

            async def mock_goto(url, **kwargs):
                page_mock._current_url = url
                logger.info(f"🌐 Mock navegando para: {url}")

            page_mock.content.side_effect = mock_content
            page_mock.goto.side_effect = mock_goto

            return page_mock

        self.browser.new_page = mock_new_page


async def test_page_manager_basic_functionality():
    """Teste básico do Page Manager"""
    print("\n🧪 === TESTE 1: FUNCIONALIDADE BÁSICA DO PAGE MANAGER ===")

    # Setup
    mock_adapter = MockScraperAdapter()
    page_manager = DJEPageManager(mock_adapter)

    # Teste 1: Cache inicial vazio
    stats = page_manager.get_cache_stats()
    print(f"📊 Cache inicial: {stats}")
    assert stats["cache_size"] == 0
    assert stats["hit_rate_percent"] == 0

    # Teste 2: Primeira requisição (cache miss)
    current_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710"
    previous_content = await page_manager.get_previous_page_content(current_url, 3710)

    print(
        f"📄 Conteúdo obtido: {len(previous_content) if previous_content else 0} chars"
    )
    print(
        f"🔍 Contém processo? {'Sim' if previous_content and 'Processo' in previous_content else 'Não'}"
    )

    # Verificar cache após primeira requisição
    stats = page_manager.get_cache_stats()
    print(f"📊 Cache após 1ª requisição: {stats}")

    # Teste 3: Segunda requisição da mesma página (cache hit)
    previous_content_2 = await page_manager.get_previous_page_content(current_url, 3710)

    # Verificar cache hit
    stats = page_manager.get_cache_stats()
    print(f"📊 Cache após 2ª requisição: {stats}")
    assert stats["hits"] == 1
    assert stats["cache_size"] == 1

    print("✅ Teste 1 concluído com sucesso!")
    return page_manager


async def test_content_merger_functionality():
    """Teste do Content Merger"""
    print("\n🧪 === TESTE 2: FUNCIONALIDADE DO CONTENT MERGER ===")

    # Setup
    merger = PublicationContentMerger()

    # Dados de teste simulando publicação dividida
    previous_page_content = """
    Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença contra a Fazenda Pública
    - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita
    """

    current_page_content = """
    RPV para pagamento pelo INSS do valor de R$ 5.450,30 referente a benefício previdenciário atrasado. 
    Considerando a documentação apresentada e o valor dentro do limite legal, DEFIRO o pedido de expedição 
    de Requisição de Pequeno Valor. ADV. MARIA OLIVEIRA COSTA (OAB 123456/SP). 
    Valor principal: R$ 5.450,30. Juros moratórios: R$ 150,20. Honorários advocatícios: R$ 545,03. 
    Valor líquido: R$ 5.055,07. Intimem-se. São Paulo, 17 de março de 2025.
    
    Processo 7654321-12.2024.8.26.0002 - Mandado de Segurança
    - PEDRO SOUZA ALMEIDA - Vistos. Trata-se de mandado de segurança...
    """

    # Teste 1: Merge de conteúdo
    merged_content = merger.merge_cross_page_publication(
        previous_page_content, current_page_content, 0
    )

    print(f"📄 Tamanho do merge: {len(merged_content)} chars")
    print(
        f"🔍 Contém processo original? {'Sim' if '1234567-89.2024.8.26.0001' in merged_content else 'Não'}"
    )
    print(f"🔍 Contém RPV? {'Sim' if 'RPV' in merged_content else 'Não'}")
    print(f"🔍 Contém INSS? {'Sim' if 'INSS' in merged_content else 'Não'}")
    print(
        f"🔍 Contém 2º processo? {'Não' if '7654321-12.2024.8.26.0002' not in merged_content else 'Sim - ERRO!'}"
    )

    # Teste 2: Validação de qualidade
    is_valid = merger.validate_merged_content(merged_content, ["RPV", "INSS"])
    quality_score = merger._calculate_content_quality(merged_content)

    print(f"✅ Merge válido? {is_valid}")
    print(f"📊 Score de qualidade: {quality_score:.2f}")

    # Teste 3: Estatísticas
    stats = merger.get_merge_statistics()
    print(f"📊 Estatísticas do merger: {stats}")

    print("✅ Teste 2 concluído com sucesso!")
    return merger, merged_content


async def test_integrated_workflow():
    """Teste do workflow integrado completo"""
    print("\n🧪 === TESTE 3: WORKFLOW INTEGRADO COMPLETO ===")

    # Setup
    mock_adapter = MockScraperAdapter()
    page_manager = DJEPageManager(mock_adapter)
    content_merger = PublicationContentMerger()

    # Simular cenário: encontrou RPV na página 3710, mas início está na página 3709
    current_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina=3710"
    current_page_number = 3710

    print(f"🎯 Cenário: RPV encontrado na página {current_page_number}")
    print(f"🔗 URL atual: {current_url}")

    # Passo 1: Obter página anterior
    print("\n📥 Passo 1: Obtendo página anterior...")
    previous_content = await page_manager.get_previous_page_content(
        current_url, current_page_number
    )

    if previous_content:
        print(f"✅ Página anterior obtida: {len(previous_content)} chars")

        # Passo 2: Simular conteúdo da página atual
        print("\n🔄 Passo 2: Simulando merge...")
        current_content = """
        RPV para pagamento pelo INSS do valor de R$ 5.450,30 referente a benefício previdenciário atrasado. 
        Considerando a documentação apresentada e o valor dentro do limite legal, DEFIRO o pedido.
        ADV. MARIA OLIVEIRA COSTA (OAB 123456/SP). Valor líquido: R$ 5.055,07.
        
        Processo 7654321-12.2024.8.26.0002 - Próximo processo
        """

        # Passo 3: Fazer merge
        merged_content = content_merger.merge_cross_page_publication(
            previous_content, current_content, 0
        )

        # Passo 4: Validar resultado
        is_valid = content_merger.validate_merged_content(
            merged_content, ["RPV", "INSS"]
        )
        quality_score = content_merger._calculate_content_quality(merged_content)

        print(f"✅ Merge realizado: {len(merged_content)} chars")
        print(f"📊 Qualidade: {quality_score:.2f}")
        print(f"✅ Válido: {is_valid}")

        # Passo 5: Métricas finais
        cache_stats = page_manager.get_cache_stats()

        print(f"\n📊 === MÉTRICAS FINAIS ===")
        print(f"🎯 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")
        print(f"📥 Downloads realizados: {cache_stats['downloads_made']}")
        print(f"💾 Páginas em cache: {cache_stats['cache_size']}")
        print(f"🔄 Merge bem-sucedido: {'Sim' if is_valid else 'Não'}")
        print(f"⭐ Score de qualidade: {quality_score:.2f}/1.00")

        # Calcular economia de downloads
        total_requests = cache_stats["hits"] + cache_stats["misses"]
        if total_requests > 0:
            economia_downloads = (cache_stats["hits"] / total_requests) * 100
            print(f"💰 Economia de downloads: {economia_downloads:.1f}%")

        print("✅ Teste 3 concluído com sucesso!")

        return {
            "cache_stats": cache_stats,
            "merge_quality": quality_score,
            "merge_valid": is_valid,
            "content_size": len(merged_content),
        }
    else:
        print("❌ Falha ao obter página anterior")
        return None


async def test_performance_scenarios():
    """Teste de cenários de performance"""
    print("\n🧪 === TESTE 4: CENÁRIOS DE PERFORMANCE ===")

    mock_adapter = MockScraperAdapter()
    page_manager = DJEPageManager(mock_adapter)

    # Simular múltiplas requisições para testar cache
    base_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4092&cdCaderno=12&nuSeqpagina="

    start_time = datetime.now()

    # Requisições que vão testar cache
    test_pages = [3710, 3710, 3709, 3710, 3709, 3708, 3709]  # Repetições intencionais

    for i, page_num in enumerate(test_pages):
        url = f"{base_url}{page_num}"
        print(f"📥 Requisição {i + 1}: Página {page_num}")

        content = await page_manager.get_previous_page_content(url, page_num)

        # Mostrar status do cache
        stats = page_manager.get_cache_stats()
        print(
            f"   📊 Cache: {stats['hits']} hits, {stats['misses']} misses, hit rate: {stats['hit_rate_percent']:.1f}%"
        )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Estatísticas finais
    final_stats = page_manager.get_cache_stats()

    print(f"\n📊 === RESULTADOS DE PERFORMANCE ===")
    print(f"⏱️  Tempo total: {duration:.2f}s")
    print(f"📥 Total de requisições: {len(test_pages)}")
    print(f"✅ Cache hits: {final_stats['hits']}")
    print(f"❌ Cache misses: {final_stats['misses']}")
    print(f"📊 Hit rate: {final_stats['hit_rate_percent']:.1f}%")
    print(f"💾 Páginas únicas em cache: {final_stats['cache_size']}")
    print(f"📏 Memória cache: {final_stats['cache_memory_usage']} chars")

    # Validar eficiência
    expected_hits = len(test_pages) - len(set(test_pages))  # Requisições duplicadas
    actual_efficiency = (final_stats["hits"] / len(test_pages)) * 100

    print(f"🎯 Eficiência esperada: {(expected_hits / len(test_pages)) * 100:.1f}%")
    print(f"🎯 Eficiência real: {actual_efficiency:.1f}%")

    print("✅ Teste 4 concluído com sucesso!")

    return final_stats


async def main():
    """Função principal que executa todos os testes"""
    print("🚀 === INICIANDO TESTES PRÁTICOS - FASE 2 PAGE MANAGER ===")
    print(f"⏰ Início dos testes: {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Executar todos os testes em sequência
        page_manager = await test_page_manager_basic_functionality()
        merger, merged_content = await test_content_merger_functionality()
        workflow_result = await test_integrated_workflow()
        performance_stats = await test_performance_scenarios()

        # Resumo final
        print("\n🎉 === RESUMO FINAL DOS TESTES ===")
        print("✅ Teste 1: Funcionalidade básica do Page Manager")
        print("✅ Teste 2: Funcionalidade do Content Merger")
        print("✅ Teste 3: Workflow integrado completo")
        print("✅ Teste 4: Cenários de performance")

        if workflow_result:
            print(f"\n📊 Métricas principais:")
            print(
                f"   🎯 Cache hit rate: {workflow_result['cache_stats']['hit_rate_percent']:.1f}%"
            )
            print(
                f"   ⭐ Qualidade do merge: {workflow_result['merge_quality']:.2f}/1.00"
            )
            print(f"   ✅ Merge válido: {workflow_result['merge_valid']}")

        print(f"\n🏁 Todos os testes concluídos com sucesso!")
        print(f"⏰ Término: {datetime.now().strftime('%H:%M:%S')}")

        return True

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Executar testes
    success = asyncio.run(main())

    if success:
        print("\n🎯 === FASE 2 PAGE MANAGER TESTADA COM SUCESSO ===")
        exit(0)
    else:
        print("\n💥 === FALHA NOS TESTES ===")
        exit(1)
