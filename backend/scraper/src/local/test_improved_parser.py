#!/usr/bin/env python3
"""
Script de teste para validar as melhorias implementadas no parser DJE-SP
"""

import sys
import os

# Adicionar o diretório pai (src) ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock das dependências que podem não estar disponíveis
class MockPublication:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockLawyer:
    def __init__(self, name, oab):
        self.name = name
        self.oab = oab


class MockMonetaryValue:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_real(cls, value):
        return cls(value)


# Mock do logger
class MockLogger:
    def debug(self, msg):
        print(f"DEBUG: {msg}")

    def info(self, msg):
        print(f"INFO: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")


# Substituir as importações
sys.modules["domain.entities.publication"] = type(
    "MockModule",
    (),
    {
        "Publication": MockPublication,
        "Lawyer": MockLawyer,
        "MonetaryValue": MockMonetaryValue,
    },
)()

sys.modules["infrastructure.logging.logger"] = type(
    "MockModule", (), {"setup_logger": lambda name: MockLogger()}
)()

# Agora importar o parser
from infrastructure.web.content_parser import DJEContentParser

# Conteúdo de teste baseado no PDF processado
test_content = """
Diário Oficial eletrônico - quarta-feira, 13 de novembro de 2024

Diário da Justiça Eletrônica - Caderno Judicial - Presidente - Capital (Proc.) | São Paulo, Ano XVII, Edição 4902

3714 TJ - Tribunal de Justiça do Estado de São Paulo

Processo 0017752-90.2019.8.26.0053 ) Procedimento Comum (Proc. Exec.) - Saúde - Claudio Luiz Bueno de Miranda - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS - Marília Rezende de Oliveira - Cláudia Luiz relacionados aos valores de precatório deverá ser feito no incidente e não serão avaliados neste autor. Int. - ADV. BRUNO MOREIRA COSTA (OAB 316779/SP), SERGIO ROBERTO MUNANO DA SILVA (OAB 196791/SP), ANDREA VENEZI.AN DE CARVALHO (OAB 162791/SP), ROBERTA NEVES MUNANO DA SILVA (OAB 516179/SP), JOANA LAZO CARINHEIRO (OAB 183475/SP).

Processo 0031736-13.2018.8.26.0053 (processo principal 1007966-40.2018.8.26.0053) - Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Doença Acidentário - Mirian Rezende de Oliveira - Implantação do benefício comprometida pois nossa defesa não foi bem sucedida; JOSÉ MARIA SANTOS (OAB 104052/SP), ROSANA BORGES MACHADO (OAB 298775/SP).

Processo 0031740-53.2018.8.26.0053 (processo principal 1014791-15.2014.8.26.0053) - Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Doença Acidentário - Bruno Moreira Costa - José Maria Santos - INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS - Int. - ADV. CLAUDIA MARIA BARRETO - WALDYR GRISARD FILHO - WALDEIR GRISARD NETO - Inadmissível Laboratoria Permanente - Edison da Silva Guerra - Vistoria II Homologação das cláusulas aprovadas do cadastro pela expedição da sentença em 23/05/22 2021. R$ 43.545,51 - juros monetários, R$ 11.578,51 - honorários advocatícios. Os valores devem ser atualizados na data do efetivo pagamento das séries recursal (data da disponibilização do acórdão).

Publicação Oficial do Tribunal de Justiça do Estado de São Paulo - Lei Federal n° 11.419/06, art. 4°.
"""


def test_parser():
    """Testa as funcionalidades do parser aprimorado"""
    print("🔍 Testando parser DJE-SP aprimorado...")

    parser = DJEContentParser()

    # Teste 1: Processamento de múltiplas publicações
    print("\n📋 Teste 1: Processamento de múltiplas publicações")
    publications = parser.parse_multiple_publications(test_content)
    print(f"   Publicações encontradas: {len(publications)}")

    # Teste 2: Validação de cada publicação
    print("\n📋 Teste 2: Validação de publicações individuais")
    for i, pub in enumerate(publications, 1):
        print(f"\n   Publicação {i}:")
        print(f"   - Número do processo: {pub.process_number}")
        print(f"   - Data de publicação: {pub.publication_date}")
        print(f"   - Autores: {pub.authors}")
        print(
            f"   - Advogados: {[f'{l.name} (OAB {l.oab})' for l in pub.lawyers] if pub.lawyers else 'Nenhum'}"
        )

        # Verificar valores monetários
        values = []
        if pub.gross_value:
            values.append(f"Valor bruto: R$ {pub.gross_value.value}")
        if pub.interest_value:
            values.append(f"Juros: R$ {pub.interest_value.value}")
        if pub.attorney_fees:
            values.append(f"Honorários: R$ {pub.attorney_fees.value}")

        if values:
            print(f"   - Valores: {', '.join(values)}")
        else:
            print(f"   - Valores: Não identificados")

    # Teste 3: Teste de padrões específicos
    print("\n📋 Teste 3: Teste de padrões específicos")

    # Teste extração de data por extenso
    date = parser._extract_publication_date(test_content)
    print(f"   - Data extraída: {date}")

    # Teste detecção INSS
    is_inss = parser._is_inss_related(test_content)
    print(f"   - Relacionado ao INSS: {is_inss}")

    print("\n✅ Testes concluídos!")
    return publications


if __name__ == "__main__":
    publications = test_parser()

    print(f"\n📊 Resumo: {len(publications)} publicações processadas com sucesso!")
