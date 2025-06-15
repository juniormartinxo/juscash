#!/usr/bin/env python3
"""
Teste da funcionalidade de salvamento de relatórios TXT
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.files.report_txt_saver import ReportTxtSaver
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


async def test_report_saver():
    """Testa o salvamento de relatórios TXT"""
    print("🧪 Teste do Salvador de Relatórios TXT")
    print("=" * 60)

    try:
        # Criar instância do salvador
        report_saver = ReportTxtSaver("./test_relatorios")

        print(f"📁 Diretório de teste criado")

        # Criar publicação de teste
        test_publication = Publication(
            process_number="0013168-70.2024.8.26.0053",
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime.now(),
            authors=["Sheila de Oliveira"],
            defendant="Instituto Nacional do Seguro Social - INSS",
            lawyers=[
                Lawyer(name="Eunice Mendonca da Silva Carvalho", oab="138649"),
                Lawyer(name="Patricia Mendonça de Carvalho Araújo", oab="332295"),
            ],
            gross_value=MonetaryValue.from_real(129144.23),
            net_value=MonetaryValue.from_real(113611.90),
            interest_value=MonetaryValue.from_real(0.00),
            attorney_fees=MonetaryValue.from_real(15532.33),
            content="""Processo 0013168-70.2024.8.26.0053 (processo principal 1070174-86.2022.8.26.0053) - Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Acidente (Art. 86) - Sheila de Oliveira - Vistos. 1) Homologação dos cálculos: Com a concordância da parte contrária (fls. 104/105), homologo os cálculos apresentados (fls. 93/96) e atualizados para 08/2024 (data-base), que correspondem ao importe total de R$ 129.144,23, composto pelas seguintes parcelas: R$ 113.611,90 - principal bruto/líquido; R$ 0,00 - juros moratórios; R$ 15.532,33 - honorários advocatícios. Os valores devem ser atualizados na data do efetivo pagamento pelo INSS.""",
            extraction_metadata={
                "extraction_date": datetime.now().isoformat(),
                "source_url": "/tmp/dje_scraper_pdfs/dje_20241113_test.pdf",
                "extraction_method": "enhanced_rpv_inss_pattern",
                "match_type": "pagamento pelo INSS",
                "match_position": 2038,
                "process_spans_pages": False,
                "text_length": 5117,
            },
        )

        print(f"📄 Publicação de teste criada: {test_publication.process_number}")

        # Teste 1: Salvar relatório
        print(f"\n📝 Teste 1: Salvamento de relatório")
        saved_path = await report_saver.save_publication_report(test_publication)

        if saved_path:
            print(f"✅ Relatório salvo em: {saved_path}")

            # Verificar se arquivo foi criado
            if Path(saved_path).exists():
                print(f"✅ Arquivo confirmado no sistema de arquivos")

                # Ler primeiras linhas para verificar conteúdo
                with open(saved_path, "r", encoding="utf-8") as f:
                    first_lines = f.readlines()[:10]
                    print(f"📋 Primeiras linhas do relatório:")
                    for i, line in enumerate(first_lines, 1):
                        print(f"   {i:2d}: {line.strip()}")
            else:
                print(f"❌ Arquivo não encontrado: {saved_path}")
        else:
            print(f"❌ Falha ao salvar relatório")

        # Teste 2: Estatísticas
        print(f"\n📊 Teste 2: Estatísticas do dia")
        stats = report_saver.get_daily_stats()
        print(f"📅 Data: {stats.get('date')}")
        print(f"📝 Total de relatórios: {stats.get('total_reports')}")
        print(f"📁 Diretório: {stats.get('directory')}")

        if stats.get("files"):
            print(f"📄 Arquivos recentes:")
            for file in stats.get("files", []):
                print(f"   - {file}")

        # Teste 3: Testar com segunda publicação
        print(f"\n📝 Teste 3: Segunda publicação")

        test_publication2 = Publication(
            process_number="0029544-34.2024.8.26.0053",
            publication_date=datetime(2024, 11, 13),
            availability_date=datetime.now(),
            authors=["Verissimo Ursulino do Nascimento"],
            defendant="Instituto Nacional do Seguro Social - INSS",
            gross_value=MonetaryValue.from_real(34791.86),
            attorney_fees=MonetaryValue.from_real(3006.30),
            content="Processo de Incapacidade Laborativa Permanente...",
            extraction_metadata={
                "extraction_date": datetime.now().isoformat(),
                "source_url": "/tmp/dje_scraper_pdfs/dje_20241113_test2.pdf",
                "extraction_method": "enhanced_rpv_inss_pattern",
            },
        )

        saved_path2 = await report_saver.save_publication_report(test_publication2)
        if saved_path2:
            print(f"✅ Segunda publicação salva: {saved_path2}")
        else:
            print(f"❌ Falha ao salvar segunda publicação")

        # Estatísticas finais
        print(f"\n📊 Estatísticas finais:")
        final_stats = report_saver.get_daily_stats()
        print(f"📝 Total de relatórios: {final_stats.get('total_reports')}")

        print(f"\n🎉 Teste concluído com sucesso!")
        print(f"💡 Os relatórios foram salvos em: {final_stats.get('directory')}")

        return True

    except Exception as error:
        print(f"❌ Erro durante teste: {error}")
        logger.error(f"Erro no teste: {error}")
        import traceback

        traceback.print_exc()
        return False


async def test_error_handling():
    """Testa tratamento de erros"""
    print(f"\n🔥 Teste de Tratamento de Erros")
    print("-" * 40)

    try:
        report_saver = ReportTxtSaver("./test_relatorios")

        # Criar publicação com dados inválidos
        invalid_publication = Publication(
            process_number="",  # Número vazio
            availability_date=datetime.now(),
            authors=[],  # Lista vazia
            content="",  # Conteúdo vazio
        )

        saved_path = await report_saver.save_publication_report(invalid_publication)

        if saved_path:
            print(f"✅ Relatório com dados inválidos salvo: {saved_path}")
            # Verificar se o conteúdo foi tratado adequadamente
            with open(saved_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "ERRO" in content:
                    print(f"❌ Relatório contém erro")
                else:
                    print(f"✅ Relatório com dados inválidos tratado adequadamente")
        else:
            print(f"❌ Falha ao salvar relatório com dados inválidos")

    except Exception as error:
        print(f"⚠️ Erro esperado capturado: {error}")


if __name__ == "__main__":
    print("🚀 Iniciando testes do ReportTxtSaver")

    asyncio.run(test_report_saver())
    asyncio.run(test_error_handling())

    print(f"\n✅ Todos os testes concluídos!")
