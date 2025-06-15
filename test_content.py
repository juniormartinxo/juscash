#!/usr/bin/env python3
import json
import requests

# Conteúdo original da publicação
content = """Processo 0029544-34.2024.8.26.0053 (processo principal 1032313- 32.2023.8.26.0053) - Cumprimento de Sentença contra 
a Fazenda Pública - Incapacidade Laborativa Permanente - Veriss imo Ursulino do Nascimento - Vistos. 1) Homologação 
dos cálculos: Com a concordância da parte contrária (fls. 33), homologo os cálculos apresentados pelo INSS (fls. 24/29) e 
atualizados para 10/2024 (data-base), que correspondem ao impor te total de R$ 34.791,86, composto pelas seguintes parcelas: 
R$ 31.785,56 - principal bruto/líquido; R$ 0,00 - juros moratór ios; R$ 3.006,30 - honorários advocatícios. Os valores devem se r 
atualizados na data do efetivo pagamento pelo INSS. Ausente o i nteresse recursal, dá-se o trânsito em julgado deste item nesta  
data. 2) Peticionamento eletrônico do incidente processual: Nos  termos do Comunicado SPI nº 03/2014, providencie a parte 
autora a instauração do incidente processual de requisição de p agamento (RPV ou Precatório) pelo sistema de peticionamento 
eletrônico (portal e-SAJ). Os valores do requisitório deverão s er discriminados e individualizados de acordo com a natureza 
de cada parcela (principal, juros de mora, honorários advocatíc ios), em conformidade estrita com a conta homologada e nos 
termos da presente decisão. Conforme o artigo 9º da Resolução n º 551/2011 do Órgão Especial do E. TJSP e art. 1.197, §§1º 
e 2º das NSCGJ, para a instrução e conferência do incidente pro cessual, o(a) requerente deverá apresentar sua petição de 
requerimento com cópia dos seguintes documentos necessários par a a expedição do ofício requisitório, devidamente separados 
e categorizados: documentos pessoais do(a) requerente (RG e CPF ); procuração e substabelecimento(s) outorgado(s) ao longo 
do presente feito do(a) advogada(a) que assina a petição e que consta como beneficiário(a); memória(s) de cálculo completa 
dos valores homologados; decisão(ões) homologatória(s) dos valo res devidos e a serem requisitados. demais peças que o(a) 
exequente julgar necessário. 3) Requisição do crédito do(a) adv ogado(a): A critério dos interessados, os valores devidos poder ão 
ser requisitados conjuntamente, em um único incidente processua l, ou requisitados de forma apartada, separando-se o valor 
do crédito principal (principal bruto/líquido + juros moratório s) e o valor da sucumbência, nos termos da Súmula Vinculante nº  
47, hipótese em que os(as) exequentes deverão providenciar, em incidentes processuais distintos, a requisição do crédito do(a)  
autor(a) e dos valores devidos a título de honorários de sucumb ência, sendo o primeiro formado em nome da parte autora e o 
último formado em nome do(a) advogado(a) requerente. Já os hono rários advocatícios contratuais devem ser obrigatoriamente 
requisitados juntamente do principal, sob pena de configurar fr acionamento. A Entidade Devedora é parte estranha ao contrato 
firmado entre o(a) exequente e seu(sua) advogado(a) (STF, RE 1. 094.439 AgR, 2ª T, Rel. Min. DIAS TOFFOLI, j. 2.3.2018). Na 
hipótese de o(a) advogado(a) pretender a individualização dos h onorários contratuais em campo próprio dentro do requisitório d o 
crédito do(a) exequente, deverá apresentar planilha da conta, c om a exata separação das verbas referentes ao principal bruto/
líquido, juros de mora, honorários sucumbenciais, honorários co ntratuais e demais verbas, e cópia do contrato nos autos deste 
Cumprimento de Sentença antes do peticionamento eletrônico do i ncidente processual, a fim de possibilitar o exercício da ampla  
defesa e do contraditório. 4) Individualização de requisitórios : Havendo mais de um credor, os ofícios de requisição deverão 
ser expedidos de modo individual por credor em requisições sepa radas, na proporção devida a cada um, ainda que exista 
litisconsórcio, bem como a planilha de cálculos e a documentaçã o necessária igualmente deverão ser apresentadas de forma 
individualizada por credor, nos termos da Portaria nº 9.622/201 8 (D.J.E. de 08/06/18) e do Comunicado Conjunto nº 1.212/2018 
(D.J.E. de 22/06/18), que regulamentam a expedição dos requisit órios de pagamento no âmbito deste Tribunal. Para tanto, 
deverão os(as) exequentes apresentar, antes do peticionamento e letrônico do incidente processual e nos autos do Cumprimento 
de Sentença contra a Fazenda Pública, a competente planilha de cálculo, com a exata separação das verbas, individualizadas 
por credor, a fim de possibilitar a correta aferição pela parte  contrária e por este Juízo do quinhão cabente a cada requerent e ou 
litisconsorte. 5) Disposições finais: Defiro o prazo de 30 (tri nta) dias para cumprimento. Devidamente instaurados os incident es"""

# Remover quebras de linha e espaços extras
clean_content = " ".join(content.split())

print(f"Conteúdo original: {len(content)} chars")
print(f"Conteúdo limpo: {len(clean_content)} chars")

# Testar com conteúdo limpo
payload = {
    "processNumber": "0000007-00.2024.8.26.0001",
    "availabilityDate": "2025-06-15T19:01:41.356Z",
    "authors": ["Veriss Imo Ursulino Do Nascimento"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": clean_content,
    "status": "NOVA",
    "scrapingSource": "DJE-SP",
    "caderno": "3",
    "instancia": "1",
    "local": "Capital",
    "parte": "1",
    "lawyers": [],
    "extractionMetadata": {"test": "value"},
}

print(f"\nTamanho do JSON: {len(json.dumps(payload))} chars")
print(f"Primeiros 200 chars do conteúdo: {clean_content[:200]}...")
