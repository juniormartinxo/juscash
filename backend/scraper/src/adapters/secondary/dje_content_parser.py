"""
Arquivo: src/adapters/secondary/dje_content_parser.py

Parser especializado para extração de conteúdo das páginas do DJE.
Segue princípios da Arquitetura Hexagonal como componente de infraestrutura.

Responsabilidades:
- Extração de publicações dos resultados de pesquisa
- Parse de conteúdo das publicações individuais
- Normalização de dados extraídos
- Validação de critérios de negócio
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal, InvalidOperation
from playwright.async_api import Page, ElementHandle

from src.core.entities.publication import Publication
from src.shared.value_objects import ScrapingCriteria, ProcessNumber, Status
from src.shared.exceptions import ParsingException
from src.shared.logger import get_logger

logger = get_logger(__name__)


class DJEContentParser:
    """
    Parser para extração e processamento de conteúdo do DJE.
    
    Responsabilidade: Encapsular toda a lógica de extração e parse
    de dados específicos do DJE, transformando HTML em entidades de domínio.
    
    Princípios da Arquitetura Hexagonal:
    - Componente de infraestrutura (adapter secundário)
    - Isolamento da lógica de parsing específica do DJE
    - Transformação de dados externos em entidades de domínio
    """
    
    def __init__(self, page: Page):
        """
        Inicializa o parser de conteúdo.
        
        Args:
            page: Instância da página Playwright
        """
        self.page = page
        self.selectors = self._get_content_selectors()
        self.patterns = self._get_regex_patterns()
        
    def _get_content_selectors(self) -> Dict[str, str]:
        """
        Retorna seletores para diferentes tipos de conteúdo no DJE.
        
        Returns:
            Dict com seletores CSS organizados por tipo de conteúdo
        """
        return {
            # Resultados de pesquisa
            'search_results': 'body',
            'result_items': 'td:has-text("caderno 3")',
            'result_links': 'a:has-text("ocorrência")',
            'pagination_links': 'a:has-text("Próxima"), a:has-text("2"), a:has-text("3")',
            
            # Conteúdo das publicações
            'publication_containers': [
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
            ],
            
            # Elementos específicos
            'process_number': '.numero-processo, .processo',
            'publication_date': '.data-publicacao, .data',
            'author_info': '.autor, .requerente',
            'lawyer_info': '.advogado, .oab'
        }
    
    def _get_regex_patterns(self) -> Dict[str, List[str]]:
        """
        Retorna padrões regex para extração de dados específicos.
        
        Returns:
            Dict com padrões regex organizados por tipo de dado
        """
        return {
            # Padrões para número de processo
            'process_number': [
                r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',  # Formato padrão CNJ
                r'(?:processo|autos)[:\s]*(\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+)',
                r'(\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+[.\-/]\d+)',  # Formato mais genérico
                r'(\d+[.\-/]\d+)'  # Formato simples
            ],
            
            # Padrões para datas
            'dates': [
                r'disponibilização[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'data[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ],
            
            # Padrões para autores
            'authors': [
                r'autor(?:es)?[:\s]*([^,\n]+)',
                r'requerente[:\s]*([^,\n]+)',
                r'exequente[:\s]*([^,\n]+)'
            ],
            
            # Padrões para advogados
            'lawyers': [
                r'advogad[oa][:\s]*([^,\n]+)',
                r'oab[:\s]*(\d+[./]?\w*)',
                r'dr\.?\s+([^,\n]+)'
            ],
            
            # Padrões para valores monetários
            'monetary_values': {
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
            },
            
            # Padrões para contagem de resultados
            'result_count': [
                r'(\d+)\s+ocorrência[s]?\s+encontrada[s]?',
                r'Resultados\s+(\d+)\s+a\s+(\d+)\s+de\s+(\d+)'
            ]
        }
    
    async def extract_publications_from_results(self, 
                                              criteria: ScrapingCriteria,
                                              max_publications: Optional[int] = None) -> List[Publication]:
        """
        Extrai publicações dos resultados da pesquisa avançada.
        
        Args:
            criteria: Critérios de scraping para validação
            max_publications: Limite máximo de publicações a extrair
            
        Returns:
            List[Publication]: Lista de publicações extraídas e validadas
            
        Raises:
            ParsingException: Se erro durante extração
        """
        logger.info("📋 Extraindo publicações dos resultados da pesquisa...")
        publications: List[Publication] = []
        
        try:
            # Aguardar página carregar completamente
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Extrair metadados dos resultados
            result_metadata = await self._extract_result_metadata()
            logger.info(f"Metadados: {result_metadata}")
            
            # Buscar elementos que contêm publicações
            publication_elements = await self._find_publication_elements()
            
            if not publication_elements:
                logger.warning("Nenhum elemento de publicação encontrado")
                return publications
            
            logger.info(f"Encontrados {len(publication_elements)} elementos de publicação")
            
            # Processar cada elemento
            processed_count = 0
            for i, element in enumerate(publication_elements):
                if max_publications and processed_count >= max_publications:
                    logger.info(f"Limite de {max_publications} publicações atingido")
                    break
                
                try:
                    # Extrair conteúdo do elemento
                    content = await self._extract_element_content(element)
                    
                    if not self._is_valid_publication_content(content):
                        logger.debug(f"Elemento {i} não contém publicação válida")
                        continue
                    
                    # Verificar se atende aos critérios
                    if not criteria.matches_content(content):
                        logger.debug(f"Elemento {i} não atende aos critérios de busca")
                        continue
                    
                    # Criar publicação a partir do conteúdo
                    publication = await self._create_publication_from_content(content)
                    
                    if publication:
                        publications.append(publication)
                        processed_count += 1
                        logger.info(f"Publicação {processed_count} extraída: {publication.process_number}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar elemento {i}: {str(e)}")
                    continue
            
            logger.info(f"✅ Extração concluída: {len(publications)} publicações válidas")
            return publications
            
        except Exception as e:
            logger.error(f"❌ Erro durante extração de publicações: {str(e)}")
            raise ParsingException("extract_publications_from_results", "página_resultados", str(e))
    
    async def _extract_result_metadata(self) -> Dict[str, Any]:
        """
        Extrai metadados dos resultados da pesquisa.
        
        Returns:
            Dict com metadados dos resultados
        """
        try:
            page_content = await self.page.content()
            
            metadata = {
                'page_url': self.page.url,
                'page_title': await self.page.title(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Extrair número total de resultados
            for pattern in self.patterns['result_count']:
                match = re.search(pattern, page_content, re.IGNORECASE)
                if match:
                    if 'ocorrência' in pattern:
                        metadata['total_results'] = int(match.group(1))
                    else:  # Padrão "X a Y de Z"
                        metadata['start_result'] = int(match.group(1))
                        metadata['end_result'] = int(match.group(2))
                        metadata['total_results'] = int(match.group(3))
                    break
            
            # Verificar se há mais páginas
            has_pagination = 'Próxima' in page_content or 'próxima' in page_content
            metadata['has_pagination'] = has_pagination
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")
            return {'error': str(e)}
    
    async def _find_publication_elements(self) -> List[ElementHandle]:
        """
        Encontra elementos que contêm publicações na página.
        
        Returns:
            Lista de ElementHandle com potenciais publicações
        """
        publication_elements = []
        
        # Tentar diferentes seletores
        for selector in self.selectors['publication_containers']:
            try:
                elements = await self.page.query_selector_all(selector)
                
                # Filtrar elementos que provavelmente contêm publicações
                for element in elements:
                    try:
                        text = await element.inner_text()
                        if self._is_potential_publication_element(text):
                            publication_elements.append(element)
                    except:
                        continue
                
                if publication_elements:
                    logger.info(f"Elementos encontrados com seletor: {selector}")
                    break
                    
            except Exception as e:
                logger.debug(f"Erro com seletor {selector}: {str(e)}")
                continue
        
        # Remover duplicatas mantendo ordem
        unique_elements = self._remove_duplicate_elements(publication_elements)
        
        return unique_elements[:50]  # Limitar para performance
    
    def _is_potential_publication_element(self, text: str) -> bool:
        """
        Verifica se um elemento potencialmente contém uma publicação.
        
        Args:
            text: Texto do elemento
            
        Returns:
            bool: True se elemento pode conter publicação
        """
        if len(text) < 100:  # Muito pequeno
            return False
        
        # Indicadores de publicação
        indicators = [
            'processo',
            'inss',
            'instituto nacional do seguro social',
            'rpv',
            'pagamento',
            'advogado',
            'oab'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def _remove_duplicate_elements(self, elements: List[ElementHandle]) -> List[ElementHandle]:
        """
        Remove elementos duplicados da lista.
        
        Args:
            elements: Lista de ElementHandle
            
        Returns:
            Lista sem duplicatas
        """
        seen = set()
        unique_elements = []
        
        for element in elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        return unique_elements
    
    async def _extract_element_content(self, element: ElementHandle) -> str:
        """
        Extrai o conteúdo textual de um elemento.
        
        Args:
            element: ElementHandle do elemento
            
        Returns:
            String com conteúdo do elemento
        """
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
    
    def _is_valid_publication_content(self, content: str) -> bool:
        """
        Valida se o conteúdo representa uma publicação válida.
        
        Args:
            content: Conteúdo textual
            
        Returns:
            bool: True se conteúdo é válido
        """
        if not content or len(content.strip()) < 50:
            return False
        
        # Verificar se contém indicadores mínimos
        content_lower = content.lower()
        
        required_indicators = ['processo', 'inss']
        has_required = all(indicator in content_lower for indicator in required_indicators)
        
        return has_required
    
    async def _create_publication_from_content(self, content: str) -> Optional[Publication]:
        """
        Cria uma entidade Publication a partir do conteúdo extraído.
        
        Args:
            content: Conteúdo textual da publicação
            
        Returns:
            Publication ou None se não conseguir criar
        """
        try:
            # Criar publicação básica
            publication = Publication(
                content=content,
                status=Status.NEW,
                defendant="Instituto Nacional do Seguro Social - INSS"
            )
            
            # Extrair informações específicas
            await self._extract_publication_details(publication, content)
            
            return publication
            
        except Exception as e:
            logger.error(f"Erro ao criar publicação: {str(e)}")
            return None
    
    async def _extract_publication_details(self, publication: Publication, content: str) -> None:
        """
        Extrai detalhes específicos de uma publicação.
        
        Args:
            publication: Entidade Publication a ser preenchida
            content: Conteúdo textual para extração
        """
        try:
            # Extrair número do processo
            self._extract_process_number(publication, content)
            
            # Extrair data de disponibilização
            self._extract_availability_date(publication, content)
            
            # Extrair autores
            self._extract_authors(publication, content)
            
            # Extrair advogados
            self._extract_lawyers(publication, content)
            
            # Extrair valores monetários
            self._extract_monetary_values(publication, content)
            
        except Exception as e:
            logger.debug(f"Erro ao extrair detalhes da publicação: {str(e)}")
    
    def _extract_process_number(self, publication: Publication, content: str) -> None:
        """Extrai número do processo."""
        for pattern in self.patterns['process_number']:
            match = re.search(pattern, content)
            if match:
                try:
                    process_number = match.group(1)
                    publication.process_number = ProcessNumber(process_number)
                    logger.debug(f"Número do processo extraído: {publication.process_number}")
                    return
                except Exception as e:
                    logger.debug(f"Erro ao criar ProcessNumber {process_number}: {str(e)}")
                    continue
    
    def _extract_availability_date(self, publication: Publication, content: str) -> None:
        """Extrai data de disponibilização."""
        for pattern in self.patterns['dates']:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    publication.availability_date = datetime.strptime(date_str, '%d/%m/%Y')
                    logger.debug(f"Data de disponibilização extraída: {publication.availability_date}")
                    return
                except Exception as e:
                    logger.debug(f"Erro ao parsear data {date_str}: {str(e)}")
                    continue
    
    def _extract_authors(self, publication: Publication, content: str) -> None:
        """Extrai autores/requerentes."""
        for pattern in self.patterns['authors']:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                author_name = match.group(1).strip()
                if author_name and len(author_name) > 2:
                    publication.authors.append(author_name)
                    logger.debug(f"Autor extraído: {author_name}")
                    return
    
    def _extract_lawyers(self, publication: Publication, content: str) -> None:
        """Extrai advogados."""
        for pattern in self.patterns['lawyers']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                lawyer_info = match.group(1).strip()
                if lawyer_info and len(lawyer_info) > 2:
                    publication.lawyers.append(lawyer_info)
                    logger.debug(f"Advogado extraído: {lawyer_info}")
    
    def _extract_monetary_values(self, publication: Publication, content: str) -> None:
        """Extrai valores monetários."""
        try:
            for field_name, patterns in self.patterns['monetary_values'].items():
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
    
    async def extract_publication_links(self) -> List[Dict[str, str]]:
        """
        Extrai links para páginas individuais de publicações.
        
        Returns:
            Lista de dicts com informações dos links
        """
        try:
            links = []
            
            # Buscar links de ocorrências
            link_elements = await self.page.query_selector_all(self.selectors['result_links'])
            
            for element in link_elements:
                try:
                    href = await element.get_attribute('href')
                    text = await element.inner_text()
                    
                    if href:
                        links.append({
                            'url': href,
                            'text': text.strip(),
                            'type': 'publication_detail'
                        })
                        
                except Exception as e:
                    logger.debug(f"Erro ao extrair link: {e}")
                    continue
            
            logger.info(f"Encontrados {len(links)} links de publicações")
            return links
            
        except Exception as e:
            logger.error(f"Erro ao extrair links: {e}")
            return []
    
    async def navigate_to_publication_detail(self, link_url: str) -> bool:
        """
        Navega para página de detalhes de uma publicação específica.
        
        Args:
            link_url: URL da página de detalhes
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            logger.info(f"Navegando para detalhes: {link_url}")
            
            await self.page.goto(link_url, wait_until='networkidle')
            await self.page.wait_for_load_state('domcontentloaded')
            
            logger.info("✅ Navegação para detalhes realizada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao navegar para detalhes: {e}")
            return False
    
    async def extract_detailed_publication(self, 
                                         criteria: ScrapingCriteria) -> Optional[Publication]:
        """
        Extrai publicação detalhada da página atual.
        
        Args:
            criteria: Critérios para validação
            
        Returns:
            Publication ou None se não conseguir extrair
        """
        try:
            # Aguardar carregamento
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Extrair todo o conteúdo da página
            page_content = await self.page.content()
            text_content = await self.page.evaluate('() => document.body.innerText')
            
            # Verificar se atende aos critérios
            if not criteria.matches_content(text_content):
                logger.debug("Página de detalhes não atende aos critérios")
                return None
            
            # Criar publicação a partir do conteúdo detalhado
            publication = await self._create_publication_from_content(text_content)
            
            if publication:
                logger.info(f"Publicação detalhada extraída: {publication.process_number}")
            
            return publication
            
        except Exception as e:
            logger.error(f"Erro ao extrair publicação detalhada: {e}")
            return None
    
    async def check_pagination(self) -> Dict[str, Any]:
        """
        Verifica se há páginas adicionais de resultados.
        
        Returns:
            Dict com informações de paginação
        """
        try:
            page_content = await self.page.content()
            
            pagination_info = {
                'has_next_page': False,
                'next_page_url': None,
                'current_page': 1,
                'total_pages': None
            }
            
            # Verificar se há link "Próxima"
            next_links = await self.page.query_selector_all('a:has-text("Próxima"), a:has-text("próxima")')
            
            if next_links:
                try:
                    next_url = await next_links[0].get_attribute('href')
                    pagination_info['has_next_page'] = True
                    pagination_info['next_page_url'] = next_url
                except:
                    pass
            
            # Tentar extrair número da página atual
            page_match = re.search(r'Página\s+(\d+)', page_content)
            if page_match:
                pagination_info['current_page'] = int(page_match.group(1))
            
            return pagination_info
            
        except Exception as e:
            logger.error(f"Erro ao verificar paginação: {e}")
            return {'error': str(e)}
    
    async def navigate_to_next_page(self) -> bool:
        """
        Navega para a próxima página de resultados.
        
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            # Verificar se há próxima página
            pagination_info = await self.check_pagination()
            
            if not pagination_info.get('has_next_page'):
                logger.info("Não há próxima página disponível")
                return False
            
            next_url = pagination_info.get('next_page_url')
            if next_url:
                logger.info(f"Navegando para próxima página: {next_url}")
                await self.page.goto(next_url, wait_until='networkidle')
                await self.page.wait_for_load_state('domcontentloaded')
                return True
            else:
                # Tentar clicar no link "Próxima"
                next_link = await self.page.query_selector('a:has-text("Próxima"), a:has-text("próxima")')
                if next_link:
                    await next_link.click()
                    await self.page.wait_for_load_state('networkidle')
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao navegar para próxima página: {e}")
            return False