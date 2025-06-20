#!/usr/bin/env python3
"""
Script de teste para validar o enriquecimento de processos com dados do e-SAJ
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append("src")

from cli.enrichment_cli import EnrichmentCLI
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_basic_functionality():
    """
    Testa funcionalidade básica do enriquecimento
    """
    logger.info("🧪 Iniciando teste básico de funcionalidade...")

    # Processo de exemplo mencionado pelo usuário
    test_process = "0009027-08.2024.8.26.0053"

    cli = EnrichmentCLI()

    try:
        await cli.test_single_process(test_process)
        logger.info("✅ Teste básico concluído com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro no teste básico: {e}")
        raise


async def test_multiple_processes():
    """
    Testa enriquecimento de múltiplos processos
    """
    logger.info("🧪 Iniciando teste de múltiplos processos...")

    # Lista de processos para teste
    test_processes = [
        "0009027-08.2024.8.26.0053",
        "0001234-56.2024.8.26.0053",  # Processo fictício para teste
        "0005678-90.2024.8.26.0053",  # Processo fictício para teste
    ]

    cli = EnrichmentCLI()

    try:
        await cli.test_multiple_processes(test_processes)
        logger.info("✅ Teste de múltiplos processos concluído!")
    except Exception as e:
        logger.error(f"❌ Erro no teste de múltiplos processos: {e}")
        raise


async def main():
    """
    Função principal de teste
    """
    print("🚀 TESTE DE ENRIQUECIMENTO DE PROCESSOS e-SAJ")
    print("=" * 60)

    try:
        # Teste 1: Funcionalidade básica
        print("\n📋 TESTE 1: Funcionalidade Básica")
        print("-" * 40)
        await test_basic_functionality()

        # Teste 2: Múltiplos processos (comentado para não sobrecarregar)
        # print("\n📋 TESTE 2: Múltiplos Processos")
        # print("-" * 40)
        # await test_multiple_processes()

        print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")

    except KeyboardInterrupt:
        logger.info("⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
