import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Status(Enum):
    """
    Enum para status das publicações no sistema.
    
    Representa os diferentes estados que uma publicação pode ter
    durante seu ciclo de vida no sistema.
    """
    NEW = "nova"                    # Publicação recém extraída
    READ = "lida"                   # Publicação foi revisada
    SENT_TO_LAWYER = "enviada_adv"  # Publicação enviada para advogado
    COMPLETED = "concluida"         # Publicação finalizada


@dataclass(frozen=True)
class ProcessNumber:
    """
    Objeto de valor representando um número de processo judicial.
    
    Valida e normaliza números de processo do padrão CNJ.
    Formato esperado: NNNNNNN-DD.AAAA.J.TR.OOOO
    """
    
    value: str
    
    def __post_init__(self):
        """Valida o número do processo na criação."""
        if not self.value:
            raise ValueError("Número do processo não pode estar vazio")
        
        # Remove espaços e caracteres especiais desnecessários
        cleaned = re.sub(r'[^\d\-\.]', '', self.value.strip())
        
        # Valida formato básico do CNJ (pode ser mais flexível para diferentes formatos)
        if not self._is_valid_format(cleaned):
            # Se não está no formato CNJ, aceita qualquer sequência alfanumérica
            if not re.match(r'^[\w\-\.\/]+$', self.value.strip()):
                raise ValueError(f"Formato inválido de número de processo: {self.value}")
        
        # Atualiza o valor limpo (só funciona porque usamos object.__setattr__)
        object.__setattr__(self, 'value', cleaned if self._is_valid_format(cleaned) else self.value.strip())
    
    def _is_valid_format(self, value: str) -> bool:
        """
        Verifica se o número está no formato CNJ.
        
        Args:
            value: Valor a ser validado
            
        Returns:
            True se está no formato CNJ
        """
        # Padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
        cnj_pattern = r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
        return bool(re.match(cnj_pattern, value))
    
    def get_sequential_number(self) -> Optional[str]:
        """
        Extrai o número sequencial do processo (primeiros 7 dígitos no padrão CNJ).
        
        Returns:
            Número sequencial ou None se não estiver no padrão CNJ
        """
        if self._is_valid_format(self.value):
            return self.value[:7]
        return None
    
    def get_court_code(self) -> Optional[str]:
        """
        Extrai o código do tribunal (últimos 4 dígitos no padrão CNJ).
        
        Returns:
            Código do tribunal ou None se não estiver no padrão CNJ
        """
        if self._is_valid_format(self.value):
            return self.value[-4:]
        return None
    
    def __str__(self) -> str:
        """Representação string do número do processo."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash para uso em sets e como chave de dicionário."""
        return hash(self.value)


@dataclass(frozen=True)
class ScrapingCriteria:
    """
    Objeto de valor representando critérios de busca para scraping.
    
    Define os parâmetros necessários para realizar o scraping
    das publicações no DJE.
    """
    
    required_terms: tuple[str, ...]  # Termos obrigatórios na publicação
    caderno: str = "3"               # Caderno do DJE (padrão: 3)
    instancia: str = "1"             # Instância (padrão: 1ª Instância)
    local: str = "Capital"           # Local (padrão: Capital)
    parte: str = "1"                 # Parte do caderno (padrão: Parte 1)
    
    def __post_init__(self):
        """Valida os critérios na criação."""
        if not self.required_terms:
            raise ValueError("Pelo menos um termo obrigatório deve ser especificado")
        
        if any(not term.strip() for term in self.required_terms):
            raise ValueError("Termos obrigatórios não podem estar vazios")
        
        # Normaliza os termos (remove espaços extras)
        normalized_terms = tuple(term.strip() for term in self.required_terms)
        object.__setattr__(self, 'required_terms', normalized_terms)
    
    def get_caderno_description(self) -> str:
        """
        Retorna a descrição completa do caderno sendo pesquisado.
        
        Returns:
            Descrição formatada do caderno
        """
        return f"Caderno {self.caderno} - Judicial - {self.instancia}ª Instância - {self.local} Parte {self.parte}"
    
    def matches_content(self, content: str) -> bool:
        """
        Verifica se o conteúdo atende aos critérios de busca.
        
        Args:
            content: Conteúdo a ser verificado
            
        Returns:
            True se todos os termos obrigatórios estão presentes
        """
        if not content:
            return False
        
        content_lower = content.lower()
        return all(term.lower() in content_lower for term in self.required_terms)
    
    def __str__(self) -> str:
        """Representação string dos critérios."""
        terms_str = ", ".join(self.required_terms)
        return f"ScrapingCriteria(terms=[{terms_str}], {self.get_caderno_description()})"


@dataclass(frozen=True)
class DJEUrl:
    """
    Objeto de valor representando URLs do DJE.
    
    Encapsula a lógica de construção e validação de URLs
    do Diário da Justiça Eletrônico.
    """
    
    base_url: str = "https://dje.tjsp.jus.br"
    
    def get_main_url(self) -> str:
        """
        Retorna a URL principal do DJE.
        
        Returns:
            URL principal para acesso inicial
        """
        return f"{self.base_url}/cdje/index.do"
    
    def get_consultation_url(self, volume: Optional[str] = None, 
                            diary: Optional[str] = None,
                            notebook: Optional[str] = None,
                            page: Optional[str] = None) -> str:
        """
        Constrói URL de consulta específica do DJE.
        
        Args:
            volume: Número do volume
            diary: Número do diário
            notebook: Código do caderno
            page: Número da página
            
        Returns:
            URL formatada para consulta
        """
        url = f"{self.base_url}/cdje/consultaSimples.do"
        
        params = []
        if volume:
            params.append(f"cdVolume={volume}")
        if diary:
            params.append(f"nuDiario={diary}")
        if notebook:
            params.append(f"cdCaderno={notebook}")
        if page:
            params.append(f"nuSeqpagina={page}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def is_valid_dje_url(self, url: str) -> bool:
        """
        Verifica se uma URL pertence ao domínio do DJE.
        
        Args:
            url: URL a ser validada
            
        Returns:
            True se é uma URL válida do DJE
        """
        return url.startswith(self.base_url)
    
    def __str__(self) -> str:
        """Representação string da URL base."""
        return self.base_url