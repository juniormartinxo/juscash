#!/usr/bin/env python3
import json
import requests

# JSON exato do scraper
payload = {
    "process_number": "0013168-70.2024.8.26.0053",
    "availabilityDate": "2025-06-15T19:30:01.145Z",
    "authors": ["Sheila De Oliv Eira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Processo 0013168-70.2024.8.26.0053 (processo principal 1070174- 86.2022.8.26.0053) - Cumprimento de Sentença contra a Fazenda Pública - Auxílio-Acidente (Art. 86) - Sheila de Oliv eira - Vistos. 1) Homologação dos cálculos: Com a concordância da parte contrária (fls. 104/105), homologo os cálculos apresen tados (fls. 93/96) e atualizados para 08/2024 (data-base), que correspondem ao importe total de R$ 129.144,23, composto pelas seguintes parcelas: R$ 113.611,90 - principal bruto/líquido; R$ 0,00 - juros moratórios; R$ 15.532,33 - honorários advocatíc ios. Os valores devem ser atualizados na data do efetivo pagamento pelo INSS. Ausente o interesse recursal, dá-se o trân sito em julgado deste item nesta data. 2) Peticionamento eletrônico do incidente processual: Nos termos do Comunicado SP I nº 03/2014, providencie a parte autora a instauração do incidente processual de requisição de pagamento (RPV ou Prec atório) pelo sistema de peticionamento eletrônico (portal e-SAJ). Os valores do requisitório deverão ser discriminados e individualizados de acordo com a natureza de cada parcela (principal, juros de mora, honorários advocatícios), em conform idade estrita com a conta homologada e nos termos da presente decisão. Conforme o artigo 9º da Resolução nº 551/2011 do Órgão Especial do E. TJSP e art. 1.197, §§1º e 2º das NSCGJ, para a instrução e conferência do incidente processual, o(a) re querente deverá apresentar sua petição de requerimento com cópia dos seguintes documentos necessários para a expedição do ofício requisitório, devidamente separados e categorizados: documentos pessoais do(a) requerente (RG e CPF); procuração e s ubstabelecimento(s) outorgado(s) ao longo do presente feito do(a) advogada(a) que assina a petição e que consta como beneficiário(a); memória(s) de cálculo completa dos valores homologados; decisão(ões) homologatória(s) dos valores devidos e a serem requisitados. demais peças que o(a) exequente julgar necessário. 3) Requisição do crédito do(a) advogado(a): A critério dos interessados, os valores devidos poderão ser requisitados conjuntamente, em um único incidente processual, o u requisitados de forma apartada, separando-se o valor do crédito principal (principal bruto/líquido + juros moratórios) e o valor da sucumbência, nos termos da Súmula Vinculante nº 47 , hipótese em que os(as) exequentes deverão providenciar, em inci dentes processuais distintos, a requisição do crédito do(a) autor(a) e dos valores devidos a título de honorários de sucumb ência, sendo o primeiro formado em nome da parte autora e o último formado em nome do(a) advogado(a) requerente. Já os hono rários advocatícios contratuais devem ser obrigatoriamente requisitados juntamente do principal, sob pena de configurar fr acionamento. A Entidade Devedora é parte estranha ao contrato firmado entre o(a) exequente e seu(sua) advogado(a) (STF, RE 1. 094.439 AgR, 2ª T, Rel. Min. DIAS TOFFOLI, j. 2.3.2018). Na hipótese de o(a) advogado(a) pretender a individualização dos h onorários contratuais em campo próprio dentro do requisitório d o crédito do(a) exequente, deverá apresentar planilha da conta, c om a exata separação das verbas referentes ao principal bruto/ líquido, juros de mora, honorários sucumbenciais, honorários co ntratuais e demais verbas, e cópia do contrato nos autos deste Cumprimento de Sentença antes do peticionamento eletrônico do i ncidente processual, a fim de possibilitar o exercício da ampla defesa e do contraditório. 4) Individualização de requisitórios : Havendo mais de um credor, os ofícios de requisição deverão ser expedidos de modo individual por credor em requisições sepa radas, na proporção devida a cada um, ainda que exista litisconsórcio, bem como a planilha de cálculos e a documentaçã o necessária igualmente deverão ser apresentadas de forma individualizada por credor, nos termos da Portaria nº 9.622/201 8 (D.J.E. de 08/06/18) e do Comunicado Conjunto nº 1.212/2018 (D.J.E. de 22/06/18), que regulamentam a expedição dos requisit órios de pagamento no âmbito deste Tribunal. Para tanto, deverão os(as) exequentes apresentar, antes do peticionamento e letrônico do incidente processual e nos autos do Cumprimento de Sentença contra a Fazenda Pública, a competente planilha de cálculo, com a exata separação das verbas, individualizadas por credor, a fim de possibilitar a correta aferição pela parte contrária e por este Juízo do quinhão cabente a cada requerent e ou litisconsorte. 5) Disposições finais: Defiro o prazo de 30 (tri nta) dias para cumprimento. Devidamente instaurados os incident es e requisitados os valores, aguarde-se o pagamento lançando-se o código SAJ nº 15.247, Após extinção do ultimo incidente pela quitação, estes autos deverão ser remetidos à conclusão pa ra extinção da execução, nos termos do § 1º do art. 1.291 do provimento CGJ nº 29/2023). No silêncio a qualquer tempo, ce rtifique-se e aguarde-se provocação no arquivo provisório (61614). Int. - ADV: EUNICE MENDONCA DA SILVA DE CARVALHO (OAB 138649/SP), PATRICIA MENDONÇA DE CARVALHO ARAÚJO (OAB 332295/SP)",
    "status": "NOVA",
    "scrapingSource": "DJE-SP",
    "caderno": "3",
    "instancia": "1",
    "local": "Capital",
    "parte": "1",
    "lawyers": [
        {"name": "Eunice Mendonca Da Silva Carvalho", "oab": "138649"},
        {"name": "Patricia Mendonça Carvalho Araújo", "oab": "332295"},
    ],
    "extractionMetadata": {
        "extraction_date": "2025-06-15T19:30:01.154676",
        "source_url": "/tmp/dje_scraper_pdfs/dje_20250615_193001_091766.pdf",
        "extraction_method": "enhanced_rpv_inss_pattern",
        "match_type": "pagamento pelo INSS",
        "match_position": 2038,
        "process_spans_pages": False,
        "text_length": 5117,
    },
}

print(f"Tamanho do JSON: {len(json.dumps(payload))} chars")
print(f"Tamanho do conteúdo: {len(payload['content'])} chars")

# Salvar em arquivo para usar com curl
with open("exact_payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("JSON salvo em exact_payload.json")
