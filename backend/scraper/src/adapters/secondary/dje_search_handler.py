"""
Arquivo: src/adapters/secondary/dje_search_handler.py

Handler especializado para pesquisas avançadas no DJE.
Segue princípios da Arquitetura Hexagonal como componente de infraestrutura.

Responsabilidades:
- Configuração de pesquisas avançadas no DJE
- Navegação específica da interface de pesquisa
- Validação de resultados de pesquisa
- Isolamento da lógica específica do DJE
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.shared.logger import get_logger
from src.shared.exceptions import NavigationException, TimeoutException

logger = get_logger(__name__)


class DJEAdvancedSearchHandler:
    """
    Handler para pesquisa avançada no DJE.
    
    Responsabilidade: Encapsular a lógica específica de navegação
    e configuração da pesquisa avançada do site do DJE.
    
    Princípios da Arquitetura Hexagonal:
    - Componente de infraestrutura (adapter secundário)
    - Isolamento das especificidades do DJE
    - Reutilizável e testável independentemente
    """
    
    def __init__(self, page: Page):
        """
        Inicializa o handler de pesquisa avançada.
        
        Args:
            page: Instância da página Playwright
        """
        self.page = page
        self.selectors = self._get_selectors()
        self.search_config = self._get_default_search_config()
    
    def _get_selectors(self) -> Dict[str, str]:
        """
        Retorna seletores CSS específicos do DJE.
        
        Returns:
            Dict com seletores CSS organizados por funcionalidade
        """
        return {
            # Campos de data
            'data_inicio': '#dtInicioString',
            'data_fim': '#dtFimString',
            
            # Campo de caderno
            'caderno_select': 'select[name="dadosConsulta.cdCaderno"]',
            
            # Campo de palavras-chave
            'palavras_chave': 'input[name="dadosConsulta.pesquisaLivre"]',
            
            # Botões de ação
            'btn_pesquisar': 'input[type="submit"][value="Pesquisar"]',
            'btn_limpar': 'input[type="button"][value="Limpar"]',
            
            # Operadores lógicos
            'btn_e': 'input[value=" E "]',
            'btn_ou': 'input[value="OU"]',
            'btn_nao': 'input[value="NÃO"]',
            'btn_aspas': 'input[value="\\"  \\""]',
            
            # Elementos de resultado
            'resultados_container': 'body',
            'loading_indicator': '.loading, .carregando, .spinner'
        }
    
    def _get_default_search_config(self) -> Dict[str, Any]:
        """
        Retorna configuração padrão de pesquisa para o projeto.
        
        Returns:
            Dict com configurações padrão
        """
        return {
            'data_inicio': '17/03/2025',  # Data específica do projeto
            'caderno_value': '12',        # Caderno 3 - Capital - Parte I
            'palavras_chave': '"RPV" e "pagamento pelo INSS"',  # Termos obrigatórios
            'timeout_search': 60000,      # 60 segundos para pesquisa
            'timeout_elements': 10000     # 10 segundos para elementos
        }
    
    async def execute_project_search(self) -> bool:
        """
        Executa a pesquisa específica do projeto DJE.
        
        Configuração fixa conforme especificação:
        - Data início: 17/03/2025
        - Caderno: 3 - Judicial - 1ª Instância - Capital - Parte I
        - Termos: RPV E pagamento pelo INSS
        
        Returns:
            bool: True se pesquisa foi executada com sucesso
            
        Raises:
            NavigationException: Se erro na navegação/pesquisa
            TimeoutException: Se timeout durante processo
        """
        config = self.search_config
        
        return await self.configure_advanced_search(
            data_inicio=config['data_inicio'],
            data_fim=self._get_current_date(),
            palavras_chave=config['palavras_chave']
        )
    
    async def configure_advanced_search(self, 
                                      data_inicio: str,
                                      data_fim: Optional[str] = None,
                                      palavras_chave: str = "RPV E pagamento pelo INSS",
                                      caderno_value: Optional[str] = None) -> bool:
        """
        Configura a pesquisa avançada com parâmetros personalizados.
        
        Args:
            data_inicio: Data inicial no formato DD/MM/AAAA
            data_fim: Data final no formato DD/MM/AAAA (se None, usa data atual)
            palavras_chave: Termos de busca específicos
            caderno_value: Valor do caderno (se None, usa padrão do projeto)
            
        Returns:
            bool: True se configuração foi bem-sucedida
            
        Raises:
            NavigationException: Se erro na configuração
        """
        try:
            logger.info("🔍 Configurando pesquisa avançada do DJE...")
            
            # Usar valores padrão se não especificados
            if not data_fim:
                data_fim = self._get_current_date()
            
            if not caderno_value:
                caderno_value = self.search_config['caderno_value']
            
            # === 1. CONFIGURAR DATAS ===
            await self._configure_dates(data_inicio, data_fim)
            
            # === 2. SELECIONAR CADERNO ===
            await self._select_caderno_advanced(caderno_value)
            
            # === 3. CONFIGURAR PALAVRAS-CHAVE ===
            await self._configure_search_terms(palavras_chave)
            
            # === 4. EXECUTAR PESQUISA ===
            return await self._execute_search()
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar pesquisa avançada: {e}")
            raise NavigationException(f"Erro na pesquisa avançada: {str(e)}")
    
    async def _configure_dates(self, data_inicio: str, data_fim: str) -> None:
        """
        Configura as datas da pesquisa avançada.
        
        Args:
            data_inicio: Data inicial DD/MM/AAAA
            data_fim: Data final DD/MM/AAAA
            
        Raises:
            TimeoutException: Se elementos não encontrados
        """
        logger.info(f"📅 Configurando datas: {data_inicio} até {data_fim}")
        
        try:
            # Aguardar campos de data estarem disponíveis
            await self.page.wait_for_selector(
                self.selectors['data_inicio'], 
                timeout=self.search_config['timeout_elements']
            )
            await self.page.wait_for_selector(
                self.selectors['data_fim'], 
                timeout=self.search_config['timeout_elements']
            )
            
            # Configurar data início
            await self._remove_readonly('dtInicioString')
            await self.page.fill(self.selectors['data_inicio'], '')
            await self.page.fill(self.selectors['data_inicio'], data_inicio)
            await self.page.dispatch_event(self.selectors['data_inicio'], 'change')
            await self.page.dispatch_event(self.selectors['data_inicio'], 'blur')
            
            # Configurar data fim
            await self._remove_readonly('dtFimString')
            await self.page.fill(self.selectors['data_fim'], '')
            await self.page.fill(self.selectors['data_fim'], data_fim)
            await self.page.dispatch_event(self.selectors['data_fim'], 'change')
            await self.page.dispatch_event(self.selectors['data_fim'], 'blur')
            
            # Validar se datas foram definidas
            data_inicio_atual = await self.page.input_value(self.selectors['data_inicio'])
            data_fim_atual = await self.page.input_value(self.selectors['data_fim'])
            
            if data_inicio_atual == data_inicio and data_fim_atual == data_fim:
                logger.info(f"✅ Datas configuradas: {data_inicio} - {data_fim}")
            else:
                logger.warning(f"⚠️ Datas podem não ter sido definidas corretamente")
                logger.info(f"Esperado: {data_inicio} - {data_fim}")
                logger.info(f"Atual: {data_inicio_atual} - {data_fim_atual}")
            
        except PlaywrightTimeoutError:
            raise TimeoutException("configure_dates", self.search_config['timeout_elements'] // 1000)
        except Exception as e:
            logger.error(f"❌ Erro ao configurar datas: {e}")
            raise
    
    async def _select_caderno_advanced(self, caderno_value: str) -> None:
        """
        Seleciona o caderno específico na pesquisa avançada.
        
        Args:
            caderno_value: Valor do caderno (ex: "12")
            
        Raises:
            NavigationException: Se falha na seleção
        """
        logger.info(f"📚 Selecionando caderno valor: {caderno_value}")
        
        try:
            # Aguardar select do caderno
            await self.page.wait_for_selector(
                self.selectors['caderno_select'], 
                timeout=self.search_config['timeout_elements']
            )
            
            # Método 1: select_option direto
            try:
                await self.page.select_option(self.selectors['caderno_select'], value=caderno_value)
                logger.info(f"✅ Método 1 - Caderno {caderno_value} selecionado")
                
                # Validar seleção
                selected_value = await self.page.evaluate("""
                    () => {
                        const select = document.querySelector('select[name="dadosConsulta.cdCaderno"]');
                        return select ? select.value : null;
                    }
                """)
                
                if selected_value == caderno_value:
                    return
                else:
                    logger.warning(f"⚠️ Validação falhou: esperado {caderno_value}, atual {selected_value}")
                
            except Exception as e:
                logger.warning(f"⚠️ Método 1 falhou: {e}")
            
            # Método 2: Locator (fallback)
            try:
                locator = self.page.locator(self.selectors['caderno_select'])
                await locator.select_option(value=caderno_value)
                logger.info(f"✅ Método 2 - Caderno {caderno_value} selecionado")
                return
            except Exception as e:
                logger.warning(f"⚠️ Método 2 falhou: {e}")
            
            # Método 3: JavaScript direto (último recurso)
            try:
                result = await self.page.evaluate(f"""
                    () => {{
                        const select = document.querySelector('select[name="dadosConsulta.cdCaderno"]');
                        if (select) {{
                            select.value = '{caderno_value}';
                            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            select.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            return select.value === '{caderno_value}';
                        }}
                        return false;
                    }}
                """)
                
                if result:
                    logger.info(f"✅ Método 3 - Caderno {caderno_value} selecionado")
                    return
                else:
                    raise NavigationException(f"Falha em todos os métodos de seleção do caderno {caderno_value}")
                    
            except Exception as e:
                logger.error(f"❌ Método 3 com erro: {e}")
                raise NavigationException(f"Erro crítico ao selecionar caderno: {str(e)}")
                
        except PlaywrightTimeoutError:
            raise TimeoutException("select_caderno", self.search_config['timeout_elements'] // 1000)
        except Exception as e:
            logger.error(f"❌ Erro na seleção do caderno: {e}")
            raise
    
    async def _configure_search_terms(self, palavras_chave: str) -> None:
        """
        Configura os termos de busca com validação.
        
        Args:
            palavras_chave: String com termos de busca
            
        Raises:
            TimeoutException: Se campo não encontrado
        """
        logger.info(f"🔍 Configurando palavras-chave: '{palavras_chave}'")
        
        try:
            # Aguardar campo de palavras-chave
            await self.page.wait_for_selector(
                self.selectors['palavras_chave'], 
                timeout=self.search_config['timeout_elements']
            )
            
            # Limpar campo e inserir termos
            await self.page.fill(self.selectors['palavras_chave'], '')
            await self.page.fill(self.selectors['palavras_chave'], palavras_chave)
            
            # Validar se termos foram inseridos
            valor_atual = await self.page.input_value(self.selectors['palavras_chave'])
            
            if valor_atual == palavras_chave:
                logger.info(f"✅ Palavras-chave configuradas: '{palavras_chave}'")
            else:
                logger.warning(f"⚠️ Termos podem não ter sido definidos corretamente")
                logger.info(f"Esperado: '{palavras_chave}'")
                logger.info(f"Atual: '{valor_atual}'")
            
            # Aguardar processamento
            await self.page.wait_for_timeout(500)
            
        except PlaywrightTimeoutError:
            raise TimeoutException("configure_search_terms", self.search_config['timeout_elements'] // 1000)
        except Exception as e:
            logger.error(f"❌ Erro ao configurar palavras-chave: {e}")
            raise
    
    async def _execute_search(self) -> bool:
        """
        Executa a pesquisa avançada e aguarda resultados.
        
        Returns:
            bool: True se pesquisa foi executada com sucesso
            
        Raises:
            TimeoutException: Se timeout durante pesquisa
        """
        logger.info("🚀 Executando pesquisa avançada...")
        
        try:
            # Aguardar um momento antes de clicar (estabilizar interface)
            await self.page.wait_for_timeout(1000)
            
            # Clicar no botão Pesquisar
            await self.page.click(self.selectors['btn_pesquisar'])
            
            # Aguardar carregamento dos resultados com timeout estendido
            await self.page.wait_for_load_state(
                'networkidle', 
                timeout=self.search_config['timeout_search']
            )
            
            # Validar se obteve resultados
            await self._validate_search_results()
            
            logger.info("✅ Pesquisa executada com sucesso")
            return True
            
        except PlaywrightTimeoutError:
            raise TimeoutException("execute_search", self.search_config['timeout_search'] // 1000)
        except Exception as e:
            logger.error(f"❌ Erro ao executar pesquisa: {e}")
            return False
    
    async def _validate_search_results(self) -> Dict[str, Any]:
        """
        Valida se a pesquisa retornou resultados e extrai metadados.
        
        Returns:
            Dict com informações sobre os resultados
        """
        try:
            # Aguardar carregamento completo
            await self.page.wait_for_timeout(2000)
            
            # Obter conteúdo da página
            page_content = await self.page.content()
            current_url = self.page.url
            
            # Indicadores de sucesso
            success_indicators = [
                "Resultados",
                "caderno 3 - Judicial - 1ª Instância - Capital - Parte I",
                "ocorrência encontrada",
                "ocorrências encontradas",
                "Página"
            ]
            
            # Indicadores de falha
            failure_indicators = [
                "nenhum resultado",
                "não foram encontrados",
                "0 ocorrência"
            ]
            
            # Verificar se há resultados
            found_results = any(indicator.lower() in page_content.lower() 
                              for indicator in success_indicators)
            
            no_results = any(indicator.lower() in page_content.lower() 
                           for indicator in failure_indicators)
            
            result_info = {
                'has_results': found_results,
                'no_results': no_results,
                'current_url': current_url,
                'page_title': await self.page.title()
            }
            
            if found_results:
                logger.info("✅ Resultados da pesquisa encontrados")
                
                # Tentar extrair número de ocorrências
                import re
                result_count_match = re.search(
                    r'(\d+)\s+ocorrência[s]?\s+encontrada[s]?', 
                    page_content, 
                    re.IGNORECASE
                )
                
                if result_count_match:
                    count = int(result_count_match.group(1))
                    result_info['result_count'] = count
                    logger.info(f"📊 {count} ocorrência(s) encontrada(s)")
                
            elif no_results:
                logger.warning("⚠️ Pesquisa executada mas sem resultados")
                result_info['result_count'] = 0
                
            else:
                logger.warning("⚠️ Não foi possível validar os resultados")
                logger.debug(f"URL atual: {current_url}")
                
            return result_info
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar resultados: {e}")
            return {'has_results': False, 'error': str(e)}
    
    async def _remove_readonly(self, element_id: str) -> None:
        """
        Remove atributo readonly de um elemento para permitir edição.
        
        Args:
            element_id: ID do elemento HTML
        """
        await self.page.evaluate(f"""
            () => {{
                const campo = document.getElementById('{element_id}');
                if (campo) {{
                    campo.removeAttribute('readonly');
                    campo.classList.remove('disabled');
                }}
            }}
        """)
    
    def _get_current_date(self) -> str:
        """
        Retorna a data atual no formato DD/MM/AAAA.
        
        Returns:
            String com data atual formatada
        """
        return datetime.now().strftime("%d/%m/%Y")
    
    async def get_search_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados da última pesquisa realizada.
        
        Returns:
            Dict com metadados da pesquisa
        """
        try:
            return {
                'current_url': self.page.url,
                'page_title': await self.page.title(),
                'search_config': self.search_config,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao obter metadados: {e}")
            return {'error': str(e)}