"""
Dados de exemplo baseados nas imagens reais para testes
"""

# Conteúdo real das publicações conforme mostrado nas imagens
SAMPLE_DJE_PUBLICATIONS = [
    {
        "id": "pub_001",
        "raw_text": """
        13/11/2024 - Caderno 3 - Judicial - 1ª Instância - Capital - Parte 1 - Página 3710
        Processo 0029547-86.2024.8.26.0053
        ADV: JOSÉ BRUN JUNIOR (OAB 12836/SP)
        Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Acidente (Art. 86) - Josuel Anderson de Oliveira
        R$ 11.608,32 - principal bruto/líquido, R$ 835,67 - honorários advocatícios
        Homologação dos cálculos apresentados para aposentadoria por invalidez do INSS.
        """,
        "expected_data": {
            "process_number": "0029547-86.2024.8.26.0053",
            "authors": ["Josuel Anderson de Oliveira"],
            "lawyers": [{"name": "JOSÉ BRUN JUNIOR", "oab": "12836"}],
            "gross_value": 1160832,  # em centavos
            "attorney_fees": 83567,  # em centavos
            "defendant": "Instituto Nacional do Seguro Social - INSS",
        },
    },
    {
        "id": "pub_002",
        "raw_text": """
        13/11/2024 - Caderno 3 - Judicial - 1ª Instância - Capital - Parte 1 - Página 3714
        Processo 0029547-97.2024.8.26.0053
        meta data: Peticionamento eletrônico do incidente processual nos termos da Comunicação SPI
        procedido a parte autora a intimação do incidente processual de requisição de pagamento
        INSS benefício de aposentadoria especial valor devido
        """,
        "expected_data": {
            "process_number": "0029547-97.2024.8.26.0053",
            "defendant": "Instituto Nacional do Seguro Social - INSS",
        },
    },
]

# Padrões de interface conforme mostrado nas imagens
DJE_INTERFACE_SELECTORS = {
    "pesquisa_avancada": {
        "data_inicial": "input[name='dataInicial']",
        "data_final": "input[name='dataFinal']",
        "caderno": "select[name='caderno']",
        "palavras_chave": "textarea[name='palavrasChave']",
        "botao_pesquisar": "input[value='Pesquisar']",
        "botao_limpar": "input[value='Limpar']",
    },
    "resultados": {
        "tabela_resultados": "table",
        "linha_publicacao": "tr:has-text('Caderno 3')",
        "conteudo_publicacao": "td",
        "paginacao": ".paginacao",
        "proximo": "a:text('Próxima')",
    },
}

# Termos obrigatórios baseados nos requisitos
REQUIRED_SEARCH_TERMS = [
    "aposentadoria",
    "benefício",
    "INSS",
    "Instituto Nacional do Seguro Social",
]

print("📋 Dados de teste para interface real do DJE carregados")
print(f"   📄 {len(SAMPLE_DJE_PUBLICATIONS)} publicações de exemplo")
print(f"   🔍 {len(REQUIRED_SEARCH_TERMS)} termos obrigatórios")
print(f"   🌐 {len(DJE_INTERFACE_SELECTORS)} grupos de seletores")
