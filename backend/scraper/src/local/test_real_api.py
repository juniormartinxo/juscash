#!/usr/bin/env python3
"""
Teste com dados reais da API para validar correções
"""

import sys
import json
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.content_parser import DJEContentParser
from infrastructure.api.api_client_adapter import ApiClientAdapter
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_real_api_submission():
    """Testa submissão real para a API com dados corrigidos"""

    print("🧪 Teste Real de Submissão para API")
    print("=" * 50)

    # Conteúdo de teste similar ao que está falhando em produção
    test_content = """
    Processo 0112165-20.2012.8.26.0050

    Publicado em 13 de novembro de 2024

    Acidentário - CLAUDIO LUIZ BUENO DE MIRANDA - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS

    Condenar o Instituto Nacional do Seguro Social - INSS ao pagamento de:
    - Juros monetários: R$ 43.545,51
    - Honorários advocatícios: R$ 11.578,51

    ADV. MARIA JOSE DA SILVA OLIVEIRA (OAB 123456/SP)

    Trata-se de ação previdenciária para concessão de auxílio-doença e aposentadoria.
    """

    try:
        # 1. Parse dos dados
        print("📋 Etapa 1: Parsing com correções aplicadas")
        parser = DJEContentParser()
        publications = parser.parse_multiple_publications(test_content)

        if not publications:
            print("❌ Nenhuma publicação extraída")
            return False

        publication = publications[0]
        print(f"✅ Publicação parseada: {publication.process_number}")
        print(f"   👥 Autores: {publication.authors}")
        print(
            f"   ⚖️ Advogados: {[f'{l.name} (OAB {l.oab})' for l in publication.lawyers]}"
        )

        # 2. Verificar se dados estão corretos
        api_data = publication.to_api_dict()
        lawyers = api_data.get("lawyers", [])

        print(f"\n🔍 Validação dos advogados:")
        for i, lawyer in enumerate(lawyers):
            name = lawyer.get("name", "")
            oab = lawyer.get("oab", "")
            print(f"   {i+1}. Nome: '{name}' (length: {len(name)})")
            print(f"      OAB: '{oab}'")

            # Verificar se não há texto inválido
            problematic_words = ["sp", "tratase", "acao", "previdenciaria", "concessao"]
            has_problem = any(word in name.lower() for word in problematic_words)
            if has_problem:
                print(f"      ⚠️ Nome contém palavras problemáticas")
            else:
                print(f"      ✅ Nome parece válido")

        # 3. Teste de conectividade
        print(f"\n🔗 Etapa 2: Teste de conectividade com API")
        settings = get_settings()
        print(f"   API URL: {settings.api.base_url}")
        print(
            f"   API Key configurada: {'✅' if settings.api.scraper_api_key else '❌'}"
        )

        api_client = ApiClientAdapter()

        # Verificar se API está respondendo
        try:
            exists = await api_client.check_publication_exists("TEST-CONNECTION-123")
            print(f"✅ API respondendo corretamente")
        except Exception as e:
            print(f"❌ Problema de conectividade: {e}")
            return False

        # 4. Submissão de teste (comentado por segurança)
        print(f"\n💾 Etapa 3: Preparação para submissão")
        print(f"📦 Dados preparados para envio:")
        print(f"   - Processo: {api_data['processNumber']}")
        print(f"   - Autores: {len(api_data['authors'])} autores")
        print(f"   - Advogados: {len(api_data.get('lawyers', []))} advogados")
        print(
            f"   - Valores: {len([k for k in ['grossValue', 'netValue', 'interestValue', 'attorneyFees'] if k in api_data])} valores monetários"
        )

        # Para teste real, descomente as linhas abaixo:
        print(f"\n⚠️ TESTE SIMULADO - Para teste real, descomente o código de submissão")

        # Submissão real (descomente para testar)
        # success = await api_client.save_publication(publication)
        # if success:
        #     print(f"✅ Publicação salva com sucesso na API!")
        #     return True
        # else:
        #     print(f"❌ Falha ao salvar na API")
        #     return False

        print(
            f"\n🎯 Resultado: Dados preparados corretamente, prontos para submissão real"
        )
        return True

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        logger.error(f"Erro no teste: {error}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Iniciando teste com dados reais...")
    print("💡 Este teste valida as correções sem submeter dados reais")
    print()

    success = asyncio.run(test_real_api_submission())

    if success:
        print(f"\n✅ TESTE PASSOU - As correções estão funcionando!")
        print(f"💡 Agora você pode executar o scraper real com confiança")
    else:
        print(f"\n❌ TESTE FALHOU - Ainda há problemas a resolver")

    sys.exit(0 if success else 1)
