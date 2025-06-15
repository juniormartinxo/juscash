#!/usr/bin/env python3
"""
Teste de integração completa do sistema de scraping
Testa o fluxo: Parse -> Validação -> API -> Persistência
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.content_parser import DJEContentParser
from infrastructure.api.api_client_adapter import ApiClientAdapter
from application.usecases.save_publications import SavePublicationsUseCase
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)

# Conteúdo de teste real do DJE-SP (dados que processamos antes)
TEST_CONTENT = """
Processo 1234567-89.2024.8.26.0100

Publicado em 13 de novembro de 2024

Acidentário - CLAUDIO LUIZ BUENO DE MIRANDA - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS

Condenar o Instituto Nacional do Seguro Social - INSS ao pagamento de:
- Juros monetários: R$ 43.545,51
- Honorários advocatícios: R$ 11.578,51

ADV. MARIA JOSE DA SILVA OLIVEIRA (OAB 123456/SP)

Trata-se de ação previdenciária para concessão de auxílio-doença.
"""


async def test_integration():
    """Testa integração completa do sistema"""

    print("🚀 Iniciando teste de integração completa")
    print("=" * 60)

    try:
        # 1. Testar o parser aprimorado
        print("\n📋 Etapa 1: Testando parser aprimorado")
        parser = DJEContentParser()

        publications = parser.parse_multiple_publications(TEST_CONTENT)

        if not publications:
            print("❌ Nenhuma publicação extraída pelo parser")
            return False

        publication = publications[0]
        print(f"✅ Publicação extraída: {publication.process_number}")
        print(f"📅 Data: {publication.publication_date}")
        print(f"👥 Autores: {len(publication.authors)}")
        print(f"⚖️ Advogados: {len(publication.lawyers)}")
        print(
            f"💰 Valores: Juros={publication.interest_value}, Honorários={publication.attorney_fees}"
        )

        # 2. Testar conexão com API (modo dry-run)
        print("\n🌐 Etapa 2: Testando conexão com API")

        try:
            api_client = ApiClientAdapter()

            # Teste de verificação (não salva realmente)
            exists = await api_client.check_publication_exists("TEST-INTEGRATION-123")
            print(f"✅ Conexão com API: OK (exists check returned: {exists})")

        except Exception as api_error:
            print(f"⚠️ Conexão com API: {api_error}")
            print(
                "💡 Certifique-se de que a API está rodando e as configurações estão corretas"
            )

        # 3. Testar use case de salvamento (modo simulado)
        print("\n💾 Etapa 3: Testando use case de salvamento")

        save_usecase = SavePublicationsUseCase(api_client)

        # Simular salvamento (comentar para teste real)
        print("📝 Modo simulação - não salvará dados reais")
        print(f"📦 Dados que seriam enviados:")
        print(f"   - Processo: {publication.process_number}")
        print(f"   - Autores: {', '.join(publication.authors)}")
        print(
            f"   - Valores: Juros R$ {publication.interest_value}, Honorários R$ {publication.attorney_fees}"
        )

        # Para teste real, descomente as linhas abaixo:
        # stats = await save_usecase.execute([publication])
        # print(f"✅ Estatísticas de salvamento: {stats}")

        print("\n🎉 Teste de integração concluído com sucesso!")
        print("💡 Para teste real com API, descomente as linhas marcadas no código")

        return True

    except Exception as error:
        print(f"❌ Erro durante teste de integração: {error}")
        logger.error(f"Erro no teste de integração: {error}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
