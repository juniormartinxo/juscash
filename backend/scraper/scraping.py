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

    async def setup_browser(self, headless: bool = None):
        """Configura o browser Playwright"""
        playwright = await async_playwright().start()

        # Auto-detectar se está em ambiente Docker/sem display
        if headless is None:
            headless = self._should_run_headless()

        self.browser = await playwright.chromium.launch(
            headless=headless,
            downloads_path=self.temp_dir,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
        )
        self.page = await self.browser.new_page()

        # Configurar timeouts
        self.page.set_default_timeout(30000)

        mode = "headless" if headless else "com interface gráfica"
        logger.info(f"🌐 Browser Playwright configurado ({mode})")

    def _should_run_headless(self) -> bool:
        """Detecta se deve executar em modo headless"""
        import os

        # Verificar se está em Docker
        if os.path.exists("/.dockerenv"):
            return True

        # Verificar se tem DISPLAY disponível
        if not os.environ.get("DISPLAY"):
            return True

        # Verificar se está em ambiente CI
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            return True

        # Por padrão, usar headless em produção
        return True

    async def close_browser(self):
        """Fecha o browser"""
        if self.browser:
            await self.browser.close()

    async def scrape_by_date_range_internal(
        self, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Executa scraping por período de datas (método interno, browser já configurado)

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

        # 1. Acessar página de busca avançada (URL correta do projeto)
        await self.page.goto(
            "https://esaj.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada"
        )
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # 2. Preencher formulário de pesquisa
        await self._fill_search_form(date_str)

        # 3. Executar busca
        await self._execute_search()

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

        # Forçar data início usando o padrão do projeto
        data_inicio_script = f"""
        (() => {{
            const dataInicio = document.querySelector('#dtInicioString');
            if (dataInicio) {{
                dataInicio.removeAttribute('readonly');
                dataInicio.disabled = false;
                dataInicio.value = '{date_str}';
                dataInicio.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return dataInicio.value;
            }}
            return null;
        }})()
        """

        # Forçar data fim usando o padrão do projeto
        data_fim_script = f"""
        (() => {{
            const dataFim = document.querySelector('#dtFimString');
            if (dataFim) {{
                dataFim.removeAttribute('readonly');
                dataFim.disabled = false;
                dataFim.value = '{date_str}';
                dataFim.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return dataFim.value;
            }}
            return null;
        }})()
        """

        # Executar scripts para definir datas
        data_inicio_result = await self.page.evaluate(data_inicio_script)
        data_fim_result = await self.page.evaluate(data_fim_script)

        logger.info(f"📅 Data início definida: {data_inicio_result}")
        logger.info(f"📅 Data fim definida: {data_fim_result}")

        # Aguardar e selecionar caderno (seletor correto do projeto)
        await self.page.wait_for_selector(
            'select[name="dadosConsulta.cdCaderno"]', state="visible"
        )
        await self._select_caderno()

        # Preencher termo de busca (campo correto do projeto)
        search_term = '"RPV" e "pagamento pelo INSS"'
        await self._fill_search_field(search_term)

        logger.info(f"📝 Formulário preenchido para {date_str}")

    async def _select_caderno(self):
        """Seleciona o caderno correto usando o seletor do projeto"""
        try:
            # Seletor correto do projeto
            caderno_selector = 'select[name="dadosConsulta.cdCaderno"]'
            await self.page.wait_for_timeout(1000)

            # Obter todas as opções disponíveis
            options = await self.page.evaluate(
                f"""
                () => {{
                    const select = document.querySelector('{caderno_selector}');
                    if (!select) return null;
                    const options = Array.from(select.options);
                    return options.map(option => ({
                        value: option.value,
                        text: option.text
                    }));
                }}
            """
            )

            if not options:
                logger.error("❌ Nenhuma opção encontrada no campo cadernos")
                return

            logger.info(f"🔍 Opções disponíveis no caderno: {options}")

            # Usar value="12" que corresponde ao Caderno 3 (padrão do projeto)
            try:
                await self.page.select_option(caderno_selector, value="12")

                # Verificar seleção
                selected_option = await self.page.evaluate(
                    f"""
                    () => {{
                        const select = document.querySelector('{caderno_selector}');
                        const selectedOption = select.options[select.selectedIndex];
                        return {{
                            value: select.value,
                            text: selectedOption.text
                        }};
                    }}
                    """
                )

                logger.info(
                    f"✅ Caderno selecionado: {selected_option['text']} (value: {selected_option['value']})"
                )
            except Exception as e:
                logger.error(f"❌ Erro ao selecionar caderno 12: {e}")
                # Tentar primeira opção disponível
                if options:
                    first_option = options[0]["value"]
                    await self.page.select_option(caderno_selector, value=first_option)
                    logger.warning(
                        f"⚠️ Usando primeira opção disponível: {first_option}"
                    )

        except Exception as e:
            logger.error(f"❌ Erro ao selecionar caderno: {e}")
            pass

    async def _fill_search_field(self, search_term: str):
        """Preenche o campo de busca usando o seletor correto do projeto"""
        try:
            # Aguardar campo estar disponível (seletor correto do projeto)
            await self.page.wait_for_selector("#procura", timeout=10000)

            # Preencher usando JavaScript para garantir (padrão do projeto)
            keywords_script = f"""
            (() => {{
                const campo = document.querySelector('#procura');
                if (campo) {{
                    campo.value = '{search_term}';
                    campo.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    campo.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return campo.value;
                }}
                return null;
            }})()
            """

            filled_value = await self.page.evaluate(keywords_script)
            logger.info(f"✅ Palavras-chave preenchidas: '{filled_value}'")

        except Exception as e:
            logger.error(f"❌ Erro ao preencher campo de busca: {e}")

    async def _execute_search(self):
        """Executa a busca usando o padrão do projeto com múltiplos seletores"""
        try:
            # Aguardar um pouco antes de submeter
            await asyncio.sleep(2)

            # Submeter formulário com tratamento melhorado (padrão do projeto)
            submit_selectors = [
                'input[value="Pesquisar"]',
                'input[name="pbConsultar"]',
                'button:text("Pesquisar")',
                'input[type="submit"]',
                'button[type="submit"]',
                ".botaoPesquisar",
                "#pbConsultar",
                '[onclick*="consultar"]',
            ]

            submitted = False
            last_error = None

            for selector in submit_selectors:
                try:
                    # Verificar se o elemento existe
                    element = await self.page.query_selector(selector)
                    if element:
                        # Verificar se é visível e habilitado
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()

                        if is_visible and is_enabled:
                            logger.info(
                                f"🎯 Tentando submeter com selector: {selector}"
                            )
                            await element.click()

                            # Aguardar navegação ou carregamento
                            try:
                                await self.page.wait_for_load_state(
                                    "networkidle", timeout=15000
                                )
                                await asyncio.sleep(3)  # Aguardar resultados carregarem

                                # Verificar se a submissão foi bem-sucedida
                                current_url = self.page.url
                                if (
                                    "consultaAvancada" not in current_url
                                    or "resultado" in current_url.lower()
                                ):
                                    logger.info(
                                        f"✅ Formulário submetido com sucesso (selector: {selector})"
                                    )
                                    submitted = True
                                    break
                                else:
                                    logger.debug(
                                        f"⚠️ URL não mudou após submissão: {current_url}"
                                    )
                            except Exception as e:
                                logger.debug(
                                    f"⚠️ Timeout aguardando resposta para {selector}: {e}"
                                )
                                # Continuar tentando outros seletores
                        else:
                            logger.debug(
                                f"❌ Elemento {selector} não está visível ou habilitado"
                            )
                except Exception as e:
                    last_error = e
                    logger.debug(f"❌ Falha ao tentar {selector}: {e}")
                    continue

            if not submitted:
                error_msg = f"Falha ao submeter formulário. Último erro: {last_error}"
                logger.error(f"❌ {error_msg}")

                # Tentar submissão por JavaScript como último recurso
                try:
                    logger.info("🔄 Tentando submissão via JavaScript...")
                    submit_result = await self.page.evaluate(
                        """
                        () => {
                            const forms = document.querySelectorAll('form');
                            for (const form of forms) {
                                if (form.action && form.action.includes('consulta')) {
                                    form.submit();
                                    return 'Formulário submetido via JavaScript';
                                }
                            }
                            return 'Nenhum formulário encontrado';
                        }
                    """
                    )
                    logger.info(f"📝 Resultado JavaScript: {submit_result}")

                    if "submetido" in submit_result:
                        await asyncio.sleep(5)  # Aguardar mais tempo para JS
                        submitted = True
                        logger.info("✅ Formulário submetido via JavaScript")
                except Exception as js_error:
                    logger.error(f"❌ Falha na submissão JavaScript: {js_error}")

            if not submitted:
                raise Exception(error_msg)

            logger.info("✅ Pesquisa executada com critérios específicos")

        except Exception as e:
            logger.error(f"❌ Erro ao executar busca: {e}")
            raise

    async def _has_search_results(self) -> bool:
        """Verifica se a busca retornou resultados seguindo o padrão do projeto"""
        try:
            logger.info("🔍 Buscando resultados da pesquisa...")

            # Aguardar carregamento dos resultados
            await asyncio.sleep(3)

            # Tentar aguardar elementos aparecerem (padrão do projeto)
            try:
                await self.page.wait_for_selector("tr.ementaClass", timeout=10000)
                logger.info("✅ Elementos tr.ementaClass encontrados")
                return True
            except:
                logger.warning("⚠️ Timeout aguardando tr.ementaClass")

            # Verificar se há outros elementos com onclick (fallback do projeto)
            onclick_elements = await self.page.query_selector_all(
                '[onclick*="consultaSimples.do"]'
            )
            if onclick_elements:
                logger.info(
                    f"✅ Encontrados {len(onclick_elements)} elementos com consultaSimples.do"
                )
                return True

            # Verificar mensagens de "nenhum registro"
            no_results_selectors = [
                'td:has-text("Não foi encontrado nenhum registro")',
                'div:has-text("Não foi encontrado nenhum registro")',
                '*:has-text("nenhum registro")',
            ]

            for selector in no_results_selectors:
                no_results = await self.page.query_selector(selector)
                if no_results:
                    logger.info("📭 Mensagem 'nenhum registro' encontrada")
                    return False

            logger.info("📭 Nenhum resultado encontrado")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao verificar resultados: {e}")
            return False

    async def _get_publication_links(self) -> List[str]:
        """Obtém links para download dos PDFs seguindo o padrão do projeto"""
        links = []

        try:
            logger.info("🔍 Buscando links de PDF nos resultados")

            # Aguardar carregamento dos resultados
            await asyncio.sleep(3)

            # Tentar aguardar elementos aparecerem
            try:
                await self.page.wait_for_selector("tr.ementaClass", timeout=10000)
            except:
                logger.warning("⚠️ Timeout aguardando tr.ementaClass")

            # Encontrar todos os elementos tr com class="ementaClass"
            ementa_elements = await self.page.query_selector_all("tr.ementaClass")

            if not ementa_elements:
                logger.warning("⚠️ Nenhum elemento tr.ementaClass encontrado")

                # Debug: verificar se há elementos com onclick diretamente
                onclick_elements = await self.page.query_selector_all(
                    '[onclick*="consultaSimples.do"]'
                )
                logger.info(
                    f"🔍 Elementos com consultaSimples.do: {len(onclick_elements)}"
                )

                if onclick_elements:
                    logger.info(
                        "✅ Encontrados elementos com consultaSimples.do, processando diretamente..."
                    )
                    # Processar elementos com onclick diretamente
                    for element in onclick_elements:
                        try:
                            onclick_attr = await element.get_attribute("onclick")
                            if onclick_attr and "consultaSimples.do" in onclick_attr:
                                pdf_url = await self._extract_pdf_url_from_onclick(
                                    onclick_attr
                                )
                                if pdf_url:
                                    links.append(pdf_url)
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao processar elemento onclick: {e}")
                            continue

                return links

            logger.info(
                f"✅ Encontrados {len(ementa_elements)} elementos tr.ementaClass"
            )

            # Processar cada elemento para extrair links (padrão do projeto)
            for i, element in enumerate(ementa_elements):
                try:
                    # Buscar elementos com onclick que contém links para PDF
                    onclick_elements = await element.query_selector_all(
                        '[onclick*="popup"]'
                    )

                    for onclick_element in onclick_elements:
                        onclick_attr = await onclick_element.get_attribute("onclick")

                        if onclick_attr and "consultaSimples.do" in onclick_attr:
                            # Extrair URL do PDF do atributo onclick
                            pdf_url = await self._extract_pdf_url_from_onclick(
                                onclick_attr
                            )

                            if pdf_url:
                                links.append(pdf_url)

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar elemento {i + 1}: {e}")
                    continue

            logger.info(f"🔗 Encontrados {len(links)} links de PDF")

        except Exception as e:
            logger.error(f"❌ Erro ao obter links: {e}")

        return links

    async def _extract_pdf_url_from_onclick(self, onclick_attr: str) -> Optional[str]:
        """Extrai URL do PDF do atributo onclick (padrão do projeto)"""
        try:
            import re

            # Buscar padrão consultaSimples.do com parâmetros
            match = re.search(r"consultaSimples\.do\?([^'\"]+)", onclick_attr)
            if match:
                params = match.group(1)
                base_url = "https://esaj.tjsp.jus.br/cdje/consultaSimples.do"
                pdf_url = f"{base_url}?{params}"
                return pdf_url

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair URL do PDF: {e}")
            return None

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
@click.option(
    "--headless/--no-headless",
    default=None,
    help="Forçar modo headless ou com interface gráfica",
)
def run(start_date: str, end_date: str, headless: bool):
    """Executa scraping por período de datas"""

    click.echo("🚀 Iniciando DJE Scraper com Playwright")
    click.echo(f"📅 Período: {start_date} até {end_date}")

    async def execute_scraping():
        scraper = DJEScraperPlaywright()

        try:
            # Configurar browser com modo headless especificado
            await scraper.setup_browser(headless=headless)
            stats = await scraper.scrape_by_date_range_internal(start_date, end_date)

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
