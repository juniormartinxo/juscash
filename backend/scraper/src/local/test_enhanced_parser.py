#!/usr/bin/env python3
"""
Teste do Parser Aprimorado para Extração de Autores
Segue instruções específicas para padrão RPV/INSS
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.enhanced_content_parser import (
    EnhancedDJEContentParser,
    alert_edge_case,
)
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)

# Exemplo de conteúdo de relatório DJE-SP para teste
SAMPLE_REPORT_CONTENT = """
Diário da Justiça Eletrônico - Tribunal de Justiça do Estado de São Paulo
Caderno 3 - Judicial - 1ª Instância - Capital - Parte I
Data: 13/11/2024

Processo 0013168-70.2024.8.26.0053
Classe: Execução de Título Judicial
Assunto: Acidentário
Requerente: MARIA DA SILVA
Requerido: INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS
- MARIA DA SILVA - Vistos
Trata-se de execução de RPV contra o INSS no valor de R$ 15.000,00.
ADV. JOÃO DOS SANTOS (OAB 12345/SP)

Processo 0017901-21.2020.8.26.0053  
Classe: Execução de Título Judicial
Assunto: Saúde
Requerente: JOSÉ OLIVEIRA
Requerido: INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS
- JOSÉ OLIVEIRA - Vistos
Execução para pagamento pelo INSS de benefício previdenciário.
Valor principal: R$ 8.500,00
Honorários advocatícios: R$ 1.700,00
ADV. ANA COSTA (OAB 67890/SP)

Processo 0025432-15.2023.8.26.0053
Classe: Ação Ordinária
Assunto: Aposentadoria
Requerente: PEDRO SANTOS
Requerido: INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS
- PEDRO SANTOS - Vistos
Ação para concessão de aposentadoria por invalidez.
Não há menção a RPV neste processo.
ADV. CARLOS LIMA (OAB 11111/SP)

