"""
Ferramentas de debugging para o scraper
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class DebugTools:
    """
    Ferramentas para debugging do scraper
    """

    def __init__(self, debug_dir: str = "./debug"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)

        # Subdiretórios
        self.screenshots_dir = self.debug_dir / "screenshots"
        self.html_dir = self.debug_dir / "html"
        self.network_dir = self.debug_dir / "network"

        for dir_path in [self.screenshots_dir, self.html_dir, self.network_dir]:
            dir_path.mkdir(exist_ok=True)

    async def capture_page_state(self, page: Page, step_name: str) -> Dict[str, str]:
        """
        Captura estado completo da página para debugging

        Args:
            page: Página do Playwright
            step_name: Nome do passo atual

        Returns:
            Dict com caminhos dos arquivos criados
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{step_name}_{timestamp}"

        files_created = {}

        try:
            # Screenshot
            screenshot_path = self.screenshots_dir / f"{base_filename}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            files_created["screenshot"] = str(screenshot_path)

            # HTML
            html_path = self.html_dir / f"{base_filename}.html"
            html_content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            files_created["html"] = str(html_path)

            # URL atual
            files_created["url"] = page.url

            # Título da página
            files_created["title"] = await page.title()

            logger.debug(f"🐛 Estado da página capturado: {step_name}")

        except Exception as error:
            logger.error(f"❌ Erro ao capturar estado da página: {error}")

        return files_created

    async def capture_network_requests(
        self, page: Page, duration_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Captura requisições de rede por um período

        Args:
            page: Página do Playwright
            duration_seconds: Duração da captura em segundos

        Returns:
            Lista de requisições capturadas
        """
        requests_log = []

        def handle_request(request):
            try:
                request_data = {
                    "timestamp": datetime.now().isoformat(),
                    "method": request.method,
                    "url": request.url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data,
                }
                requests_log.append(request_data)
            except Exception as error:
                logger.warning(f"⚠️  Erro ao capturar requisição: {error}")

        def handle_response(response):
            try:
                # Encontrar requisição correspondente
                for req_data in reversed(requests_log):
                    if req_data["url"] == response.url:
                        req_data["response"] = {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "timestamp": datetime.now().isoformat(),
                        }
                        break
            except Exception as error:
                logger.warning(f"⚠️  Erro ao capturar resposta: {error}")

        # Registrar listeners
        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            logger.info(f"🕷️  Capturando requisições por {duration_seconds}s...")
            await asyncio.sleep(duration_seconds)

            # Salvar log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = self.network_dir / f"network_log_{timestamp}.json"

            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(requests_log, f, indent=2, ensure_ascii=False)

            logger.info(f"📋 {len(requests_log)} requisições capturadas: {log_path}")

        finally:
            # Remover listeners
            page.remove_listener("request", handle_request)
            page.remove_listener("response", handle_response)

        return requests_log

    async def extract_page_elements(
        self, page: Page, selectors: List[str]
    ) -> Dict[str, Any]:
        """
        Extrai elementos específicos da página para análise

        Args:
            page: Página do Playwright
            selectors: Lista de seletores CSS para extrair

        Returns:
            Dict com elementos extraídos
        """
        elements_data = {
            "url": page.url,
            "title": await page.title(),
            "timestamp": datetime.now().isoformat(),
            "elements": {},
        }

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                elements_info = []

                for i, element in enumerate(elements[:10]):  # Limitar a 10 elementos
                    try:
                        element_info = {
                            "index": i,
                            "text": await element.inner_text(),
                            "html": await element.inner_html(),
                            "visible": await element.is_visible(),
                            "bounding_box": await element.bounding_box(),
                        }
                        elements_info.append(element_info)
                    except Exception as error:
                        logger.warning(f"⚠️  Erro ao extrair elemento {i}: {error}")

                elements_data["elements"][selector] = {
                    "count": len(elements),
                    "elements": elements_info,
                }

            except Exception as error:
                logger.error(f"❌ Erro ao extrair seletor '{selector}': {error}")
                elements_data["elements"][selector] = {"error": str(error)}

        # Salvar extração
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extraction_path = self.debug_dir / f"elements_extraction_{timestamp}.json"

        with open(extraction_path, "w", encoding="utf-8") as f:
            json.dump(elements_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"🔍 Elementos extraídos: {extraction_path}")

        return elements_data

    def analyze_content_patterns(self, content: str) -> Dict[str, Any]:
        """
        Analisa padrões no conteúdo para debugging

        Args:
            content: Conteúdo de texto para analisar

        Returns:
            Dict com análise de padrões
        """
        analysis = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.splitlines()),
            "timestamp": datetime.now().isoformat(),
        }

        # Análise de caracteres
        char_analysis = {
            "alphanumeric": sum(1 for c in content if c.isalnum()),
            "whitespace": sum(1 for c in content if c.isspace()),
            "punctuation": sum(1 for c in content if c in ".,;:!?"),
            "digits": sum(1 for c in content if c.isdigit()),
            "uppercase": sum(1 for c in content if c.isupper()),
            "lowercase": sum(1 for c in content if c.islower()),
        }

        analysis["character_distribution"] = char_analysis

        # Padrões comuns
        import re

        patterns = {
            "process_numbers": len(
                re.findall(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", content)
            ),
            "dates": len(re.findall(r"\d{1,2}/\d{1,2}/\d{4}", content)),
            "monetary_values": len(re.findall(r"[rR]\$\s*[\d.,]+", content)),
            "oab_numbers": len(re.findall(r"oab[:\s]*\d+", content, re.IGNORECASE)),
            "emails": len(
                re.findall(
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", content
                )
            ),
        }

        analysis["pattern_matches"] = patterns

        # Palavras mais comuns
        words = content.lower().split()
        word_frequency = {}
        for word in words:
            word = re.sub(r"[^\w]", "", word)  # Remover pontuação
            if len(word) > 3:  # Apenas palavras com mais de 3 caracteres
                word_frequency[word] = word_frequency.get(word, 0) + 1

        # Top 10 palavras
        top_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
        analysis["top_words"] = top_words

        return analysis

    def create_debug_report(self, session_data: Dict[str, Any]) -> str:
        """
        Cria relatório de debugging completo

        Args:
            session_data: Dados da sessão de debugging

        Returns:
            Caminho do arquivo de relatório criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.debug_dir / f"debug_report_{timestamp}.json"

        report = {
            "report_timestamp": datetime.now().isoformat(),
            "session_data": session_data,
            "system_info": {"python_version": "3.12", "scraper_version": "1.0.0"},
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Relatório de debug criado: {report_path}")

        return str(report_path)

    def cleanup_old_debug_files(self, retention_days: int = 7) -> int:
        """
        Remove arquivos de debug antigos

        Args:
            retention_days: Dias de retenção

        Returns:
            Número de arquivos removidos
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(days=retention_days)
        removed_count = 0

        for debug_subdir in [self.screenshots_dir, self.html_dir, self.network_dir]:
            for file_path in debug_subdir.glob("*"):
                file_stat = file_path.stat()
                file_created = datetime.fromtimestamp(file_stat.st_ctime)

                if file_created < cutoff_time:
                    file_path.unlink()
                    removed_count += 1

        if removed_count > 0:
            logger.info(f"🧹 Arquivos de debug removidos: {removed_count}")

        return removed_count
