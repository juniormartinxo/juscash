"""Dados de exemplo para testes."""

SAMPLE_DJE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DJE - Diário da Justiça Eletrônico</title>
</head>
<body>
    <div class="publicacao">
        <h3>Processo nº 1234567-89.2024.8.26.0100</h3>
        <p><strong>Data de disponibilização:</strong> 15/03/2024</p>
        <p><strong>Autor:</strong> João da Silva</p>
        <p><strong>Réu:</strong> Instituto Nacional do Seguro Social - INSS</p>
        <p><strong>Advogado:</strong> Dr. Carlos Alberto - OAB/SP 123456</p>
        <div class="valores">
            <p>Valor principal bruto: R$ 15.000,50</p>
            <p>Valor líquido: R$ 12.000,00</p>
            <p>Juros moratórios: R$ 2.500,25</p>
            <p>Honorários advocatícios: R$ 3.000,00</p>
        </div>
        <div class="conteudo">
            <p>VISTOS. Trata-se de ação previdenciária movida por João da Silva contra o Instituto Nacional do Seguro Social - INSS...</p>
        </div>
    </div>
    
    <div class="publicacao">
        <h3>Processo nº 7654321-98.2024.8.26.0100</h3>
        <p><strong>Data de disponibilização:</strong> 16/03/2024</p>
        <p><strong>Autor:</strong> Maria Santos</p>
        <p><strong>Réu:</strong> Instituto Nacional do Seguro Social - INSS</p>
        <p><strong>Advogado:</strong> Dra. Ana Costa - OAB/SP 789012</p>
        <div class="valores">
            <p>Valor principal bruto: R$ 25.000,75</p>
            <p>Juros moratórios: R$ 5.000,15</p>
            <p>Honorários advocatícios: R$ 4.500,00</p>
        </div>
        <div class="conteudo">
            <p>VISTOS. Ação de auxílio-doença movida por Maria Santos contra o INSS...</p>
        </div>
    </div>
</body>
</html>
"""

SAMPLE_PUBLICATIONS_DATA = [
    {
        "process_number": "1234567-89.2024.8.26.0100",
        "publication_date": "2024-03-15",
        "availability_date": "2024-03-15",
        "authors": ["João da Silva"],
        "lawyers": ["Dr. Carlos Alberto - OAB/SP 123456"],
        "gross_value": "15000.50",
        "net_value": "12000.00",
        "interest_value": "2500.25",
        "attorney_fees": "3000.00",
        "content": "VISTOS. Trata-se de ação previdenciária..."
    },
    {
        "process_number": "7654321-98.2024.8.26.0100", 
        "publication_date": "2024-03-16",
        "availability_date": "2024-03-16",
        "authors": ["Maria Santos"],
        "lawyers": ["Dra. Ana Costa - OAB/SP 789012"],
        "gross_value": "25000.75",
        "interest_value": "5000.15", 
        "attorney_fees": "4500.00",
        "content": "VISTOS. Ação de auxílio-doença..."
    }
]