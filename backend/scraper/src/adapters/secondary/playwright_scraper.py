import re
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal, InvalidOperation
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from src.core.entities.publication import Publication
from src.core.ports.scraper_port import ScraperPort
from src.shared.value_objects import ScrapingCriteria, DJEUrl, ProcessNumber, Status
from src.shared.exceptions import (
    BrowserException, NavigationException, ElementNotFoundException,
    TimeoutException, ParsingException, handle_exception
)
from src.shared.logger import get_logger

logger = get_logger(__name__)


class PlaywrightScraperAdapter(ScraperPort):
    """
    Implementação do scraping do DJE usando Playwright.
    
    Realiza navegação automatizada no site do Diário da Justiça Eletrônico
    e extrai informações das publicações conforme critérios especificados.
    """
    
    def __init__(self, 
                 headless: bool = False,
                 timeout: int = 30000,
                 user_agent: Optional[str] = None,
                 max_retries: int = 3):
        """
        Inicializa o adaptador Playwright.
        
        Args:
            headless: Se o browser deve rodar em modo headless
            timeout: Timeout padrão em milissegundos
            user_agent: User agent customizado
            max_retries: Número máximo de tentativas em caso de erro
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.max_retries = max_retries
        
        # Atributos de controle
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Seletores CSS para elementos do DJE
        self.selectors = {
            'caderno_link': 'a[href*="cdCaderno=12"]',  # Caderno 3 - Judicial - 1ª Instância
            'publication_container': '.publicacao, .item-publicacao, div[data-publicacao]',
            'publication_content': '.conteudo-publicacao, .texto-publicacao, .content',
            'process_number': '.numero-processo, .processo',
            'publication_date': '.data-publicacao, .data',
            'next_page': 'a[href*="proxima"], .proximo-pagina, .next',
            'loading_indicator': '.loading, .carregando, .spinner'
        }
    
    async def initialize(self) -> None:
        """Inicializa o browser Playwright."""
        try:
            logger.info("Inicializando Playwright...")
            
            self.playwright = await async_playwright().start()
            
            # Configurar browser Chromium
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized'
                ],
                ignore_default_args=['--enable-automation'],
                channel='chrome'
            )
            
            # Criar contexto do browser
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True
            )
            
            # Criar nova página
            self.page = await self.context.new_page()
            
            # Configurar timeouts
            self.page.set_default_timeout(self.timeout)
            self.page.set_default_navigation_timeout(self.timeout)
            
            logger.info("Playwright inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Playwright: {str(e)}")
            raise BrowserException("initialize", str(e))
    
    async def navigate_to_dje(self, url: DJEUrl) -> bool:
        """Navega para a página principal do DJE."""
        if not self.page:
            raise BrowserException("navigate", "Browser não inicializado")
        
        main_url = url.get_main_url()
        logger.info(f"Navegando para DJE: {main_url}")
        
        for attempt in range(self.max_retries):
            try:
                # Navegar para a página principal
                response = await self.page.goto(main_url, wait_until='networkidle')
                
                if not response or response.status >= 400:
                    raise NavigationException(
                        f"Erro HTTP {response.status if response else 'desconhecido'}",
                        main_url
                    )
                
                # Aguardar carregamento da página
                await self.page.wait_for_load_state('domcontentloaded')
                
                # Verificar se chegamos na página correta
                title = await self.page.title()
                if "dje" not in title.lower() and "diário" not in title.lower():
                    logger.warning(f"Título da página não esperado: {title}")
                
                logger.info("Navegação para DJE realizada com sucesso")
                return True
                
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout na tentativa {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise TimeoutException("navigate_to_dje", self.timeout // 1000)
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Erro na navegação (tentativa {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise NavigationException(f"Falha após {self.max_retries} tentativas", main_url)
                await asyncio.sleep(2)
        
        return False
    
    async def navigate_to_caderno(self, criteria: ScrapingCriteria) -> bool:
        """Navega para o caderno específico conforme critérios."""
        if not self.page:
            raise BrowserException("navigate_caderno", "Browser não inicializado")
        
        logger.info(f"Navegando para {criteria.get_caderno_description()}")
        
        try:
            # Aguardar página carregar completamente
            await self.page.wait_for_load_state('networkidle')
            
            # Procurar link do Caderno 3 - Judicial - 1ª Instância
            # Tentativas com diferentes seletores
            caderno_selectors = [
                f'a[href*="cdCaderno=12"]',  # Código específico do caderno
                f'a:has-text("Caderno {criteria.caderno}")',
                f'a:has-text("Judicial")',
                f'a:has-text("1ª Instância")',
                f'a:has-text("Capital")'
            ]
            
            caderno_link = None
            for selector in caderno_selectors:
                try:
                    caderno_link = await self.page.wait_for_selector(selector, timeout=5000)
                    if caderno_link:
                        logger.info(f"Link do caderno encontrado com seletor: {selector}")
                        break
                except:
                    continue
            
            if not caderno_link:
                # Tentar buscar manualmente por texto
                links = await self.page.query_selector_all('a')
                for link in links:
                    text = await link.inner_text()
                    if any(term in text for term in ['Caderno 3', 'Judicial', '1ª Instância', 'Capital']):
                        caderno_link = link
                        logger.info(f"Link do caderno encontrado por texto: {text}")
                        break
            
            if not caderno_link:
                raise ElementNotFoundException("Link do caderno 3", await self.page.url)
            
            # Clicar no link do caderno
            await caderno_link.click()
            
            # Aguardar navegação
            await self.page.wait_for_load_state('networkidle')
            
            # Verificar se chegamos na página do caderno
            current_url = self.page.url
            if 'cdCaderno=12' in current_url or 'caderno' in current_url.lower():
                logger.info("Navegação para caderno realizada com sucesso")
                return True
            else:
                logger.warning(f"URL não indica caderno correto: {current_url}")
                return True  # Continuar mesmo assim
                
        except PlaywrightTimeoutError:
            raise TimeoutException("navigate_to_caderno", self.timeout // 1000)
        except Exception as e:
            logger.error(f"Erro ao navegar para caderno: {str(e)}")
            raise NavigationException(f"Erro ao acessar caderno: {str(e)}")
    
    async def extract_publications(self, 
                                 criteria: ScrapingCriteria, 
                                 max_publications: Optional[int] = None) -> List[Publication]:
        """Extrai publicações da página atual que atendem aos critérios."""
        if not self.page:
            raise BrowserException("extract_publications", "Browser não inicializado")
        
        logger.info(f"Extraindo publicações com critérios: {criteria}")
        publications: List[Publication] = []
        processed_count = 0
        
        try:
            # Aguardar página carregar
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Buscar containers de publicação
            publication_elements = await self._find_publication_elements()
            
            if not publication_elements:
                logger.warning("Nenhum elemento de publicação encontrado")
                return publications
            
            logger.info(f"Encontrados {len(publication_elements)} elementos de publicação")
            
            # Processar cada publicação
            for i, element in enumerate(publication_elements):
                if max_publications and processed_count >= max_publications:
                    logger.info(f"Limite de {max_publications} publicações atingido")
                    break
                
                try:
                    # Extrair conteúdo da publicação
                    content = await self._extract_element_content(element)
                    
                    if not content or len(content.strip()) < 50:
                        logger.debug(f"Publicação {i} tem conteúdo insuficiente")
                        continue
                    
                    # Verificar se atende aos critérios de busca
                    if not criteria.matches_content(content):
                        logger.debug(f"Publicação {i} não atende aos critérios")
                        continue
                    
                    # Criar publicação básica
                    publication = Publication(
                        content=content,
                        status=Status.NEW,
                        defendant="Instituto Nacional do Seguro Social - INSS"
                    )
                    
                    # Tentar extrair informações básicas
                    await self._extract_basic_info(publication, content)
                    
                    publications.append(publication)
                    processed_count += 1
                    
                    logger.info(f"Publicação {processed_count} extraída: {publication.process_number}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar elemento {i}: {str(e)}")
                    continue
            
            logger.info(f"Extração concluída: {len(publications)} publicações válidas")
            return publications
            
        except Exception as e:
            logger.error(f"Erro durante extração de publicações: {str(e)}")
            raise ParsingException("publications", "página_atual", str(e))
    
    async def _find_publication_elements(self) -> List:
        """Encontra elementos que contêm publicações na página."""
        publication_elements = []
        
        # Tentar diferentes seletores para encontrar publicações
        selectors_to_try = [
            '.publicacao',
            '.item-publicacao', 
            'div[data-publicacao]',
            '.conteudo-publicacao',
            'div:has-text("Processo")',
            'p:has-text("Processo")',
            'div:has-text("INSS")',
            'p:has-text("INSS")',
            # Seletores mais genéricos
            'div',
            'p'
        ]
        
        for selector in selectors_to_try:
            try:
                elements = await self.page.query_selector_all(selector)
                
                # Filtrar elementos que provavelmente contêm publicações
                for element in elements:
                    text = await element.inner_text()
                    if (len(text) > 100 and 
                        ('processo' in text.lower() or 'inss' in text.lower())):
                        publication_elements.append(element)
                
                if publication_elements:
                    logger.info(f"Elementos encontrados com seletor: {selector}")
                    break
                    
            except Exception as e:
                logger.debug(f"Erro com seletor {selector}: {str(e)}")
                continue
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_elements = []
        for element in publication_elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        return unique_elements[:50]  # Limitar a 50 elementos para performance
    
    async def _extract_element_content(self, element) -> str:
        """Extrai o conteúdo textual de um elemento."""
        try:
            # Tentar diferentes métodos de extração
            methods = [
                lambda: element.inner_text(),
                lambda: element.text_content(),
                lambda: element.inner_html()
            ]
            
            for method in methods:
                try:
                    content = await method()
                    if content and len(content.strip()) > 10:
                        return content.strip()
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.debug(f"Erro ao extrair conteúdo do elemento: {str(e)}")
            return ""
    
    async def _extract_basic_info(self, publication: Publication, content: str) -> None:
        """Extrai informações básicas do conteúdo da publicação."""
        try:
            # Extrair número do processo
            process_match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})', content)
            if not process_match:
                # Tentar outros formatos
                process_match = re.search(r'(?:processo|autos)[:\s]*(\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+)', content, re.IGNORECASE)
                if not process_match:
                    process_match = re.search(r'(\d+[.\-/]\d+)', content)  # Formato mais simples
            
            if process_match:
                try:
                    publication.process_number = ProcessNumber(process_match.group(1))
                    logger.debug(f"Número do processo extraído: {publication.process_number}")
                except Exception as e:
                    logger.debug(f"Erro ao criar ProcessNumber: {str(e)}")
            
            # Extrair data de disponibilização
            date_patterns = [
                r'disponibilização[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'data[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, content, re.IGNORECASE)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        publication.availability_date = datetime.strptime(date_str, '%d/%m/%Y')
                        logger.debug(f"Data de disponibilização extraída: {publication.availability_date}")
                        break
                    except Exception as e:
                        logger.debug(f"Erro ao parsear data {date_str}: {str(e)}")
            
            # Extrair autores
            author_patterns = [
                r'autor(?:es)?[:\s]*([^,\n]+)',
                r'requerente[:\s]*([^,\n]+)',
                r'exequente[:\s]*([^,\n]+)'
            ]
            
            for pattern in author_patterns:
                author_match = re.search(pattern, content, re.IGNORECASE)
                if author_match:
                    author_name = author_match.group(1).strip()
                    if author_name and len(author_name) > 2:
                        publication.authors.append(author_name)
                        logger.debug(f"Autor extraído: {author_name}")
                        break
            
            # Extrair advogados
            lawyer_patterns = [
                r'advogad[oa][:\s]*([^,\n]+)',
                r'oab[:\s]*([^,\n]+)',
                r'dr\.?\s+([^,\n]+)'
            ]
            
            for pattern in lawyer_patterns:
                lawyer_matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in lawyer_matches:
                    lawyer_name = match.group(1).strip()
                    if lawyer_name and len(lawyer_name) > 2:
                        publication.lawyers.append(lawyer_name)
                        logger.debug(f"Advogado extraído: {lawyer_name}")
            
            # Extrair valores monetários
            self._extract_monetary_values(publication, content)
            
        except Exception as e:
            logger.debug(f"Erro ao extrair informações básicas: {str(e)}")
    
    def _extract_monetary_values(self, publication: Publication, content: str) -> None:
        """Extrai valores monetários do conteúdo."""
        try:
            # Padrões para valores monetários
            value_patterns = {
                'gross_value': [
                    r'valor\s*principal[:\s]*r?\$?\s*([\d.,]+)',
                    r'valor\s*bruto[:\s]*r?\$?\s*([\d.,]+)',
                    r'principal[:\s]*r?\$?\s*([\d.,]+)'
                ],
                'net_value': [
                    r'valor\s*líquido[:\s]*r?\$?\s*([\d.,]+)',
                    r'líquido[:\s]*r?\$?\s*([\d.,]+)'
                ],
                'interest_value': [
                    r'juros[:\s]*r?\$?\s*([\d.,]+)',
                    r'juros\s*moratórios[:\s]*r?\$?\s*([\d.,]+)'
                ],
                'attorney_fees': [
                    r'honorários[:\s]*r?\$?\s*([\d.,]+)',
                    r'honorários\s*advocatícios[:\s]*r?\$?\s*([\d.,]+)'
                ]
            }
            
            for field_name, patterns in value_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        try:
                            value_str = match.group(1).replace('.', '').replace(',', '.')
                            value = Decimal(value_str)
                            setattr(publication, field_name, value)
                            logger.debug(f"{field_name} extraído: R$ {value}")
                            break
                        except (InvalidOperation, ValueError) as e:
                            logger.debug(f"Erro ao parsear {field_name}: {str(e)}")
                            continue
            
        except Exception as e:
            logger.debug(f"Erro ao extrair valores monetários: {str(e)}")
    
    async def extract_publication_details(self, publication: Publication) -> Publication:
        """Extrai detalhes completos de uma publicação específica."""
        # Para este caso, os detalhes já foram extraídos no método extract_publications
        # Em uma implementação mais complexa, poderia navegar para uma página de detalhes
        logger.debug(f"Detalhes da publicação {publication.id} já extraídos")
        return publication
    
    async def close(self) -> None:
        """Fecha o browser e libera recursos."""
        try:
            logger.info("Fechando Playwright...")
            
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info("Playwright fechado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao fechar Playwright: {str(e)}")
            raise BrowserException("close", str(e))