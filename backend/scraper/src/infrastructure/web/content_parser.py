"""
Parser avançado para conteúdo das publicações do DJE-SP
"""

import re
import unicodedata
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation

from domain.entities.publication import Publication, Lawyer, MonetaryValue
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class DJEContentParser:
    """
    Parser especializado para extrair dados estruturados das publicações do DJE-SP
    """

    # Padrões regex compilados para melhor performance
    PROCESS_NUMBER_PATTERN = re.compile(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})")

    DATE_PATTERNS = [
        re.compile(
            r"(?:publicad[oa]|disponibilizad[oa])\s+em\s+(\d{1,2}/\d{1,2}/\d{4})",
            re.IGNORECASE,
        ),
        re.compile(r"data[:\s]*(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE),
        re.compile(r"(\d{1,2}/\d{1,2}/\d{4})"),
    ]

    AUTHOR_PATTERNS = [
        re.compile(
            r"(?:autor|autora|requerente)(?:es)?[:\s]*(.*?)(?:x|versus|vs\.?|réu|advogado)",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(r"(.*?)\s+(?:x|versus|vs\.?)\s+Instituto Nacional", re.IGNORECASE),
        re.compile(
            r"Requerente[:\s]*(.*?)(?:\n|Requerido|Advogado)", re.IGNORECASE | re.DOTALL
        ),
    ]

    LAWYER_PATTERNS = [
        re.compile(
            r"(?:advogad[oa]|dr\.?|dra\.?)[:\s]*([^,\n]+?)(?:oab[:\s]*(\d+))?",
            re.IGNORECASE,
        ),
        re.compile(r"OAB[:\s]*(\d+)[:\s]*([^,\n]+)", re.IGNORECASE),
        re.compile(r"(\w+\s+\w+(?:\s+\w+)*)\s+(?:OAB|oab)[:\s]*(\d+)", re.IGNORECASE),
    ]

    MONETARY_PATTERNS = {
        "gross": [
            re.compile(
                r"valor\s+(?:principal|bruto)[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE
            ),
            re.compile(r"principal[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"valor\s+devido[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "net": [
            re.compile(r"valor\s+l[íi]quido[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"l[íi]quido[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "interest": [
            re.compile(r"juros?[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(
                r"corre[çc][ãa]o\s+monet[áa]ria[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE
            ),
            re.compile(r"atualiza[çc][ãa]o[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
        "fees": [
            re.compile(r"honor[áa]rios?[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"sucumbenciais[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
            re.compile(r"advocat[íi]cios[:\s]*r\$?\s*([\d.,]+)", re.IGNORECASE),
        ],
    }

    def __init__(self):
        self.confidence_threshold = 0.7

    def parse_publication(
        self, content: str, source_url: str = ""
    ) -> Optional[Publication]:
        """
        Extrai dados estruturados do conteúdo da publicação

        Args:
            content: Texto completo da publicação
            source_url: URL de origem da publicação

        Returns:
            Publication: Entidade com dados extraídos ou None se inválida
        """
        try:
            # Normalizar texto
            normalized_content = self._normalize_text(content)

            # Extrair componentes obrigatórios
            process_number = self._extract_process_number(normalized_content)
            if not process_number:
                logger.debug("❌ Número do processo não encontrado")
                return None

            authors = self._extract_authors(normalized_content)
            if not authors:
                logger.debug(
                    f"❌ Autores não encontrados para processo {process_number}"
                )
                return None

            # Extrair componentes opcionais
            publication_date = self._extract_publication_date(normalized_content)
            availability_date = self._extract_availability_date(normalized_content)
            lawyers = self._extract_lawyers(normalized_content)

            # Extrair valores monetários
            monetary_values = self._extract_all_monetary_values(normalized_content)

            # Calcular score de confiança
            confidence_score = self._calculate_confidence_score(
                process_number, authors, lawyers, monetary_values, normalized_content
            )

            if confidence_score < self.confidence_threshold:
                logger.warning(
                    f"⚠️  Baixa confiança ({confidence_score:.2f}) para {process_number}"
                )

            # Criar entidade Publication
            publication = Publication(
                process_number=process_number,
                publication_date=publication_date,
                availability_date=availability_date or datetime.now(),
                authors=authors,
                lawyers=lawyers,
                gross_value=monetary_values.get("gross"),
                net_value=monetary_values.get("net"),
                interest_value=monetary_values.get("interest"),
                attorney_fees=monetary_values.get("fees"),
                content=content,
                extraction_metadata={
                    "extraction_date": datetime.now().isoformat(),
                    "source_url": source_url,
                    "confidence_score": confidence_score,
                    "extraction_method": "advanced_parser",
                    "text_length": len(content),
                    "normalized_length": len(normalized_content),
                },
            )

            logger.debug(
                f"✅ Publicação parseada: {process_number} (confiança: {confidence_score:.2f})"
            )
            return publication

        except Exception as error:
            logger.error(f"❌ Erro ao parsear publicação: {error}")
            return None

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto removendo acentos e caracteres especiais"""
        # Remover acentos
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))

        # Limpar espaços extras
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.strip()

        return normalized

    def _extract_process_number(self, content: str) -> Optional[str]:
        """Extrai número do processo com validação"""
        match = self.PROCESS_NUMBER_PATTERN.search(content)
        if match:
            process_number = match.group(1)
            # Validação adicional do formato
            if self._validate_process_number_format(process_number):
                return process_number
        return None

    def _validate_process_number_format(self, process_number: str) -> bool:
        """Valida formato do número do processo brasileiro"""
        parts = process_number.split("-")
        if len(parts) != 2:
            return False

        # Verificar sequencial (7 dígitos)
        if len(parts[0]) != 7 or not parts[0].isdigit():
            return False

        # Verificar resto (DD.AAAA.J.TR.OOOO)
        rest_parts = parts[1].split(".")
        if len(rest_parts) != 5:
            return False

        # Validar cada parte
        expected_lengths = [2, 4, 1, 2, 4]
        for i, (part, length) in enumerate(zip(rest_parts, expected_lengths)):
            if len(part) != length or not part.isdigit():
                return False

        return True

    def _extract_publication_date(self, content: str) -> Optional[datetime]:
        """Extrai data de publicação"""
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(content)
            if match:
                try:
                    date_str = match.group(1)
                    return datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    continue
        return None

    def _extract_availability_date(self, content: str) -> Optional[datetime]:
        """Extrai data de disponibilização"""
        # Procurar por padrões específicos de disponibilização
        availability_patterns = [
            re.compile(
                r"disponibilizad[oa]\s+em\s+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
            ),
            re.compile(r"disponivel\s+em\s+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE),
        ]

        for pattern in availability_patterns:
            match = pattern.search(content)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%d/%m/%Y")
                except ValueError:
                    continue

        # Se não encontrar, usar data de publicação
        return self._extract_publication_date(content)

    def _extract_authors(self, content: str) -> List[str]:
        """Extrai lista de autores com limpeza"""
        authors = []

        for pattern in self.AUTHOR_PATTERNS:
            match = pattern.search(content)
            if match:
                authors_text = match.group(1).strip()

                # Dividir autores por separadores comuns
                raw_authors = re.split(r"[,;]|\s+e\s+|\s+and\s+", authors_text)

                for author in raw_authors:
                    cleaned_author = self._clean_author_name(author)
                    if cleaned_author and len(cleaned_author) > 3:
                        authors.append(cleaned_author)

                if authors:
                    break

        return authors[:5] if authors else ["Não identificado"]

    def _clean_author_name(self, name: str) -> str:
        """Limpa e normaliza nome do autor"""
        # Remover prefixos/sufixos comuns
        name = re.sub(r"^(sr\.?|sra\.?|dr\.?|dra\.?)\s*", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s*(cpf|rg|cnh)[:.\s]*\d+.*$", "", name, flags=re.IGNORECASE)

        # Limpar caracteres especiais
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)

        return name.strip().title()

    def _extract_lawyers(self, content: str) -> List[Lawyer]:
        """Extrai advogados com nome e OAB"""
        lawyers = []
        seen_oabs = set()

        for pattern in self.LAWYER_PATTERNS:
            matches = pattern.finditer(content)

            for match in matches:
                if len(match.groups()) == 2:
                    # Padrão: nome + OAB
                    name = match.group(1).strip()
                    oab = match.group(2) if match.group(2) else "Não informado"
                else:
                    # Padrão: OAB + nome (invertido)
                    oab = match.group(1)
                    name = match.group(2).strip()

                # Limpar e validar
                name = self._clean_lawyer_name(name)
                oab = self._clean_oab_number(oab)

                if name and len(name) > 3 and oab not in seen_oabs:
                    lawyers.append(Lawyer(name=name, oab=oab))
                    seen_oabs.add(oab)

                # Limitar número de advogados
                if len(lawyers) >= 3:
                    break

        return lawyers

    def _clean_lawyer_name(self, name: str) -> str:
        """Limpa nome do advogado"""
        # Remover prefixos profissionais
        name = re.sub(r"^(dr\.?|dra\.?|advogad[oa])\s*", "", name, flags=re.IGNORECASE)

        # Remover sufixos comuns
        name = re.sub(r"\s*(oab|advogad[oa]).*$", "", name, flags=re.IGNORECASE)

        # Limpar caracteres especiais
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)

        return name.strip().title()

    def _clean_oab_number(self, oab: str) -> str:
        """Limpa número da OAB"""
        if not oab:
            return "Não informado"

        # Extrair apenas números
        numbers = re.findall(r"\d+", oab)
        if numbers:
            return numbers[0]

        return "Não informado"

    def _extract_all_monetary_values(
        self, content: str
    ) -> Dict[str, Optional[MonetaryValue]]:
        """Extrai todos os valores monetários"""
        values = {}

        for value_type, patterns in self.MONETARY_PATTERNS.items():
            values[value_type] = self._extract_monetary_value_by_patterns(
                content, patterns
            )

        return values

    def _extract_monetary_value_by_patterns(
        self, content: str, patterns: List[re.Pattern]
    ) -> Optional[MonetaryValue]:
        """Extrai valor monetário usando lista de padrões"""
        for pattern in patterns:
            match = pattern.search(content)
            if match:
                try:
                    value_str = match.group(1)
                    decimal_value = self._parse_monetary_string(value_str)

                    if decimal_value and decimal_value > 0:
                        return MonetaryValue.from_real(decimal_value)

                except (ValueError, InvalidOperation):
                    continue

        return None

    def _parse_monetary_string(self, value_str: str) -> Optional[Decimal]:
        """Converte string monetária para Decimal"""
        # Limpar string
        cleaned = re.sub(r"[^\d.,]", "", value_str)

        if not cleaned:
            return None

        # Tratar diferentes formatos brasileiros
        # Ex: 1.500,50 -> 1500.50
        if "," in cleaned and "." in cleaned:
            # Formato: 1.234.567,89
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Formato: 1,234,567.89
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Apenas vírgula: 1234,56 -> 1234.56
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                # Vírgula como separador de milhares: 1,234 -> 1234
                cleaned = cleaned.replace(",", "")

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _calculate_confidence_score(
        self,
        process_number: str,
        authors: List[str],
        lawyers: List[Lawyer],
        monetary_values: Dict[str, Optional[MonetaryValue]],
        content: str,
    ) -> float:
        """Calcula score de confiança da extração"""
        score = 0.0

        # Processo válido: +0.3
        if process_number and self._validate_process_number_format(process_number):
            score += 0.3

        # Autores identificados: +0.2
        if authors and authors[0] != "Não identificado":
            score += 0.2
            # Bonus por múltiplos autores válidos
            if len(authors) > 1:
                score += 0.05

        # Advogados com OAB: +0.15
        valid_lawyers = [l for l in lawyers if l.oab != "Não informado"]
        if valid_lawyers:
            score += 0.15

        # Valores monetários: +0.25
        valid_values = [v for v in monetary_values.values() if v is not None]
        if valid_values:
            score += 0.15 + (len(valid_values) * 0.025)

        # Comprimento do conteúdo: +0.1
        if len(content) > 200:
            score += 0.1
        elif len(content) > 100:
            score += 0.05

        # Palavras-chave específicas do INSS: +0.05
        inss_keywords = [
            "inss",
            "instituto nacional",
            "seguro social",
            "aposentadoria",
            "beneficio",
        ]
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in inss_keywords if keyword in content_lower)
        score += min(keyword_count * 0.01, 0.05)

        return min(score, 1.0)
