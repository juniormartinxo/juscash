"""
Parser aprimorado ATUALIZADO com integração completa do Page Manager
Implementa a lógica completa de download de páginas anteriores
"""

import re
import unicodedata
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedDJEContentParser:
    """
    Parser especializado para extrair publicações do DJE-SP seguindo fluxo específico:
    1. Busca por "RPV" ou "pagamento pelo INSS" 
    2. Localiza início com "Processo NUMERO_DO_PROCESSO"
    3. Extrai autores no formato "- NOME_DO_AUTOR - Vistos"
    4. Lida com publicações divididas entre páginas usando PageManager
    """

    # Padrões regex compilados
    PROCESS_NUMBER_PATTERN = re.compile(r"Processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", re.IGNORECASE)
    
    # Padrões para buscar termos obrigatórios
    RPV_PATTERNS = [
        re.compile(r"\bRPV\b", re.IGNORECASE),
        re.compile(r"requisição\s+de\s+pequeno\s+valor", re.IGNORECASE),
        re.compile(r"pagamento\s+pelo\s+INSS", re.IGNORECASE),
        re.compile(r"pagamento\s+de\s+benefício", re.IGNORECASE)
    ]
    
    # Padrão para autores no formato específico "- NOME - Vistos"
    AUTHOR_PATTERN = re.compile(
        r"-\s+([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]{2,60}[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])\s+-\s+(?:Vistos|Visto|ADV)", 
        re.IGNORECASE
    )
    
    # Padrões para advogados aprimorados
    LAWYER_PATTERNS = [
        re.compile(r"ADV\.\s+([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]{2,50}[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])\s*\(\s*OAB\s+(\d+)\/?\w*\)", re.IGNORECASE),
        re.compile(r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]{2,50}[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])\s*\(\s*OAB\s+(\d+)\/?\w*\)", re.IGNORECASE),
    ]
    
    # Padrões monetários específicos para RPV
    MONETARY_PATTERNS = {
        "gross": [
            re.compile(r"valor\s+(?:principal|bruto|total|devido)[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"principal[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"valor\s+da\s+RPV[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"(?:quantia|importância)\s+de\s+R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "net": [
            re.compile(r"valor\s+líquido[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"líquido[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "interest": [
            re.compile(r"juros\s+moratórios[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"correção\s+monetária[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"atualização[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "fees": [
            re.compile(r"honorários\s+advocatícios[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"honorários[:\s]*R\$?\s*([\d.,]+)", re.IGNORECASE),
        ]
    }

    def __init__(self):
        self.scraper_adapter = None
        self.page_manager = None
        self.content_merger = None
        self.confidence_threshold = 0.8
    
    def set_scraper_adapter(self, scraper_adapter):
        """Define o adapter do scraper e inicializa managers auxiliares"""
        self.scraper_adapter = scraper_adapter
        
        # Importar aqui para evitar dependência circular
        from infrastructure.web.page_manager import DJEPageManager, PublicationContentMerger
        
        self.page_manager = DJEPageManager(scraper_adapter)
        self.content_merger = PublicationContentMerger()

    async def parse_multiple_publications_enhanced(
        self, 
        content: str, 
        source_url: str = "", 
        current_page_number: Optional[int] = None
    ) -> List[Publication]:
        """
        Extrai múltiplas publicações seguindo as instruções específicas
        Lida com publicações divididas entre páginas
        """
        logger.info("🔍 Iniciando extração aprimorada de publicações DJE-SP")
        
        publications = []
        
        # Normalizar conteúdo
        normalized_content = self._normalize_text(content)
        
        # 1. Buscar todas as ocorrências de termos RPV/INSS
        rpv_matches = self._find_all_rpv_occurrences(normalized_content)
        
        if not rpv_matches:
            logger.info("❌ Nenhuma ocorrência de RPV ou pagamento pelo INSS encontrada")
            return publications
        
        logger.info(f"✅ Encontradas {len(rpv_matches)} ocorrências de RPV/INSS")
        
        # 2. Para cada ocorrência, buscar o processo correspondente
        for i, rpv_match in enumerate(rpv_matches):
            logger.info(f"📋 Processando ocorrência {i + 1}/{len(rpv_matches)} na posição {rpv_match['position']}")
            
            try:
                publication = await self._extract_publication_for_rpv_occurrence(
                    normalized_content, 
                    rpv_match, 
                    source_url, 
                    current_page_number
                )
                
                if publication:
                    publications.append(publication)
                    logger.info(f"✅ Publicação extraída: {publication.process_number}")
                else:
                    logger.warning(f"⚠️ Não foi possível extrair publicação para ocorrência {i + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao processar ocorrência {i + 1}: {e}")
                continue
        
        logger.info(f"📊 Total de publicações extraídas: {len(publications)}")
        return publications

    def _find_all_rpv_occurrences(self, content: str) -> List[Dict[str, Any]]:
        """Encontra todas as ocorrências de RPV ou pagamento pelo INSS"""
        occurrences = []
        
        for pattern in self.RPV_PATTERNS:
            for match in pattern.finditer(content):
                occurrences.append({
                    'term': match.group(0),
                    'position': match.start(),
                    'pattern': pattern.pattern
                })
        
        # Ordenar por posição
        occurrences.sort(key=lambda x: x['position'])
        
        # Remover duplicatas próximas (dentro de 50 caracteres)
        filtered_occurrences = []
        for occurrence in occurrences:
            if not filtered_occurrences or (occurrence['position'] - filtered_occurrences[-1]['position']) > 50:
                filtered_occurrences.append(occurrence)
        
        return filtered_occurrences

    async def _extract_publication_for_rpv_occurrence(
        self, 
        content: str, 
        rpv_match: Dict[str, Any], 
        source_url: str, 
        current_page_number: Optional[int]
    ) -> Optional[Publication]:
        """
        Extrai uma publicação para uma ocorrência específica de RPV/INSS
        Implementa a lógica de busca para trás e download de página anterior se necessário
        """
        rpv_position = rpv_match['position']
        working_content = content
        content_was_merged = False
        
        # 1. Buscar processo para trás a partir da posição do RPV
        process_match = self._find_process_before_position(working_content, rpv_position)
        
        if not process_match:
            logger.info(f"❌ Processo não encontrado antes da posição {rpv_position}")
            
            # Verificar se é necessário baixar página anterior
            if current_page_number and current_page_number > 1 and self.page_manager:
                logger.info(f"🔄 Tentando baixar página anterior ({current_page_number - 1}) para encontrar início do processo")
                
                try:
                    previous_page_content = await self.page_manager.get_previous_page_content(
                        source_url, current_page_number
                    )
                    
                    if previous_page_content:
                        # Fazer merge do conteúdo usando o ContentMerger
                        working_content = self.content_merger.merge_cross_page_publication(
                            previous_page_content, content, rpv_position
                        )
                        
                        # Validar merge
                        if self.content_merger.validate_merged_content(working_content, ['rpv', 'pagamento pelo inss']):
                            logger.info("✅ Merge de páginas validado com sucesso")
                            content_was_merged = True
                            
                            # Recalcular posição do RPV no conteúdo merged
                            adjusted_rpv_position = len(previous_page_content) + rpv_position
                            
                            # Buscar processo novamente no conteúdo merged
                            process_match = self._find_process_before_position(working_content, adjusted_rpv_position)
                            
                            if process_match:
                                logger.info("✅ Processo encontrado após merge de páginas")
                                rpv_position = adjusted_rpv_position  # Usar posição ajustada
                            else:
                                logger.warning("⚠️ Processo ainda não encontrado mesmo após merge")
                                return None
                        else:
                            logger.warning("⚠️ Merge de páginas falhou na validação")
                            return None
                    else:
                        logger.warning("⚠️ Não foi possível baixar página anterior")
                        return None
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao processar página anterior: {e}")
                    return None
            else:
                logger.info("ℹ️ Não é possível baixar página anterior (primeira página ou page_manager não disponível)")
                return None
        
        if not process_match:
            return None
        
        process_number = process_match['process_number']
        process_start = process_match['start_position']
        
        # 2. Determinar fim da publicação (próximo processo ou fim do documento)
        publication_end = self._find_publication_end(working_content, process_start)
        
        # 3. Extrair conteúdo completo da publicação
        publication_content = working_content[process_start:publication_end]
        
        logger.info(f"📄 Extraindo publicação: {process_number} ({len(publication_content)} chars)")
        if content_was_merged:
            logger.info(f"🔗 Publicação recuperada através de merge de páginas")
        
        # 4. Extrair dados estruturados
        publication_data = self._extract_structured_data(publication_content, process_number)
        
        if not publication_data:
            logger.warning(f"⚠️ Falha ao extrair dados estruturados para {process_number}")
            return None
        
        # 5. Criar entidade Publication
        try:
            publication = Publication(
                process_number=process_number,
                authors=publication_data['authors'],
                content=publication_content,
                publication_date=publication_data.get('publication_date'),
                availability_date=publication_data.get('availability_date') or datetime.now(),
                lawyers=publication_data.get('lawyers', []),
                gross_value=publication_data.get('gross_value'),
                net_value=publication_data.get('net_value'),
                interest_value=publication_data.get('interest_value'),
                attorney_fees=publication_data.get('attorney_fees'),
                extraction_metadata={
                    'extraction_method': 'enhanced_parser_v2',
                    'source_url': source_url,
                    'rpv_term_found': rpv_match['term'],
                    'extraction_date': datetime.now().isoformat(),
                    'confidence_score': publication_data.get('confidence_score', 0.8),
                    'content_was_merged': content_was_merged,
                    'current_page_number': current_page_number
                }
            )
            
            return publication
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar entidade Publication para {process_number}: {e}")
            return None

    def _find_process_before_position(self, content: str, position: int) -> Optional[Dict[str, Any]]:
        """
        Busca o último processo antes de uma posição específica
        Retorna o processo mais próximo para trás
        """
        # Buscar todos os processos no conteúdo até a posição especificada
        search_content = content[:position]
        
        process_matches = []
        for match in self.PROCESS_NUMBER_PATTERN.finditer(search_content):
            process_matches.append({
                'process_number': match.group(1),
                'start_position': match.start(),
                'match': match
            })
        
        if not process_matches:
            return None
        
        # Retornar o último processo encontrado (mais próximo da posição)
        return process_matches[-1]

    def _find_publication_end(self, content: str, start_position: int) -> int:
        """
        Encontra o fim da publicação (próximo processo ou fim do documento)
        """
        # Buscar próximo processo após a posição inicial
        search_content = content[start_position + 1:]  # +1 para não encontrar o mesmo processo
        
        next_process_match = self.PROCESS_NUMBER_PATTERN.search(search_content)
        
        if next_process_match:
            return start_position + 1 + next_process_match.start()
        else:
            # Se não encontrar próximo processo, vai até o fim do documento
            return len(content)

    def _extract_structured_data(self, content: str, process_number: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados estruturados da publicação seguindo padrões específicos
        """
        data = {
            'process_number': process_number,
            'authors': [],
            'lawyers': [],
            'confidence_score': 0.0
        }
        
        confidence_score = 0.0
        
        # 1. Extrair autores no formato "- NOME - Vistos"
        authors = self._extract_authors_enhanced(content)
        if authors:
            data['authors'] = authors
            confidence_score += 0.3
        else:
            logger.warning(f"⚠️ Autores não encontrados para {process_number}")
            return None
        
        # 2. Extrair advogados
        lawyers = self._extract_lawyers_enhanced(content)
        data['lawyers'] = lawyers
        if lawyers:
            confidence_score += 0.15
        
        # 3. Extrair valores monetários
        monetary_values = self._extract_monetary_values_enhanced(content)
        data.update(monetary_values)
        if any(monetary_values.values()):
            confidence_score += 0.25
        
        # 4. Extrair datas (simplificado por ora)
        dates = self._extract_dates_enhanced(content)
        data.update(dates)
        if dates.get('availability_date'):
            confidence_score += 0.1
        
        # 5. Verificar se contém termos RPV
        if any(pattern.search(content) for pattern in self.RPV_PATTERNS):
            confidence_score += 0.2
        
        data['confidence_score'] = confidence_score
        
        # Só retornar se tiver confiança mínima
        if confidence_score >= self.confidence_threshold:
            return data
        else:
            logger.warning(f"⚠️ Confiança muito baixa ({confidence_score:.2f}) para {process_number}")
            return None

    def _extract_authors_enhanced(self, content: str) -> List[str]:
        """
        Extrai autores no formato específico "- NOME - Vistos"
        """
        authors = []
        
        for match in self.AUTHOR_PATTERN.finditer(content):
            author_name = match.group(1).strip()
            cleaned_name = self._clean_author_name(author_name)
            
            if cleaned_name and len(cleaned_name) > 3:
                authors.append(cleaned_name)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique_authors = []
        for author in authors:
            if author not in seen:
                seen.add(author)
                unique_authors.append(author)
        
        return unique_authors[:10]  # Máximo 10 autores

    def _extract_lawyers_enhanced(self, content: str) -> List[Lawyer]:
        """
        Extrai advogados com padrões aprimorados
        """
        lawyers = []
        seen_oabs = set()
        
        for pattern in self.LAWYER_PATTERNS:
            for match in pattern.finditer(content):
                try:
                    name = match.group(1).strip()
                    oab = match.group(2) if len(match.groups()) >= 2 else "Não informado"
                    
                    cleaned_name = self._clean_lawyer_name(name)
                    
                    if cleaned_name and len(cleaned_name) > 3 and oab not in seen_oabs:
                        lawyers.append(Lawyer(name=cleaned_name, oab=oab))
                        seen_oabs.add(oab)
                        
                        if len(lawyers) >= 5:  # Máximo 5 advogados
                            break
                            
                except Exception as e:
                    logger.debug(f"Erro ao extrair advogado: {e}")
                    continue
        
        return lawyers

    def _extract_monetary_values_enhanced(self, content: str) -> Dict[str, Optional[MonetaryValue]]:
        """
        Extrai valores monetários com padrões específicos para RPV
        """
        values = {}
        
        for value_type, patterns in self.MONETARY_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    try:
                        value_str = match.group(1)
                        decimal_value = self._parse_monetary_string(value_str)
                        
                        if decimal_value and decimal_value > 0:
                            values[value_type] = MonetaryValue.from_real(decimal_value)
                            break
                    except (ValueError, InvalidOperation):
                        continue
            
            if value_type not in values:
                values[value_type] = None
        
        return values

    def _extract_dates_enhanced(self, content: str) -> Dict[str, Optional[datetime]]:
        """
        Extrai datas da publicação (simplificado)
        """
        # Por ora, usar data atual como availability_date
        # Pode ser aprimorado com padrões específicos do DJE
        return {
            'publication_date': None,
            'availability_date': datetime.now()
        }

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto mantendo estrutura para parsing"""
        # Remover caracteres de controle mas manter quebras de linha importantes
        normalized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalizar espaços mas manter quebras de linha
        normalized = re.sub(r'[ \t]+', ' ', normalized)
        normalized = re.sub(r'\n\s*\n', '\n\n', normalized)
        
        return normalized.strip()

    def _clean_author_name(self, name: str) -> str:
        """Limpa nome do autor removendo prefixos e sufixos desnecessários"""
        # Remover prefixos
        name = re.sub(r'^(sr\.?|sra\.?|dr\.?|dra\.?)\s*', '', name, flags=re.IGNORECASE)
        
        # Remover sufixos com documentos
        name = re.sub(r'\s*(cpf|rg|cnh)[:.\s]*\d+.*$', '', name, flags=re.IGNORECASE)
        
        # Limpar caracteres especiais preservando acentos
        name = re.sub(r'[^\w\sÁÉÍÓÚÀÂÊÔÃÕÇáéíóúàâêôãõç]', '', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip().title()

    def _clean_lawyer_name(self, name: str) -> str:
        """Limpa nome do advogado"""
        # Remover prefixos profissionais
        name = re.sub(r'^(dr\.?|dra\.?|advogad[oa]|adv\.?)\s*', '', name, flags=re.IGNORECASE)
        
        # Remover sufixos
        name = re.sub(r'\s*(oab|advogad[oa]).*$', '', name, flags=re.IGNORECASE)
        
        # Limitar tamanho
        if len(name) > 60:
            words = name.split()
            name = ' '.join(words[:4]) if len(words) > 4 else name[:60]
        
        # Limpar caracteres especiais
        name = re.sub(r'[^\w\sÁÉÍÓÚÀÂÊÔÃÕÇáéíóúàâêôãõç]', '', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip().title()

    def _parse_monetary_string(self, value_str: str) -> Optional[Decimal]:
        """Converte string monetária brasileira para Decimal"""
        cleaned = re.sub(r'[^\d.,]', '', value_str)
        
        if not cleaned:
            return None
        
        # Tratar diferentes formatos brasileiros
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