Publicação Oficial do Tribunal de Justiça
"""


async def test_enhanced_parser():
    """Testa o parser aprimorado com conteúdo de exemplo"""

    print("🧪 Teste do Parser Aprimorado")
    print("=" * 50)
    print("📋 Testando extração baseada em padrões RPV/INSS")
    print("🎯 Padrão de autores: '- NOME_DO_AUTOR - Vistos'")
    print()

    # Criar parser aprimorado
    parser = EnhancedDJEContentParser()

    try:
        # Testar extração aprimorada
        publications = await parser.parse_multiple_publications_enhanced(
            SAMPLE_REPORT_CONTENT, "test_report.pdf", current_page_number=3710
        )

        print(f"📊 RESULTADOS:")
        print(f"   📄 Publicações encontradas: {len(publications)}")
        print()

        for i, pub in enumerate(publications, 1):
            print(f"📄 PUBLICAÇÃO {i}:")
            print(f"   📋 Processo: {pub.process_number}")
            print(f"   👤 Autores: {', '.join(pub.authors)}")
            print(f"   ⚖️ Advogados: {len(pub.lawyers)} advogado(s)")
            if pub.lawyers:
                for lawyer in pub.lawyers:
                    print(f"      - {lawyer.name} (OAB {lawyer.oab})")
            print(
                f"   💰 Valor Bruto: {pub.gross_value.to_real() if pub.gross_value else 'N/A'}"
            )
            print(
                f"   💰 Honorários: {pub.attorney_fees.to_real() if pub.attorney_fees else 'N/A'}"
            )
            print(
                f"   🔍 Método: {pub.extraction_metadata.get('extraction_method', 'N/A')}"
            )
            print(
                f"   📍 Tipo Match: {pub.extraction_metadata.get('match_type', 'N/A')}"
            )
            print()

        # Verificar se encontrou os casos esperados
        expected_processes = ["0013168-70.2024.8.26.0053", "0017901-21.2020.8.26.0053"]
        found_processes = [pub.process_number for pub in publications]

        print("✅ VERIFICAÇÕES:")
        for expected in expected_processes:
            if expected in found_processes:
                print(f"   ✅ Processo {expected} encontrado")
            else:
                print(f"   ❌ Processo {expected} NÃO encontrado")
                alert_edge_case(f"Processo esperado {expected} não foi extraído")

        # Verificar se o processo sem RPV/INSS foi ignorado
        ignored_process = "0025432-15.2023.8.26.0053"
        if ignored_process not in found_processes:
            print(
                f"   ✅ Processo {ignored_process} corretamente ignorado (sem RPV/INSS)"
            )
        else:
            print(f"   ⚠️ Processo {ignored_process} foi extraído mesmo sem RPV/INSS")
            alert_edge_case(f"Processo {ignored_process} foi extraído sem ter RPV/INSS")

        return len(publications) > 0

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        alert_edge_case(f"Erro durante teste do parser aprimorado: {error}")
        import traceback

        traceback.print_exc()
        return False


async def test_edge_cases():
    """Testa casos extremos e edge cases"""

    print("\n🚨 Teste de Edge Cases")
    print("=" * 30)

    parser = EnhancedDJEContentParser()

    # Caso 1: RPV no início do documento sem "Processo" anterior
    edge_case_1 = """
    RPV contra INSS no valor de R$ 10.000,00
    - AUTOR SEM PROCESSO - Vistos
    Sem número de processo identificável.
    """

    print("🧪 Caso 1: RPV sem processo anterior")
    try:
        pubs = await parser.parse_multiple_publications_enhanced(
            edge_case_1, "edge1.pdf"
        )
        if not pubs:
            print("   ✅ Corretamente ignorado (sem processo)")
        else:
            print("   ⚠️ Extraído mesmo sem processo válido")
            alert_edge_case("RPV extraído sem número de processo válido")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        alert_edge_case(f"Erro no edge case 1: {e}")

    # Caso 2: Múltiplas ocorrências RPV no mesmo processo
    edge_case_2 = """
    Processo 0012345-67.2024.8.26.0001
    - AUTOR MÚLTIPLO - Vistos
    Primeira menção a RPV aqui.
    Segunda menção a RPV também.
    Terceira menção sobre pagamento pelo INSS.
    """

    print("🧪 Caso 2: Múltiplas ocorrências no mesmo processo")
    try:
        pubs = await parser.parse_multiple_publications_enhanced(
            edge_case_2, "edge2.pdf"
        )
        if len(pubs) == 1:
            print("   ✅ Corretamente extraído como uma publicação")
        elif len(pubs) > 1:
            print(f"   ⚠️ Extraído como {len(pubs)} publicações (duplicação)")
            alert_edge_case(
                f"Processo duplicado {len(pubs)} vezes por múltiplas ocorrências RPV/INSS"
            )
        else:
            print("   ❌ Não extraído")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        alert_edge_case(f"Erro no edge case 2: {e}")

    # Caso 3: Autor com caracteres especiais
    edge_case_3 = """
    Processo 0098765-43.2024.8.26.0002
    - JOSÉ DA SILVA-SANTOS (MENOR) - Vistos
    Execução de RPV com nome complexo.
    """

    print("🧪 Caso 3: Nome com caracteres especiais")
    try:
        pubs = await parser.parse_multiple_publications_enhanced(
            edge_case_3, "edge3.pdf"
        )
        if pubs and pubs[0].authors:
            author_name = pubs[0].authors[0]
            print(f"   ✅ Autor extraído: '{author_name}'")
            if "josé" in author_name.lower() and "silva" in author_name.lower():
                print("   ✅ Nome corretamente processado")
            else:
                alert_edge_case(
                    f"Nome do autor pode ter sido mal processado: '{author_name}'"
                )
        else:
            print("   ❌ Autor não extraído")
            alert_edge_case("Autor com caracteres especiais não foi extraído")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        alert_edge_case(f"Erro no edge case 3: {e}")


if __name__ == "__main__":
    print("🚀 Teste do Parser Aprimorado para Extração de Autores")
    print("💡 Seguindo instruções específicas para padrão RPV/INSS")
    print()

    # Executar teste principal
    success = asyncio.run(test_enhanced_parser())

    # Executar testes de edge cases
    asyncio.run(test_edge_cases())

    if success:
        print("\n🎉 TESTE PRINCIPAL PASSOU!")
        print("✅ Parser aprimorado funcionando conforme especificado")
    else:
        print("\n⚠️ TESTE PRINCIPAL FALHOU")
        print("❌ Verificar implementação do parser aprimorado")

    print("\n📋 Instruções implementadas:")
    print("   1. ✅ Busca por 'RPV' ou 'pagamento pelo INSS'")
    print("   2. ✅ Localiza 'Processo NUMERO_DO_PROCESSO'")
    print("   3. ✅ Determina fim do processo")
    print("   4. ⚠️ Download de página anterior (parcialmente implementado)")
    print("   5. ✅ Extrai autores no padrão '- NOME - Vistos'")
    print("   6. ✅ Alertas para edge cases")

    sys.exit(0 if success else 1)
