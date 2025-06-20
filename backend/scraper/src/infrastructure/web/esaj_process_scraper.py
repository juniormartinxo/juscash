"""
Scraper para consulta individual de processos no e-SAJ TJSP
Extrai dados detalhados de cada processo específico
"""

import re
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from playwright.async_api import Browser, Page

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class ESAJProcessScraper:
    """
    Scraper para consulta individual de processos no e-SAJ
    """

    def __init__(self, browser: Browser):
        self.browser = browser
        self.settings = get_settings()
        self.base_url = "https://esaj.tjsp.jus.br/cpopg/open.do"

    async def scrape_process_details(
        self, process_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai dados detalhados de um processo específico

        Args:
            process_number: Número do processo (ex: 0009027-08.2024.8.26.0053)

        Returns:
            Dicionário com dados do processo ou None se erro
        """
        logger.info(f"🔍 Iniciando consulta do processo: {process_number}")

        # Validar formato do número do processo
        if not self._validate_process_number(process_number):
            logger.error(f"❌ Formato inválido do número do processo: {process_number}")
            return None

        # Extrair partes do número do processo
        process_parts = self._parse_process_number(process_number)
        if not process_parts:
            logger.error(
                f"❌ Não foi possível extrair partes do processo: {process_number}"
            )
            return None

        page = await self.browser.new_page()

        try:
            # 1. Navegar para página de consulta
            await self._navigate_to_search_page(page)

            # 2. Preencher formulário de busca
            await self._fill_search_form(page, process_parts)

            # 3. Extrair dados da página de detalhes
            process_data = await self._extract_process_data(page, process_number)

            logger.info(
                f"✅ Dados extraídos com sucesso para processo: {process_number}"
            )
            return process_data

        except Exception as error:
            logger.error(f"❌ Erro ao consultar processo {process_number}: {error}")
            return None

        finally:
            await page.close()

    def _validate_process_number(self, process_number: str) -> bool:
        """
        Valida formato do número do processo
        Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
        """
        pattern = r"^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$"
        return bool(re.match(pattern, process_number))

    def _parse_process_number(self, process_number: str) -> Optional[Dict[str, str]]:
        """
        Extrai partes do número do processo
        Ex: 0009027-08.2024.8.26.0053 -> {'first': '0009027-08.2024', 'third': '0053'}
        """
        try:
            # Padrão: NNNNNNN-DD.AAAA.J.TR.OOOO
            match = re.match(
                r"^(\d{7}-\d{2}\.\d{4})\.\d{1}\.\d{2}\.(\d{4})$", process_number
            )
            if match:
                return {
                    "first": match.group(1),  # 0009027-08.2024
                    "third": match.group(2),  # 0053
                }
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao extrair partes do processo: {e}")
            return None

    async def _navigate_to_search_page(self, page: Page) -> None:
        """
        Navega para página de consulta do e-SAJ
        """
        logger.info(f"📍 Navegando para {self.base_url}")

        await page.goto(self.base_url, wait_until="networkidle")
        await page.wait_for_load_state("domcontentloaded")

        logger.info("✅ Página de consulta carregada")

    async def _fill_search_form(
        self, page: Page, process_parts: Dict[str, str]
    ) -> None:
        """
        Preenche formulário de busca com dados do processo
        """
        logger.info("📝 Preenchendo formulário de consulta...")

        try:
            # Aguardar formulário carregar
            await page.wait_for_selector(
                'input[name="numeroDigitoAnoUnificado"]', timeout=10000
            )

            # Preencher primeiro campo (NNNNNNN-DD.AAAA)
            first_field = process_parts["first"]
            await page.fill('input[name="numeroDigitoAnoUnificado"]', first_field)
            logger.info(f"✅ Primeiro campo preenchido: {first_field}")

            # O segundo campo já vem preenchido com "8.26" - não alterar

            # Preencher terceiro campo (OOOO)
            third_field = process_parts["third"]
            await page.fill('input[name="foroNumeroUnificado"]', third_field)
            logger.info(f"✅ Terceiro campo preenchido: {third_field}")

            # Clicar no botão Consultar
            await page.click('input[value="Consultar"]')
            logger.info("🔍 Clicou em Consultar")

            # Aguardar página de resultados carregar
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Aguardar carregamento completo

            logger.info("✅ Formulário preenchido e submetido com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao preencher formulário: {e}")
            raise

    async def _extract_process_data(
        self, page: Page, process_number: str
    ) -> Dict[str, Any]:
        """
        Extrai dados detalhados da página do processo
        """
        logger.info("📊 Extraindo dados do processo...")

        # Expandir movimentações
        await self._expand_movimentacoes(page)

        # Extrair dados das diferentes seções
        process_data = {
            "process_number": process_number,
            "extraction_timestamp": datetime.now().isoformat(),
            "parties": await self._extract_parties_data(page),
            "movements": await self._extract_movements_data(page),
            "calculation_details": await self._extract_calculation_details(page),
        }

        logger.info("✅ Dados extraídos com sucesso")
        return process_data

    async def _expand_movimentacoes(self, page: Page) -> None:
        """
        Expande seção de movimentações clicando no botão
        """
        try:
            logger.info("🔽 Expandindo movimentações...")

            # Procurar e clicar no botão de expandir movimentações
            expand_button = await page.query_selector("#setasDireitamovimentacoes")
            if expand_button:
                await expand_button.click()
                await asyncio.sleep(2)  # Aguardar expansão
                logger.info("✅ Movimentações expandidas")
            else:
                logger.warning("⚠️ Botão de expandir movimentações não encontrado")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao expandir movimentações: {e}")

    async def _extract_parties_data(self, page: Page) -> Dict[str, Any]:
        """
        Extrai dados das partes do processo
        """
        logger.info("👥 Extraindo dados das partes...")

        parties_data = {"authors": [], "lawyers": []}

        try:
            # Procurar seção "PARTES DO PROCESSO"
            parties_section = await page.query_selector("text=PARTES DO PROCESSO")
            if parties_section:
                # Extrair dados do autor (Requerente)
                author_elements = await page.query_selector_all("text=Requerente")
                for element in author_elements:
                    # Buscar texto próximo que contém o nome do autor
                    parent = await element.query_selector("xpath=..")
                    if parent:
                        text = await parent.text_content()
                        # Extrair nome do autor (lógica pode precisar de ajuste)
                        author_name = self._extract_author_name(text)
                        if author_name:
                            parties_data["authors"].append(author_name)

                # Extrair advogados - buscar todo o conteúdo da página
                parties_content = await page.text_content("body")
                if parties_content:
                    lawyers = self._extract_lawyers_from_content(parties_content)

                    # Buscar OABs nas movimentações "Remetido ao DJE"
                    oab_info = await self._extract_oab_from_movements(page)
                    if oab_info:
                        # Combinar informações de OAB com os nomes dos advogados
                        lawyers = self._combine_lawyers_with_oab(lawyers, oab_info)

                    parties_data["lawyers"] = lawyers

            logger.info(
                f"✅ Extraídas {len(parties_data['authors'])} partes e {len(parties_data['lawyers'])} advogados"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados das partes: {e}")

        return parties_data

    async def _extract_movements_data(self, page: Page) -> Dict[str, Any]:
        """
        Extrai dados das movimentações do processo
        """
        logger.info("📋 Extraindo dados das movimentações...")

        movements_data = {
            "publication_date": None,
            "availability_date": None,
            "homologation_details": None,
        }

        try:
            # 1. Procurar "Certidão de Publicação Expedida"
            publication_elements = await page.query_selector_all("td.dataMovimentacao")
            for element in publication_elements:
                text = await element.text_content()
                if "Certidão de Publicação Expedida" in text:
                    # Buscar span com data da publicação
                    spans = await element.query_selector_all("span")
                    for span in spans:
                        span_text = await span.text_content()
                        if "Data da Publicação:" in span_text:
                            pub_date = self._extract_publication_date(span_text)
                            if pub_date:
                                movements_data["publication_date"] = pub_date
                                logger.info(
                                    f"✅ Data de publicação encontrada: {pub_date}"
                                )

            # 2. Procurar "Homologado o Cálculo"
            calc_elements = await page.query_selector_all("a.linkMovVincProc")
            for element in calc_elements:
                text = await element.text_content()
                if "Homologado o Cálculo" in text:
                    # Buscar span com detalhes do cálculo
                    parent = await element.query_selector("xpath=..")
                    if parent:
                        spans = await parent.query_selector_all("span")
                        for span in spans:
                            span_text = await span.text_content()
                            calc_details = self._extract_calculation_values(span_text)
                            if calc_details:
                                movements_data["homologation_details"] = calc_details
                                logger.info("✅ Detalhes de cálculo encontrados")

                    # Buscar data de disponibilidade no TD anterior
                    prev_td = await element.query_selector(
                        'xpath=../../preceding-sibling::tr[1]/td[@class="dataMovimentacao"]'
                    )
                    if prev_td:
                        date_text = await prev_td.text_content()
                        avail_date = self._extract_availability_date(date_text)
                        if avail_date:
                            movements_data["availability_date"] = avail_date
                            logger.info(
                                f"✅ Data de disponibilidade encontrada: {avail_date}"
                            )

        except Exception as e:
            logger.error(f"❌ Erro ao extrair movimentações: {e}")

        return movements_data

    async def _extract_calculation_details(
        self, page: Page
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai detalhes específicos do cálculo homologado
        """
        logger.info("💰 Extraindo detalhes do cálculo...")

        try:
            # Esta função pode ser expandida para extrair mais detalhes
            # Por enquanto, retorna None pois os dados já são extraídos em _extract_movements_data
            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair detalhes do cálculo: {e}")
            return None

    def _extract_author_name(self, text: str) -> Optional[str]:
        """
        Extrai nome do autor do texto
        """
        try:
            # Implementar lógica para extrair nome do autor
            # Esta lógica pode precisar de ajustes baseado no HTML real
            if "Requerente" in text:
                # Extrair nome após "Requerente"
                parts = text.split("Requerente")
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    # Limpar e extrair apenas o nome
                    name = re.sub(r"[^\w\s]", " ", name_part).strip()
                    return name[:100] if name else None
            return None
        except Exception:
            return None

    def _extract_lawyers_from_content(self, content: str) -> List[Dict[str, str]]:
        """
        Extrai informações dos advogados do conteúdo completo
        Busca por padrões "Advogado: NOME" ou "Advogada: NOME"
        """
        lawyers = []
        try:
            # Padrão para capturar advogados: "Advogado:" ou "Advogada:" seguido do nome
            patterns = [r"Advogado:\s*([^\n\r]+)", r"Advogada:\s*([^\n\r]+)"]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    # Limpar o nome (remover caracteres especiais desnecessários)
                    name = re.sub(r"\s+", " ", name)  # Normalizar espaços
                    name = name.split("\n")[0].strip()  # Pegar só a primeira linha

                    if name and len(name) > 2:  # Nome deve ter pelo menos 3 caracteres
                        lawyers.append(
                            {
                                "name": name,
                                "oab": "OAB/SP",  # Placeholder - pode ser extraído posteriormente
                            }
                        )
                        logger.info(f"✅ Advogado encontrado: {name}")

            # Remover duplicatas baseado no nome
            unique_lawyers = []
            seen_names = set()
            for lawyer in lawyers:
                if lawyer["name"] not in seen_names:
                    unique_lawyers.append(lawyer)
                    seen_names.add(lawyer["name"])

            return unique_lawyers

        except Exception as e:
            logger.error(f"❌ Erro ao extrair advogados: {e}")
            return []

    async def _extract_oab_from_movements(self, page: Page) -> List[Dict[str, str]]:
        """
        Extrai informações de OAB das movimentações "Remetido ao DJE"
        """
        oab_lawyers = []
        try:
            logger.info("🔍 Buscando OABs nas movimentações...")

            # Buscar TDs com class="descricaoMovimentacao" que contenham "Remetido ao DJE"
            movement_elements = await page.query_selector_all(
                "td.descricaoMovimentacao"
            )

            for element in movement_elements:
                text = await element.text_content()
                if "Remetido ao DJE" in text:
                    logger.info("✅ Encontrou movimentação 'Remetido ao DJE'")

                    # Buscar spans dentro deste TD
                    spans = await element.query_selector_all("span")
                    for span in spans:
                        span_text = await span.text_content()
                        if "Advogados(s):" in span_text:
                            logger.info("📋 Encontrou seção 'Advogados(s):'")

                            # Extrair informações dos advogados após "Advogados(s):"
                            lawyers_info = self._parse_oab_lawyers(span_text)
                            oab_lawyers.extend(lawyers_info)

                            logger.info(
                                f"✅ Extraídos {len(lawyers_info)} advogados com OAB"
                            )

            return oab_lawyers

        except Exception as e:
            logger.error(f"❌ Erro ao extrair OABs: {e}")
            return []

    def _parse_oab_lawyers(self, text: str) -> List[Dict[str, str]]:
        """
        Extrai nomes e OABs do texto após "Advogados(s):"
        """
        lawyers = []
        try:
            # Encontrar texto após "Advogados(s):"
            if "Advogados(s):" in text:
                after_lawyers = text.split("Advogados(s):")[1]

                # Padrões para capturar advogados com OAB
                # Formato comum: "NOME (OAB XXXXX/SP)"
                patterns = [
                    r"([A-ZÁÊÇÕ][a-záêçõ\s]+)\s*\(OAB\s*(\d+/[A-Z]{2})\)",
                    r"([A-ZÁÊÇÕ][a-záêçõ\s]+)\s*-\s*OAB\s*(\d+/[A-Z]{2})",
                    r"([A-ZÁÊÇÕ][a-záêçõ\s]+)\s*OAB\s*(\d+/[A-Z]{2})",
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, after_lawyers, re.IGNORECASE)
                    for match in matches:
                        name = match[0].strip()
                        oab = match[1].strip()

                        if len(name) > 2:  # Nome válido
                            lawyers.append({"name": name, "oab": oab})
                            logger.info(f"✅ OAB encontrado: {name} - {oab}")

                # Se não encontrou com padrões específicos, tentar extrair manualmente
                if not lawyers:
                    logger.info("🔍 Tentando extração manual de OABs...")
                    lawyers = self._manual_oab_extraction(after_lawyers)

            return lawyers

        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse de OABs: {e}")
            return []

    def _manual_oab_extraction(self, text: str) -> List[Dict[str, str]]:
        """
        Extração manual mais flexível de advogados e OABs
        """
        lawyers = []
        try:
            # Buscar todos os números de OAB no texto
            oab_numbers = re.findall(r"(\d+/[A-Z]{2})", text)

            # Buscar nomes próximos aos números de OAB
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if any(oab in line for oab in oab_numbers):
                    # Extrair nome e OAB desta linha
                    for oab in oab_numbers:
                        if oab in line:
                            # Tentar extrair o nome antes do OAB
                            parts = line.split(oab)[0]
                            name = re.sub(r"[^\w\s]", " ", parts).strip()
                            name = " ".join(name.split())  # Normalizar espaços

                            if len(name) > 2:
                                lawyers.append({"name": name, "oab": oab})
                                logger.info(f"✅ OAB manual: {name} - {oab}")
                                break

            return lawyers

        except Exception as e:
            logger.error(f"❌ Erro na extração manual: {e}")
            return []

    def _combine_lawyers_with_oab(
        self, lawyers: List[Dict[str, str]], oab_info: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Combina informações de advogados com seus respectivos OABs
        """
        try:
            # Criar um mapa de nomes para OABs
            oab_map = {}
            for oab_lawyer in oab_info:
                name = oab_lawyer["name"].lower().strip()
                oab_map[name] = oab_lawyer["oab"]

            # Atualizar advogados com OABs encontrados
            updated_lawyers = []
            for lawyer in lawyers:
                lawyer_name = lawyer["name"].lower().strip()

                # Buscar OAB exato ou similar
                found_oab = None
                for oab_name, oab_number in oab_map.items():
                    # Comparação exata
                    if lawyer_name == oab_name:
                        found_oab = oab_number
                        break
                    # Comparação parcial (nome contém ou é contido)
                    elif lawyer_name in oab_name or oab_name in lawyer_name:
                        found_oab = oab_number
                        break

                updated_lawyers.append(
                    {
                        "name": lawyer["name"],
                        "oab": found_oab if found_oab else "OAB/SP",  # Fallback
                    }
                )

                if found_oab:
                    logger.info(f"🔗 Combinado: {lawyer['name']} -> {found_oab}")

            return updated_lawyers

        except Exception as e:
            logger.error(f"❌ Erro ao combinar advogados com OAB: {e}")
            return lawyers  # Retorna lista original em caso de erro

    def _extract_publication_date(self, text: str) -> Optional[str]:
        """
        Extrai data de publicação do texto
        """
        try:
            # Procurar padrão "Data da Publicação: DD/MM/YYYY"
            match = re.search(r"Data da Publicação:\s*(\d{2}/\d{2}/\d{4})", text)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def _extract_availability_date(self, text: str) -> Optional[str]:
        """
        Extrai data de disponibilidade do texto
        """
        try:
            # Procurar padrão de data DD/MM/YYYY
            match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def _extract_calculation_values(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai valores do cálculo do texto
        """
        try:
            calc_details = {
                "content": text,
                "gross_value": None,
                "interest_value": None,
                "attorney_fees": None,
            }

            logger.info(f"🔍 Analisando conteúdo: {text[:200]}...")

            # Padrões melhorados para capturar valores monetários
            # a) Valor bruto - múltiplos padrões
            gross_patterns = [
                r"composto pelas seguintes parcelas:\s*R?\$?\s*([\d\.,]+)",
                r"(?:valor|total|principal).*?R\$\s*([\d\.,]+)",
                r"R\$\s*([\d\.,]+).*?(?:principal|bruto|total)",
                r"(\d{1,3}(?:\.\d{3})*,\d{2})",  # Formato brasileiro padrão
            ]

            for pattern in gross_patterns:
                gross_match = re.search(pattern, text, re.IGNORECASE)
                if gross_match:
                    value = self._parse_monetary_value(gross_match.group(1))
                    if value and value > 1000:  # Valor mínimo razoável
                        calc_details["gross_value"] = value
                        logger.info(f"✅ Valor bruto encontrado: R$ {value:.2f}")
                        break

            # b) Valor dos juros - padrões melhorados
            interest_patterns = [
                r"([R$\d\.,]+)\s*-\s*juros moratórios",
                r"juros.*?R\$\s*([\d\.,]+)",
                r"(\d{1,2},\d{2})\s*-\s*juros",  # Para valores pequenos como 18,49
            ]

            for pattern in interest_patterns:
                interest_match = re.search(pattern, text, re.IGNORECASE)
                if interest_match:
                    value = self._parse_monetary_value(interest_match.group(1))
                    if value:
                        calc_details["interest_value"] = value
                        logger.info(f"✅ Valor juros encontrado: R$ {value:.2f}")
                        break

                        # c) Valor dos honorários - padrão original que funcionava
            fees_match = re.search(
                r"([R$\d\.,]+),\s*referente aos honorários advocatícios", text
            )
            if fees_match:
                value = self._parse_monetary_value(fees_match.group(1))
                if value:
                    calc_details["attorney_fees"] = value
                    logger.info(f"✅ Valor honorários encontrado: R$ {value:.2f}")

            # Se não encontrou o valor bruto pelos padrões específicos,
            # tentar capturar todos os valores e pegar o maior
            if not calc_details["gross_value"]:
                all_values = re.findall(r"R\$\s*([\d\.,]+)", text)
                all_values.extend(re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", text))

                if all_values:
                    parsed_values = []
                    for val in all_values:
                        parsed = self._parse_monetary_value(val)
                        if parsed and parsed > 1000:  # Filtrar valores muito pequenos
                            parsed_values.append(parsed)

                    if parsed_values:
                        # Pegar o maior valor como valor bruto
                        calc_details["gross_value"] = max(parsed_values)
                        logger.info(
                            f"✅ Valor bruto (maior encontrado): R$ {calc_details['gross_value']:.2f}"
                        )

            return calc_details

        except Exception as e:
            logger.error(f"❌ Erro ao extrair valores do cálculo: {e}")
            return None

    def _parse_monetary_value(self, value_str: str) -> Optional[float]:
        """
        Converte string monetária para float
        Suporta formatos: 48.754,23 | R$ 48.754,23 | 48754,23 | 1.039,75
        """
        try:
            if not value_str:
                return None

            # Remover símbolos monetários, espaços e vírgulas/pontos extras no final
            clean_value = re.sub(r"[R$\s]", "", value_str.strip())
            clean_value = re.sub(
                r"[,\.]+$", "", clean_value
            )  # Remove vírgulas/pontos no final

            # Se não tem vírgula nem ponto, assumir que são centavos
            if "," not in clean_value and "." not in clean_value:
                return (
                    float(clean_value) / 100
                    if len(clean_value) <= 4
                    else float(clean_value)
                )

            # Formato brasileiro: 48.754,23 ou 1.039,75
            if "," in clean_value:
                # Se tem ponto antes da vírgula, é separador de milhares
                if "." in clean_value and clean_value.rindex(".") < clean_value.rindex(
                    ","
                ):
                    # Remover pontos (separadores de milhares) e trocar vírgula por ponto
                    clean_value = clean_value.replace(".", "").replace(",", ".")
                else:
                    # Apenas vírgula decimal
                    clean_value = clean_value.replace(",", ".")

            # Formato americano ou já limpo: 48754.23
            result = float(clean_value)

            logger.debug(f"💰 Convertido '{value_str}' -> {result}")
            return result

        except Exception as e:
            logger.warning(f"⚠️ Erro ao converter valor '{value_str}': {e}")
            return None
