#!/usr/bin/env python3
"""
Scraper DJE-SP com Playwright
Executa scraping por período de datas extraindo informações de RPV e pagamentos pelo INSS
"""

import asyncio
import click
import re
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import PyPDF2
from playwright.async_api import async_playwright, Page, Browser

# Adicionar o src ao path para imports
import sys

sys.path.append(str(Path(__file__).parent / "src"))

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.files.report_json_saver import ReportJsonSaver
from infrastructure.logging.logger import setup_logger
from decimal import Decimal

logger = setup_logger(__name__)


class DJEScraperPlaywright:
    """Scraper principal usando Playwright"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.json_saver = ReportJsonSaver()
        self.temp_dir = tempfile.mkdtemp()

    async def setup_browser(self):
        """Configura o browser Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Para debug, mude para True em produção
            downloads_path=self.temp_dir,
        )
        self.page = await self.browser.new_page()

        # Configurar timeouts
        self.page.set_default_timeout(30000)

        logger.info("🌐 Browser Playwright configurado")

    async def close_browser(self):
        """Fecha o browser"""
        if self.browser:
            await self.browser.close()

    async def scrape_by_date_range(
        self, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Executa scraping por período de datas

        Args:
            start_date: Data início (YYYY-MM-DD)
            end_date: Data fim (YYYY-MM-DD)

        Returns:
            Estatísticas da execução
        """
        stats = {
            "total_days": 0,
            "successful_days": 0,
            "total_publications": 0,
            "successful_publications": 0,
            "failed_publications": 0,
            "errors": [],
        }

        try:
            await self.setup_browser()

            # Converter strings para datetime
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
            final_date = datetime.strptime(end_date, "%Y-%m-%d")

            while current_date <= final_date:
                date_str = current_date.strftime("%d/%m/%Y")
                stats["total_days"] += 1

                logger.info(f"📅 Processando data: {date_str}")

                try:
                    day_stats = await self.scrape_single_date(date_str)
                    stats["successful_days"] += 1
                    stats["total_publications"] += day_stats["total_found"]
                    stats["successful_publications"] += day_stats["successful"]
                    stats["failed_publications"] += day_stats["failed"]

                    logger.info(
                        f"✅ Data {date_str} processada - {day_stats['successful']} publicações salvas"
                    )

                except Exception as e:
                    error_msg = f"Erro ao processar data {date_str}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

                # Próxima data
                current_date += timedelta(days=1)

                # Pequena pausa entre datas
                await asyncio.sleep(2)

        finally:
            await self.close_browser()
            # Limpar arquivos temporários
            await self._cleanup_temp_files()

        return stats

    async def scrape_single_date(self, date_str: str) -> Dict[str, int]:
        """
        Executa scraping para uma data específica

        Args:
            date_str: Data no formato DD/MM/YYYY

        Returns:
            Estatísticas do dia
        """
        stats = {"total_found": 0, "successful": 0, "failed": 0}

        # 1. Acessar página de busca avançada
        await self.page.goto(
            "https://dje.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada"
        )
        await self.page.wait_for_load_state("domcontentloaded")

        # 2. Preencher formulário de pesquisa
        await self._fill_search_form(date_str)

        # 3. Executar busca
        await self.page.click('input[name="dadosConsulta.pesquisaLivre"]')
        await self.page.wait_for_timeout(3000)

        # 4. Verificar se há resultados
        if not await self._has_search_results():
            logger.info(f"📭 Nenhum resultado encontrado para {date_str}")
            return stats

        # 5. Processar resultados
        publication_links = await self._get_publication_links()
        stats["total_found"] = len(publication_links)

        for i, link in enumerate(publication_links):
            try:
                logger.info(f"📄 Processando publicação {i+1}/{len(publication_links)}")
                publication = await self._process_publication(link, date_str)

                if publication:
                    # Salvar como JSON
                    saved_path = await self.json_saver.save_publication_json(
                        publication
                    )
                    if saved_path:
                        stats["successful"] += 1
                        logger.info(
                            f"💾 Publicação salva: {publication.process_number}"
                        )
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                logger.error(f"❌ Erro ao processar publicação {i+1}: {e}")
                stats["failed"] += 1

        return stats

    async def _fill_search_form(self, date_str: str):
        """Preenche o formulário de busca avançada"""

        # Desbloquear e preencher campo data início
        await self.page.evaluate(
            'document.getElementById("dtInicioString").removeAttribute("readonly")'
        )
        await self.page.fill("#dtInicioString", date_str)

        # Desbloquear e preencher campo data fim
        await self.page.evaluate(
            'document.getElementById("dtFimString").removeAttribute("readonly")'
        )
        await self.page.fill("#dtFimString", date_str)

        # Selecionar caderno 12
        await self.page.select_option("#cadernos", "12")

        # Preencher termo de busca
        search_term = '"RPV" e "pagamento pelo INSS"'
        await self.page.fill('input[name="dadosConsulta.pesquisaLivre"]', search_term)

        logger.info(f"📝 Formulário preenchido para {date_str}")

    async def _has_search_results(self) -> bool:
        """Verifica se a busca retornou resultados"""
        try:
            # Aguardar elementos aparecerem
            await self.page.wait_for_timeout(2000)

            # Verificar se div de resultados existe
            results_div = await self.page.query_selector("#divResultadosSuperior")
            if not results_div:
                return False

            # Verificar se não há mensagem de "nenhum registro"
            no_results = await self.page.query_selector(
                '.ementaClass:has-text("Não foi encontrado nenhum registro")'
            )
            if no_results:
                return False

            return True

        except Exception:
            return False

    async def _get_publication_links(self) -> List[str]:
        """Obtém links para download dos PDFs das publicações"""
        links = []

        try:
            # Aguardar resultados carregarem
            await self.page.wait_for_selector("#divResultadosInferior tr.ementaClass")

            # Buscar todos os links de visualização
            link_elements = await self.page.query_selector_all(
                'tr.ementaClass a.layout[title="Visualizar"]'
            )

            for element in link_elements:
                href = await element.get_attribute("href")
                if href:
                    # Converter para URL absoluta se necessário
                    if href.startswith("/"):
                        href = f"https://dje.tjsp.jus.br{href}"
                    links.append(href)

            logger.info(f"🔗 Encontrados {len(links)} links de publicações")

        except Exception as e:
            logger.error(f"❌ Erro ao obter links: {e}")

        return links

    async def _process_publication(
        self, pdf_link: str, date_str: str
    ) -> Optional[Publication]:
        """
        Processa uma publicação completa

        Args:
            pdf_link: Link para o PDF da publicação
            date_str: Data da busca

        Returns:
            Objeto Publication ou None se falhou
        """
        try:
            # 1. Baixar e processar PDF
            pdf_path = await self._download_pdf(pdf_link)
            if not pdf_path:
                return None

            # 2. Extrair dados do PDF
            pdf_data = await self._extract_pdf_data(pdf_path)
            if not pdf_data:
                return None

            # 3. Buscar dados adicionais no ESAJ
            esaj_data = await self._get_esaj_data(pdf_data["process_number"])
            if not esaj_data:
                return None

            # 4. Criar objeto Publication
            publication = await self._create_publication(pdf_data, esaj_data, date_str)

            return publication

        except Exception as e:
            logger.error(f"❌ Erro ao processar publicação: {e}")
            return None

    async def _download_pdf(self, pdf_link: str) -> Optional[str]:
        """Baixa PDF da publicação"""
        try:
            # Criar nova aba para download
            new_page = await self.browser.new_page()

            # Configurar para download
            async with new_page.expect_download() as download_info:
                await new_page.goto(pdf_link)

            download = await download_info.value

            # Salvar arquivo
            pdf_filename = f"pub_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
            pdf_path = Path(self.temp_dir) / pdf_filename
            await download.save_as(pdf_path)

            await new_page.close()

            logger.info(f"📥 PDF baixado: {pdf_filename}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"❌ Erro ao baixar PDF: {e}")
            return None

    async def _extract_pdf_data(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Extrai dados do PDF"""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page in pdf_reader.pages:
                    text += page.extract_text()

            # Buscar número do processo
            process_number = self._extract_process_number(text)
            if not process_number:
                logger.warning("❌ Número do processo não encontrado no PDF")
                return None

            # Buscar autores
            authors = self._extract_authors(text)
            if not authors:
                logger.warning("❌ Autores não encontrados no PDF")
                return None

            return {
                "process_number": process_number,
                "authors": authors,
                "pdf_content": text,
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do PDF: {e}")
            return None

    def _extract_process_number(self, text: str) -> Optional[str]:
        """Extrai número do processo do texto do PDF"""
        try:
            # Buscar por "RPV" ou "pagamento pelo INSS"
            rpv_pattern = r"(RPV|pagamento pelo INSS)"
            matches = list(re.finditer(rpv_pattern, text, re.IGNORECASE))

            if not matches:
                return None

            # Para cada match, buscar número do processo anterior
            process_pattern = r"Processo\s+(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})"

            for match in matches:
                # Buscar no texto antes da posição do match
                text_before = text[: match.start()]

                # Buscar último número de processo antes da posição
                process_matches = list(re.finditer(process_pattern, text_before))
                if process_matches:
                    return process_matches[-1].group(1)

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair número do processo: {e}")
            return None

    def _extract_authors(self, text: str) -> List[str]:
        """Extrai autores do texto do PDF"""
        try:
            # Buscar padrão "- Nome - Vistos"
            pattern = r"-\s+([^-]+?)\s+-\s+Vistos"
            matches = re.findall(pattern, text)

            authors = []
            for match in matches:
                author = match.strip()
                if author and author not in authors:
                    authors.append(author)

            return authors

        except Exception as e:
            logger.error(f"❌ Erro ao extrair autores: {e}")
            return []

    async def _get_esaj_data(self, process_number: str) -> Optional[Dict[str, Any]]:
        """Busca dados adicionais no ESAJ"""
        try:
            # Dividir número do processo
            parts = process_number.split(".8.26.")
            if len(parts) != 2:
                logger.error(f"❌ Formato de processo inválido: {process_number}")
                return None

            numero_digito = parts[0]
            foro_numero = parts[1]

            # Acessar ESAJ
            await self.page.goto("https://esaj.tjsp.jus.br/cpopg/open.do")
            await self.page.wait_for_load_state("domcontentloaded")

            # Preencher formulário
            await self.page.fill("#numeroDigitoAnoUnificado", numero_digito)
            await self.page.fill("#foroNumeroUnificado", foro_numero)

            # Clicar no botão de consulta
            await self.page.click("#botaoConsultarProcessos")
            await self.page.wait_for_timeout(3000)

            # Clicar em movimentações
            await self.page.click("#linkmovimentacoes")
            await self.page.wait_for_timeout(2000)

            # Buscar informações necessárias
            publication_date = await self._extract_publication_date()
            content_data = await self._extract_content_data()

            if not content_data:
                logger.warning(
                    f"❌ Dados de conteúdo não encontrados para {process_number}"
                )
                return None

            return {
                "publication_date": publication_date,
                "content": content_data["content"],
                "lawyers": content_data["lawyers"],
                "gross_value": content_data["gross_value"],
                "net_value": content_data["net_value"],
                "interest_value": content_data["interest_value"],
                "attorney_fees": content_data["attorney_fees"],
            }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados no ESAJ: {e}")
            return None

    async def _extract_publication_date(self) -> Optional[datetime]:
        """Extrai data de publicação"""
        try:
            # Buscar TD com "Certidão de Publicação Expedida"
            td_element = await self.page.query_selector(
                'td.descricaoMovimentacao:has-text("Certidão de Publicação Expedida")'
            )

            if not td_element:
                return None

            # Buscar SPAN dentro do TD
            span_element = await td_element.query_selector("span")
            if not span_element:
                return None

            span_text = await span_element.inner_text()

            # Extrair data após "Data da Publicação: "
            date_match = re.search(
                r"Data da Publicação:\s*(\d{2}/\d{2}/\d{4})", span_text
            )
            if date_match:
                date_str = date_match.group(1)
                return datetime.strptime(date_str, "%d/%m/%Y")

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair data de publicação: {e}")
            return None

    async def _extract_content_data(self) -> Optional[Dict[str, Any]]:
        """Extrai dados do conteúdo da movimentação"""
        try:
            # Buscar TD com "Remetido ao DJE"
            td_element = await self.page.query_selector(
                'td.descricaoMovimentacao:has-text("Remetido ao DJE")'
            )

            if not td_element:
                return None

            # Buscar SPAN dentro do TD
            span_element = await td_element.query_selector("span")
            if not span_element:
                return None

            content = await span_element.inner_text()

            # Sanitizar conteúdo
            sanitized_content = self._sanitize_content(content)

            # Extrair dados do conteúdo
            lawyers = self._extract_lawyers_from_content(sanitized_content)
            values = self._extract_values_from_content(sanitized_content)

            return {
                "content": sanitized_content,
                "lawyers": lawyers,
                "gross_value": values.get("gross_value"),
                "net_value": values.get("net_value"),
                "interest_value": values.get("interest_value"),
                "attorney_fees": values.get("attorney_fees"),
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do conteúdo: {e}")
            return None

    def _sanitize_content(self, content: str) -> str:
        """Sanitiza conteúdo removendo caracteres perigosos e normalizando"""
        if not content:
            return ""

        # Remover caracteres perigosos para SQL injection
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        sanitized = content

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        # Substituir quebras de linha por espaços
        sanitized = re.sub(r"\s+", " ", sanitized)

        # Remover espaços duplos
        sanitized = re.sub(r"\s{2,}", " ", sanitized)

        return sanitized.strip()

    def _extract_lawyers_from_content(self, content: str) -> List[Lawyer]:
        """Extrai advogados do conteúdo"""
        lawyers = []

        try:
            # Buscar padrão "Advogados(s): Nome (OAB XXXXX/SP)"
            pattern = r"Advogados?\([^)]*\):\s*([^(]+)\s*\(([^)]+)\)"
            matches = re.findall(pattern, content)

            for name, oab in matches:
                name = name.strip()
                oab = oab.strip()

                if name and oab:
                    lawyers.append(Lawyer(name=name, oab=oab))

        except Exception as e:
            logger.error(f"❌ Erro ao extrair advogados: {e}")

        return lawyers

    def _extract_values_from_content(
        self, content: str
    ) -> Dict[str, Optional[MonetaryValue]]:
        """Extrai valores monetários do conteúdo"""
        values = {
            "gross_value": None,
            "net_value": None,
            "interest_value": None,
            "attorney_fees": None,
        }

        try:
            # Valor bruto: entre "parcelas: " e " - principal"
            gross_match = re.search(
                r"parcelas:\s*R\$\s*([\d.,]+)\s*-\s*principal", content
            )
            if gross_match:
                value = self._parse_monetary_value(gross_match.group(1))
                values["gross_value"] = values["net_value"] = MonetaryValue.from_real(
                    value
                )

            # Juros: antes de " - juros moratórios"
            interest_match = re.search(
                r"R\$\s*([\d.,]+)\s*-\s*juros moratórios", content
            )
            if interest_match:
                value = self._parse_monetary_value(interest_match.group(1))
                values["interest_value"] = MonetaryValue.from_real(value)

            # Honorários: antes de " - honorários advocatícios"
            fees_match = re.search(
                r"R\$\s*([\d.,]+)\s*-\s*honorários advocatícios", content
            )
            if fees_match:
                value = self._parse_monetary_value(fees_match.group(1))
                values["attorney_fees"] = MonetaryValue.from_real(value)

        except Exception as e:
            logger.error(f"❌ Erro ao extrair valores: {e}")

        return values

    def _parse_monetary_value(self, value_str: str) -> Decimal:
        """Converte string de valor monetário para Decimal"""
        # Remover separadores de milhares e converter vírgula para ponto
        clean_value = value_str.replace(".", "").replace(",", ".")
        return Decimal(clean_value)

    async def _create_publication(
        self, pdf_data: Dict[str, Any], esaj_data: Dict[str, Any], date_str: str
    ) -> Publication:
        """Cria objeto Publication com todos os dados"""

        # Converter data
        availability_date = datetime.strptime(date_str, "%d/%m/%Y")

        return Publication(
            process_number=pdf_data["process_number"],
            authors=pdf_data["authors"],
            publication_date=esaj_data.get("publication_date"),
            availability_date=availability_date,
            defendant="Instituto Nacional do Seguro Social - INSS",
            lawyers=esaj_data.get("lawyers", []),
            gross_value=esaj_data.get("gross_value"),
            net_value=esaj_data.get("net_value"),
            interest_value=esaj_data.get("interest_value"),
            attorney_fees=esaj_data.get("attorney_fees"),
            content=esaj_data.get("content", ""),
            status="NOVA",
            scraping_source="DJE-SP",
            caderno="12",
            instancia="1",
            local="Capital",
            parte="1",
        )

    async def _cleanup_temp_files(self):
        """Remove arquivos temporários"""
        try:
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("🧹 Arquivos temporários removidos")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar arquivos temporários: {e}")


@click.group()
def cli():
    """DJE Scraper com Playwright"""
    pass


@cli.command()
@click.option("--start-date", required=True, help="Data início (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="Data fim (YYYY-MM-DD)")
def run(start_date: str, end_date: str):
    """Executa scraping por período de datas"""

    click.echo("🚀 Iniciando DJE Scraper com Playwright")
    click.echo(f"📅 Período: {start_date} até {end_date}")

    async def execute_scraping():
        scraper = DJEScraperPlaywright()

        try:
            stats = await scraper.scrape_by_date_range(start_date, end_date)

            click.echo("\n📊 Resultados da Execução:")
            click.echo(
                f"   📅 Dias processados: {stats['successful_days']}/{stats['total_days']}"
            )
            click.echo(f"   📄 Publicações encontradas: {stats['total_publications']}")
            click.echo(f"   ✅ Publicações salvas: {stats['successful_publications']}")
            click.echo(f"   ❌ Falhas: {stats['failed_publications']}")

            if stats["errors"]:
                click.echo("\n❌ Erros encontrados:")
                for error in stats["errors"]:
                    click.echo(f"   - {error}")

        except Exception as e:
            click.echo(f"❌ Erro durante execução: {e}")
            raise

    asyncio.run(execute_scraping())


if __name__ == "__main__":
    cli()
