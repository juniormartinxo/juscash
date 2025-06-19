"""
🧪 TESTES ESPECÍFICOS - EXTRAÇÃO APRIMORADA DE ADVOGADOS

Testes focados nos problemas reportados:
1. Padrão "ADV:" com dois pontos
2. Múltiplos advogados separados por vírgula
3. Advogados no final das publicações
4. Diferentes formatos de OAB
"""

import pytest
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.web.enhanced_parser_integrated import EnhancedDJEParserIntegrated
from domain.entities.publication import Lawyer


class TestEnhancedLawyerExtraction:
    """Testes específicos para extração aprimorada de advogados"""

    @pytest.fixture
    def parser(self):
        """Enhanced parser para testes"""
        return EnhancedDJEParserIntegrated()

    def test_adv_colon_pattern(self, parser):
        """Testa padrão ADV: NOME (OAB XX/SP)"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        Publicação sobre RPV para pagamento pelo INSS.
        ADV: MARCIO SILVA COELHO (OAB 45683/SP).
        """

        lawyers = parser._extract_lawyers(content)

        assert len(lawyers) >= 1

        # Verificar se MARCIO foi capturado
        marcio_found = any(
            "MARCIO" in lawyer.name.upper() and "45683" in lawyer.oab_number
            for lawyer in lawyers
        )
        assert marcio_found, (
            f"MARCIO não encontrado. Advogados: {[l.name for l in lawyers]}"
        )

    def test_multiple_lawyers_comma_separated(self, parser):
        """Testa múltiplos advogados separados por vírgula"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        Publicação sobre RPV para pagamento pelo INSS.
        ADV: MARCIO SILVA COELHO (OAB 45683/SP), ESMERALDA FIGUEIREDO DE OLIVEIRA (OAB 29062/SP).
        """

        lawyers = parser._extract_lawyers(content)

        assert len(lawyers) >= 2

        # Verificar se ambos foram capturados
        marcio_found = any("MARCIO" in lawyer.name.upper() for lawyer in lawyers)
        esmeralda_found = any("ESMERALDA" in lawyer.name.upper() for lawyer in lawyers)

        assert marcio_found, (
            f"MARCIO não encontrado. Advogados: {[l.name for l in lawyers]}"
        )
        assert esmeralda_found, (
            f"ESMERALDA não encontrada. Advogados: {[l.name for l in lawyers]}"
        )

    def test_lawyer_at_publication_end(self, parser):
        """Testa advogado no final da publicação"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA - Vistos. O requerente solicita RPV para pagamento pelo INSS 
        do valor de R$ 5.450,30. Defiro o pedido conforme documentação apresentada.
        Intimem-se as partes. São Paulo, 17 de março de 2025.
        KARINA CHINEM UEZATO (OAB 197415/SP).
        """

        lawyers = parser._extract_lawyers(content)

        assert len(lawyers) >= 1

        # Verificar se KARINA foi capturada
        karina_found = any(
            "KARINA" in lawyer.name.upper() and "197415" in lawyer.oab_number
            for lawyer in lawyers
        )
        assert karina_found, (
            f"KARINA não encontrada. Advogados: {[l.name for l in lawyers]}"
        )

    def test_various_adv_patterns(self, parser):
        """Testa diferentes variações do padrão ADV"""
        test_cases = [
            # ADV: (dois pontos)
            "ADV: MARIA SANTOS OLIVEIRA (OAB 123456/SP)",
            # ADV. (ponto)
            "ADV. JOSÉ RODRIGUES LIMA (OAB 789012/RJ)",
            # ADVOGADO
            "ADVOGADO PEDRO COSTA SILVA (OAB 345678/MG)",
            # ADVOGADA
            "ADVOGADA ANA PAULA FERREIRA (OAB 567890/DF)",
            # Só nome e OAB
            "CARLOS EDUARDO SANTOS (OAB 901234/RS)",
        ]

        for i, case in enumerate(test_cases):
            content = f"""
            Processo 123456{i}-89.2024.8.26.000{i} - Teste
            Publicação sobre RPV. {case}.
            """

            lawyers = parser._extract_lawyers(content)
            assert len(lawyers) >= 1, f"Falha no caso {i + 1}: {case}"

    def test_oab_number_variations(self, parser):
        """Testa diferentes formatos de número OAB"""
        test_cases = [
            "ADVOGADO TESTE UM (OAB 12345/SP)",  # 5 dígitos
            "ADVOGADO TESTE DOIS (OAB 123456/SP)",  # 6 dígitos
            "ADVOGADO TESTE TRES (OAB 1234/SP)",  # 4 dígitos
            "ADVOGADO TESTE QUATRO (OAB 123456)",  # Sem UF
            "ADVOGADO TESTE CINCO (OAB 123456/RJ)",  # UF diferente
        ]

        for i, case in enumerate(test_cases):
            content = f"""
            Processo 123456{i}-89.2024.8.26.000{i} - Teste
            Publicação sobre RPV. {case}.
            """

            lawyers = parser._extract_lawyers(content)
            assert len(lawyers) >= 1, f"Falha no formato OAB: {case}"

    def test_end_region_extraction(self, parser):
        """Testa extração específica da região final"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        - JOÃO DA SILVA - Vistos. O requerente solicita RPV para pagamento pelo INSS.
        
        Muito texto aqui no meio da publicação que pode confundir o parser.
        Mais texto ainda para testar se o parser consegue focar no final.
        Ainda mais texto para garantir que só capture os advogados do final.
        
        Final da publicação com advogados:
        ADV: MARCOS ANTONIO SILVA (OAB 111111/SP), LUCIA FERNANDA COSTA (OAB 222222/SP).
        São Paulo, 17 de março de 2025.
        """

        # Testar método específico para região final
        end_lawyers = parser._extract_lawyers_from_publication_end(content)

        assert len(end_lawyers) >= 2

        # Verificar nomes específicos
        marcos_found = any("MARCOS" in lawyer.name.upper() for lawyer in end_lawyers)
        lucia_found = any("LUCIA" in lawyer.name.upper() for lawyer in end_lawyers)

        assert marcos_found, (
            f"MARCOS não encontrado no final. Advogados: {[l.name for l in end_lawyers]}"
        )
        assert lucia_found, (
            f"LUCIA não encontrada no final. Advogados: {[l.name for l in end_lawyers]}"
        )

    def test_multiple_lawyers_parsing(self, parser):
        """Testa parsing de múltiplos advogados de um texto"""
        text = "ADV: MARCIO SILVA COELHO (OAB 45683/SP), ESMERALDA FIGUEIREDO DE OLIVEIRA (OAB 29062/SP), KARINA CHINEM UEZATO (OAB 197415/SP)"

        lawyers = parser._parse_multiple_lawyers_from_text(text)

        assert len(lawyers) == 3

        # Verificar todos os nomes
        names_found = [lawyer.name.upper() for lawyer in lawyers]
        assert any("MARCIO" in name for name in names_found)
        assert any("ESMERALDA" in name for name in names_found)
        assert any("KARINA" in name for name in names_found)

        # Verificar números OAB
        oabs_found = [lawyer.oab_number for lawyer in lawyers]
        assert "45683" in oabs_found
        assert "29062" in oabs_found
        assert "197415" in oabs_found

    def test_lawyer_name_validation(self, parser):
        """Testa validação de nomes de advogados"""
        # Nomes válidos
        valid_names = [
            "MARIA SANTOS OLIVEIRA",
            "JOSÉ RODRIGUES LIMA",
            "ANA PAULA FERREIRA COSTA",
            "MARCOS ANTONIO DA SILVA JUNIOR",
        ]

        for name in valid_names:
            assert parser._is_valid_lawyer_name(name), f"Nome válido rejeitado: {name}"

        # Nomes inválidos
        invalid_names = [
            "AB",  # Muito curto
            "A B",  # Palavras muito curtas
            "X",  # Uma palavra só
            "M" * 85,  # Muito longo
            "NOME@INVALID",  # Caracteres inválidos
        ]

        for name in invalid_names:
            assert not parser._is_valid_lawyer_name(name), (
                f"Nome inválido aceito: {name}"
            )

    def test_no_duplicate_lawyers(self, parser):
        """Testa que não há duplicação de advogados pelo mesmo OAB"""
        content = """
        Processo 1234567-89.2024.8.26.0001 - Teste
        ADV. MARIA SANTOS (OAB 123456/SP) fez o pedido.
        No final: MARIA SANTOS (OAB 123456/SP).
        """

        lawyers = parser._extract_lawyers(content)

        # Deve ter apenas 1 advogado (mesmo OAB)
        assert len(lawyers) == 1
        assert lawyers[0].oab_number == "123456"

    def test_real_world_example(self, parser):
        """Testa com exemplo real baseado no feedback do usuário"""
        content = """
        Processo 0029443-31.2023.8.26.0053/02 - Requisição de Pequeno Valor - Incapacidade Laborativa Permanente - Carla
        Rosana da Silva Balbino - 1ª. No campo prévio, dedica a ação previa pelo fundamento, por art. 5º, §3º da
        Provimento CSM nº 2.753/2024 ce artigo 49, §1º da Resolução 303 do CNJ, para eventual manifestação quanto a seu teor.
        
        Final da publicação:
        ADV: MARCIO SILVA COELHO (OAB 45683/SP), ESMERALDA FIGUEIREDO DE OLIVEIRA (OAB 29062/SP).
        
        Processo 1234567-89.2024.8.26.0002 - Próxima Ação
        """

        lawyers = parser._extract_lawyers(content)

        assert len(lawyers) >= 2

        # Verificar advogados específicos mencionados pelo usuário
        marcio_found = any(
            "MARCIO" in lawyer.name.upper()
            and "SILVA" in lawyer.name.upper()
            and "45683" in lawyer.oab_number
            for lawyer in lawyers
        )
        esmeralda_found = any(
            "ESMERALDA" in lawyer.name.upper() and "29062" in lawyer.oab_number
            for lawyer in lawyers
        )

        assert marcio_found, (
            f"MARCIO SILVA COELHO não encontrado. Advogados: {[(l.name, l.oab_number) for l in lawyers]}"
        )
        assert esmeralda_found, (
            f"ESMERALDA não encontrada. Advogados: {[(l.name, l.oab_number) for l in lawyers]}"
        )

    def test_performance_with_large_content(self, parser):
        """Testa performance com conteúdo grande"""
        # Simular publicação grande
        large_content = (
            """
        Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença
        """
            + "Muito texto repetido. " * 1000
            + """
        ADV: FERNANDO SANTOS OLIVEIRA (OAB 999999/SP).
        """
        )

        lawyers = parser._extract_lawyers(large_content)

        assert len(lawyers) >= 1
        assert any("FERNANDO" in lawyer.name.upper() for lawyer in lawyers)

    def test_edge_cases(self, parser):
        """Testa casos extremos"""
        # Caso 1: Múltiplas ocorrências de ADV
        content1 = """
        ADV. PRIMEIRO ADVOGADO (OAB 111111/SP) solicitou algo.
        ADV: SEGUNDO ADVOGADO (OAB 222222/SP) também.
        """
        lawyers1 = parser._extract_lawyers(content1)
        assert len(lawyers1) >= 2

        # Caso 2: OAB sem UF
        content2 = "ADVOGADO SEM UF (OAB 333333)"
        lawyers2 = parser._extract_lawyers(content2)
        assert len(lawyers2) >= 1

        # Caso 3: Nome com caracteres especiais válidos
        content3 = "MARIA-JOSÉ DOS SANTOS-SILVA (OAB 444444/SP)"
        lawyers3 = parser._extract_lawyers(content3)
        assert len(lawyers3) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
