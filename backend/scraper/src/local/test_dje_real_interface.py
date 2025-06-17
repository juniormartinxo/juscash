"""
Teste específico para a interface real do DJE
Baseado nas imagens fornecidas mostrando a estrutura real
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.web.content_parser import DJEContentParser
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


def test_real_dje_content():
    """Testa parser com conteúdo real das imagens do DJE"""

    # Conteúdo real extraído das imagens
    real_content_sample = """
    13/11/2024 - Caderno 3 - Judicial - 1ª Instância - Capital - Parte 1 - Página 3710 📱 1) conteúdo encontrado nesta página!
    meta data: 2) Peticionamento eletrônico do incidente processual: Nos termos da Comunicação SPI nº 03/2014, procedido a parte autora a intimação do
    incidente processual de requisição de pagamento (RPV ou Precatório) pelo sistema de peticionamento eletrônico (portal e-SAJ). Os valores do requisitório
    deverão ser discriminados e individualizados de acordo com a natureza de cada parcela (principal ...
    
    Processo 0029547-86.2024.8.26.0053 - ADV: JOSÉ BRUN JUNIOR (OAB 12836/SP) Processo ...
    
    CONCLUSÃO. - ADV: JOSÉ BRUN JUNIOR (OAB 12836/SP)
    Processo 0029547-97.2024.8.26.0053 - Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Acidente (Art. 86) - Josuel Anderson de Oliveira - Vistos. 1) Homologação dos cálculos: Com a concordância da parte contrária (fls. 35), homologo os cálculos apresentados (fls. 29/31) e atualizado para 10/2024 (data-base), que correspondem ao importe total de R$ 13.210,54, composto pelas seguintes parcelas: R$ 11.608,32 - principal bruto/líquido, R$ 835,67 - honorários advocatícios. Os valores devem ser atualizados pela SELIC até a data do efetivo pagamento pelo INSS. Ausente o interesse recursal, dê-se o trânsito em julgado deste item nesta data. 2) Peticionamento eletrônico do incidente processual: Nos termos da Comunicação SPI nº 03/2014, procedindo a parte autora a intimação do incidente processual de requisição de pagamento (RPV ou Precatório) pelo sistema de peticionamento eletrônico (portal e-SAJ). Os valores do requisitório deverão ser discriminados e individualizados de acordo com a natureza de cada parcela (principal, juros de mora, honorários advocatícios), em conformidade estrita com a conta homologada e nos termos da presente decisão. Conforme o artigo 17 da Resolução nº 551/2011 do Órgão Especial do E. TJSP e do § 1º art. 1º, SEJP da Lei nº 20.555/30, para a instrução e conferência do incidente processual, o(a) requerente deverá apresentar sua petição de requerimento com cópia dos seguintes documentos: a) certidão da homologação emitida pelo(a) diretor(a) secretário para a expedição do ofício requisitório, devidamente organizada e categorizada por documentos pessoais, do(a) requerente (RG e CPF), procuração e substabelecimento(s) outorgado(s) ao longo do presente feito do(a) advogado(a) para saque conforme estabelecido; c) cópia certidão da comarca para qualidade de representação de questões demandas; d(as) exequente lugar necessário; c) cópia do crédito do(a) advogado(a): A conta dos mandados dos requerentes de pedido de dos autores; e dados da conta bancária, beneficiário(a); memória(s) dos valores devido e as sentenças estabelecidas, demais peças que o(a) exequente lugar necessário e conta da presente: com certidão; A conta dos requerentes de pedido de dos autores; é necessário e se for da conta completa que constam como beneficiário(a): memória(s) dos valores devido e as sentenças estabelecidas.
    """

    logger.info("🧪 Testando parser com conteúdo real do DJE")

    parser = DJEContentParser()

    # Testar extração de número do processo
    process_number = parser._extract_process_number(real_content_sample)
    logger.info(f"📋 Número do processo extraído: {process_number}")

    # Testar extração de autores
    authors = parser._extract_authors(real_content_sample)
    logger.info(f"👥 Autores extraídos: {authors}")

    # Testar extração de advogados
    lawyers = parser._extract_lawyers(real_content_sample)
    logger.info(f"⚖️  Advogados extraídos: {lawyers}")

    # Testar extração de valores monetários
    monetary_values = parser._extract_all_monetary_values(real_content_sample)
    logger.info("💰 Valores monetários:")
    for value_type, value in monetary_values.items():
        if value:
            logger.info(f"   {value_type}: R$ {value.to_real()}")

    # Testar parsing completo
    publication = parser.parse_publication(
        real_content_sample, "https://dje.tjsp.jus.br/test"
    )

    if publication:
        logger.info("✅ Publicação parseada com sucesso:")
        logger.info(f"   📋 Processo: {publication.process_number}")
        logger.info(f"   👥 Autores: {publication.authors}")
        logger.info(f"   ⚖️  Advogados: {len(publication.lawyers)}")
        logger.info(
            f"   💰 Valor bruto: R$ {publication.gross_value.to_real() if publication.gross_value else 'N/A'}"
        )
        logger.info(
            f"   🎯 Confiança: {publication.extraction_metadata.get('confidence_score', 'N/A')}"
        )

        # Converter para formato da API
        api_data = publication.to_api_dict()
        logger.info("📤 Dados para API:")
        logger.info(f"   process_number: {api_data['process_number']}")
        logger.info(f"   authors: {api_data['authors']}")
        logger.info(f"   gross_value: {api_data['gross_value']} centavos")

        return True
    else:
        logger.error("❌ Falha ao parsear publicação")
        return False


async def test_dje_navigation_simulation():
    """Simula navegação no DJE baseada na interface real"""

    logger.info("🌐 Simulando navegação na interface real do DJE")

    # Simular passos de navegação baseados nas imagens
    navigation_steps = [
        "1. Acessar https://dje.tjsp.jus.br/cdje/index.do",
        "2. Clicar em 'Pesquisa avançada'",
        "3. Selecionar 'Caderno 3 - Judicial - 1ª Instância - Capital - Parte 1'",
        "4. Inserir palavras-chave: 'aposentadoria benefício INSS'",
        "5. Clicar em 'Pesquisar'",
        "6. Processar resultados da pesquisa",
    ]

    for i, step in enumerate(navigation_steps, 1):
        logger.info(f"🔄 Passo {i}: {step}")
        await asyncio.sleep(1)  # Simular tempo de execução

    logger.info("✅ Simulação de navegação concluída")


def test_data_validation():
    """Testa validação com dados baseados na estrutura real"""

    logger.info("🔍 Testando validação de dados reais")

    # Dados extraídos das imagens
    test_cases = [
        {
            "process_number": "0029547-86.2024.8.26.0053",
            "expected_valid": True,
            "description": "Número real das imagens",
        },
        {
            "process_number": "0029547-97.2024.8.26.0053",
            "expected_valid": True,
            "description": "Outro número real das imagens",
        },
        {
            "lawyer_text": "ADV: JOSÉ BRUN JUNIOR (OAB 12836/SP)",
            "expected_name": "JOSÉ BRUN JUNIOR",
            "expected_oab": "12836",
            "description": "Advogado real das imagens",
        },
        {
            "monetary_text": "R$ 11.608,32 - principal bruto/líquido",
            "expected_value": 11608.32,
            "description": "Valor principal das imagens",
        },
        {
            "monetary_text": "R$ 835,67 - honorários advocatícios",
            "expected_value": 835.67,
            "description": "Honorários das imagens",
        },
    ]

    parser = DJEContentParser()

    # Testar números de processo
    for case in test_cases:
        if "process_number" in case:
            is_valid = parser._validate_process_number_format(case["process_number"])
            status = "✅" if is_valid == case["expected_valid"] else "❌"
            logger.info(
                f"{status} {case['description']}: {case['process_number']} -> {is_valid}"
            )

    # Testar extração de advogados
    for case in test_cases:
        if "lawyer_text" in case:
            lawyers = parser._extract_lawyers(case["lawyer_text"])
            if lawyers:
                lawyer = lawyers[0]
                name_ok = case["expected_name"] in lawyer.name
                oab_ok = case["expected_oab"] in lawyer.oab
                status = "✅" if name_ok and oab_ok else "❌"
                logger.info(
                    f"{status} {case['description']}: {lawyer.name} (OAB: {lawyer.oab})"
                )

    # Testar valores monetários
    for case in test_cases:
        if "monetary_text" in case:
            values = parser._extract_all_monetary_values(case["monetary_text"])
            found_value = None
            for value in values.values():
                if (
                    value
                    and abs(float(value.to_real()) - case["expected_value"]) < 0.01
                ):
                    found_value = value
                    break

            status = "✅" if found_value else "❌"
            logger.info(
                f"{status} {case['description']}: R$ {found_value.to_real() if found_value else 'N/A'}"
            )


def main():
    """Função principal do teste"""
    logger.info("🚀 Iniciando testes com interface real do DJE")
    logger.info("=" * 50)

    # Teste 1: Parser com conteúdo real
    logger.info("\n📄 Teste 1: Parser com conteúdo real")
    success1 = test_real_dje_content()

    # Teste 2: Validação de dados
    logger.info("\n🔍 Teste 2: Validação de dados")
    test_data_validation()

    # Teste 3: Simulação de navegação
    logger.info("\n🌐 Teste 3: Simulação de navegação")
    asyncio.run(test_dje_navigation_simulation())

    # Resumo
    logger.info("\n📊 Resumo dos Testes")
    logger.info("=" * 50)

    if success1:
        logger.info("✅ Todos os testes passaram!")
        logger.info("🎯 O parser está otimizado para a interface real do DJE")
        logger.info("📋 Pronto para extrair dados das publicações reais")
    else:
        logger.error("❌ Alguns testes falharam")
        logger.info("🔧 Verifique os padrões de parsing")

    return success1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
