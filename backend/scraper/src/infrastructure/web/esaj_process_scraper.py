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

                # Extrair advogados
                lawyer_elements = await page.query_selector_all("text=Advogado")
                for element in lawyer_elements:
                    parent = await element.query_selector("xpath=..")
                    if parent:
                        text = await parent.text_content()
                        lawyer_info = self._extract_lawyer_info(text)
                        if lawyer_info:
                            parties_data["lawyers"].append(lawyer_info)

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

    def _extract_lawyer_info(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extrai informações do advogado do texto
        """
        try:
            if "Advogado" in text:
                # Extrair nome e OAB do advogado
                # Implementar lógica específica baseada no formato do HTML
                return {
                    "name": "Nome do Advogado",  # Placeholder
                    "oab": "OAB/SP",  # Placeholder
                }
            return None
        except Exception:
            return None

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

            # a) Valor bruto após "composto pelas seguintes parcelas:"
            gross_match = re.search(
                r"composto pelas seguintes parcelas:\s*([R$\d\.,]+)", text
            )
            if gross_match:
                calc_details["gross_value"] = self._parse_monetary_value(
                    gross_match.group(1)
                )

            # b) Valor dos juros antes de "- juros moratórios"
            interest_match = re.search(r"([R$\d\.,]+)\s*-\s*juros moratórios", text)
            if interest_match:
                calc_details["interest_value"] = self._parse_monetary_value(
                    interest_match.group(1)
                )

            # c) Valor dos honorários antes de "referente aos honorários advocatícios"
            fees_match = re.search(
                r"([R$\d\.,]+),\s*referente aos honorários advocatícios", text
            )
            if fees_match:
                calc_details["attorney_fees"] = self._parse_monetary_value(
                    fees_match.group(1)
                )

            return calc_details

        except Exception as e:
            logger.error(f"❌ Erro ao extrair valores do cálculo: {e}")
            return None

    def _parse_monetary_value(self, value_str: str) -> Optional[float]:
        """
        Converte string monetária para float
        """
        try:
            # Remover símbolos e converter
            clean_value = re.sub(r"[R$\s]", "", value_str)
            clean_value = clean_value.replace(".", "").replace(",", ".")
            return float(clean_value)
        except Exception:
            return None
