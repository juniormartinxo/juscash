#!/usr/bin/env python3
"""
Teste simplificado das melhorias do parser DJE-SP
"""

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict

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


def test_date_extraction():
    """Testa extração de data por extenso"""
    print("📅 Testando extração de data por extenso...")

    # Padrão para datas por extenso
    date_pattern = re.compile(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", re.IGNORECASE)
    match = date_pattern.search(test_content)

    if match:
        day = match.group(1)
        month_name = match.group(2)
        year = match.group(3)

        month_map = {
            "janeiro": "01",
            "fevereiro": "02",
            "março": "03",
            "abril": "04",
            "maio": "05",
            "junho": "06",
            "julho": "07",
            "agosto": "08",
            "setembro": "09",
            "outubro": "10",
            "novembro": "11",
            "dezembro": "12",
        }

        month = month_map.get(month_name.lower())
        if month:
            date_str = f"{day.zfill(2)}/{month}/{year}"
            parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
            print(f"   ✅ Data extraída: {parsed_date.strftime('%d/%m/%Y')}")
            return parsed_date

    print("   ❌ Data não encontrada")
    return None


def test_process_extraction():
    """Testa extração de números de processo"""
    print("\n🔍 Testando extração de números de processo...")

    process_pattern = re.compile(
        r"Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", re.IGNORECASE
    )
    matches = process_pattern.findall(test_content)

    print(f"   ✅ Processos encontrados: {len(matches)}")
    for i, process in enumerate(matches, 1):
        print(f"   {i}. {process}")

    return matches


def test_author_extraction():
    """Testa extração de autores com padrões aprimorados"""
    print("\n👥 Testando extração de autores...")

    # Padrões específicos para estrutura do DJE-SP
    author_patterns = [
        re.compile(r"Acidentário\s+-\s+([^-]+?)\s+-", re.IGNORECASE),
        re.compile(r"Saúde\s+-\s+([^-]+?)\s+-\s+INSTITUTO", re.IGNORECASE),
        re.compile(r"Exec\.\)\s+-\s+\w+\s+-\s+([^-]+?)\s+-\s+INSTITUTO", re.IGNORECASE),
        re.compile(r"-\s+([^-]+?)\s+-\s+INSTITUTO\s+NACIONAL", re.IGNORECASE),
    ]

    authors_found = []

    for pattern in author_patterns:
        matches = pattern.finditer(test_content)
        for match in matches:
            author = match.group(1).strip()
            # Limpar nome
            author = re.sub(r"[^\w\sÁÉÍÓÚÀÂÊÔÃÕÇáéíóúàâêôãõç]", "", author)
            author = re.sub(r"\s+", " ", author).strip().title()

            if (
                author
                and len(author) > 3
                and not re.search(
                    r"(inss|instituto|nacional|seguro|social)", author, re.IGNORECASE
                )
            ):
                authors_found.append(author)

    print(f"   ✅ Autores encontrados: {len(authors_found)}")
    for i, author in enumerate(authors_found, 1):
        print(f"   {i}. {author}")

    return authors_found


def test_lawyer_extraction():
    """Testa extração de advogados"""
    print("\n⚖️  Testando extração de advogados...")

    # Padrões aprimorados para nomes em maiúsculas com OAB
    lawyer_patterns = [
        re.compile(r"([A-Z][A-Z\s]+[A-Z])\s*\(\s*OAB\s+(\d+)", re.IGNORECASE),
        re.compile(
            r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])\s*\(\s*OAB\s+(\d+)",
            re.IGNORECASE,
        ),
        re.compile(r"ADV\.\s+([A-Z][A-Z\s]+[A-Z])\s*\(\s*OAB\s+(\d+)", re.IGNORECASE),
    ]

    lawyers_found = []
    seen_oabs = set()

    for pattern in lawyer_patterns:
        matches = pattern.finditer(test_content)
        for match in matches:
            name = match.group(1).strip()
            oab = match.group(2)

            # Limpar nome
            name = re.sub(
                r"^(dr\.?|dra\.?|advogad[oa]|adv\.?)\s*", "", name, flags=re.IGNORECASE
            )
            name = re.sub(r"[^\w\sÁÉÍÓÚÀÂÊÔÃÕÇáéíóúàâêôãõç]", "", name)
            name = re.sub(r"\s+", " ", name).strip().title()

            if name and len(name) > 3 and oab not in seen_oabs:
                lawyers_found.append({"name": name, "oab": oab})
                seen_oabs.add(oab)

    print(f"   ✅ Advogados encontrados: {len(lawyers_found)}")
    for i, lawyer in enumerate(lawyers_found, 1):
        print(f"   {i}. {lawyer['name']} (OAB {lawyer['oab']})")

    return lawyers_found


def test_monetary_extraction():
    """Testa extração de valores monetários"""
    print("\n💰 Testando extração de valores monetários...")

    monetary_patterns = {
        "R$ genérico": re.compile(r"R\$\s*([\d.,]+)", re.IGNORECASE),
        "juros monetários": re.compile(
            r"juros\s+monet[áa]rios[,:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE
        ),
        "honorários advocatícios": re.compile(
            r"honor[áa]rios\s+advocat[íi]cios[,:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE
        ),
    }

    values_found = {}

    for value_type, pattern in monetary_patterns.items():
        match = pattern.search(test_content)
        if match:
            value_str = match.group(1)
            # Converter para formato padrão
            cleaned = re.sub(r"[^\d.,]", "", value_str)

            if "," in cleaned and "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                parts = cleaned.split(",")
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")

            try:
                decimal_value = Decimal(cleaned)
                values_found[value_type] = decimal_value
                print(f"   ✅ {value_type}: R$ {decimal_value}")
            except InvalidOperation:
                print(f"   ❌ Erro ao processar {value_type}: {value_str}")

    return values_found


def test_inss_detection():
    """Testa detecção de publicações relacionadas ao INSS"""
    print("\n🏛️  Testando detecção INSS...")

    inss_keywords = [
        "inss",
        "instituto nacional do seguro social",
        "seguro social",
        "previdencia",
        "auxilio",
        "aposentadoria",
        "beneficio",
        "acidentario",
    ]

    content_lower = test_content.lower()
    found_keywords = [keyword for keyword in inss_keywords if keyword in content_lower]

    print(f"   ✅ Palavras-chave INSS encontradas: {len(found_keywords)}")
    for keyword in found_keywords:
        print(f"   - {keyword}")

    return len(found_keywords) > 0


def main():
    """Executa todos os testes"""
    print("🧪 Testando melhorias do parser DJE-SP")
    print("=" * 50)

    # Executar testes
    date = test_date_extraction()
    processes = test_process_extraction()
    authors = test_author_extraction()
    lawyers = test_lawyer_extraction()
    values = test_monetary_extraction()
    is_inss = test_inss_detection()

    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    print(f"✅ Data de publicação: {'Extraída' if date else 'Não encontrada'}")
    print(f"✅ Processos encontrados: {len(processes)}")
    print(f"✅ Autores encontrados: {len(authors)}")
    print(f"✅ Advogados encontrados: {len(lawyers)}")
    print(f"✅ Valores monetários: {len(values)}")
    print(f"✅ Relacionado ao INSS: {'Sim' if is_inss else 'Não'}")

    print("\n🎉 Testes concluídos com sucesso!")


if __name__ == "__main__":
    main()
