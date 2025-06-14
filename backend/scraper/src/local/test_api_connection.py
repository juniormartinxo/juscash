"""
Script para testar conexão com a API
"""

import asyncio
import os
from datetime import datetime

from src.local.load_root_dotenv import get_dotenv_path
from dotenv import load_dotenv
from src.domain.entities.publication import Publication, Lawyer, MonetaryValue
from src.infrastructure.api.api_client_adapter import ApiClientAdapter
from src.infrastructure.logging.logger import setup_logger

load_dotenv(get_dotenv_path())

logger = setup_logger(__name__)


async def test_api_connection():
    """Testa a conexão com a API"""
    logger.info("🧪 Iniciando teste de conexão com a API")

    # Verificar se API Key está configurada
    api_key = os.getenv("SCRAPER_API_KEY")
    if not api_key or api_key == "sua_chave_aqui":
        logger.warning("⚠️  SCRAPER_API_KEY não configurada ou usando valor padrão")
        logger.info("💡 Continuando teste mesmo sem API key válida...")
    else:
        logger.info(f"🔑 API Key configurada: {api_key[:8]}...")

    # Criar cliente API
    api_client = ApiClientAdapter()

    # Criar publicação de teste
    test_publication = Publication(
        process_number=f"TEST-{int(datetime.now().timestamp())}-89.2024.8.26.0100",
        publication_date=datetime(2024, 3, 15),
        availability_date=datetime.now(),
        authors=["João Silva Santos - TESTE", "Maria Oliveira - TESTE"],
        lawyers=[
            Lawyer(name="Dr. Carlos Advogado - TESTE", oab="123456"),
            Lawyer(name="Dra. Ana Jurista - TESTE", oab="789012"),
        ],
        gross_value=MonetaryValue.from_real(1500.00),
        net_value=MonetaryValue.from_real(1350.00),
        interest_value=MonetaryValue.from_real(100.00),
        attorney_fees=MonetaryValue.from_real(50.00),
        content="Conteúdo de teste da publicação do DJE sobre aposentadoria por invalidez do INSS. Este é um teste automatizado da conexão entre o scraper e a API.",
        extraction_metadata={
            "extraction_date": datetime.now().isoformat(),
            "source_url": "https://dje.tjsp.jus.br/test",
            "confidence_score": 1.0,
            "test_run": True,
        },
    )

    logger.info(f"📄 Testando publicação: {test_publication.process_number}")

    try:
        # Testar salvamento
        success = await api_client.save_publication(test_publication)

        if success:
            logger.info("✅ Teste de conexão com API PASSOU")
            logger.info(
                f"📊 Publicação de teste salva: {test_publication.process_number}"
            )
            return True
        else:
            logger.error("❌ Teste de conexão com API FALHOU")
            return False

    except Exception as error:
        logger.error(f"❌ Erro durante teste: {error}")
        return False


async def test_publication_check():
    """Testa verificação de publicação existente"""
    logger.info("🔍 Testando verificação de publicação existente")

    api_client = ApiClientAdapter()

    # Testar com número de processo que provavelmente não existe
    test_process = "TEST-NONEXISTENT-89.2024.8.26.0100"

    exists = await api_client.check_publication_exists(test_process)
    logger.info(f"📋 Publicação {test_process} existe: {exists}")

    return True


async def main():
    """Função principal do teste"""
    logger.info("🚀 Iniciando testes do scraper DJE-SP")

    tests = [
        ("Conexão com API", test_api_connection),
        ("Verificação de publicação", test_publication_check),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Executando: {test_name}")

        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: PASSOU")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FALHOU")
                failed += 1
        except Exception as error:
            logger.error(f"❌ {test_name}: ERRO - {error}")
            failed += 1

    logger.info("\n📊 Resultados dos testes:")
    logger.info(f"✅ Passou: {passed}")
    logger.info(f"❌ Falhou: {failed}")
    logger.info(f"📈 Total: {passed + failed}")

    if failed == 0:
        logger.info("🎉 Todos os testes passaram!")
    else:
        logger.warning("⚠️  Alguns testes falharam. Verifique a configuração.")


if __name__ == "__main__":
    asyncio.run(main())
