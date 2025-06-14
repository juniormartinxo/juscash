"""
Serviço de domínio para validação de publicações
"""

import re
from typing import List
from entities.publication import Publication


class PublicationValidator:
    """
    Serviço responsável por validar publicações extraídas
    """

    @staticmethod
    def validate_process_number(process_number: str) -> bool:
        """
        Valida formato do número do processo
        Formato esperado: NNNNNNN-DD.AAAA.J.TR.OOOO
        """
        pattern = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"
        return bool(re.match(pattern, process_number.strip()))

    @staticmethod
    def contains_required_terms(content: str, required_terms: List[str]) -> bool:
        """
        Verifica se o conteúdo contém todos os termos obrigatórios
        """
        content_lower = content.lower()
        return all(term.lower() in content_lower for term in required_terms)

    @staticmethod
    def validate_publication(
        publication: Publication, required_terms: List[str]
    ) -> bool:
        """
        Valida uma publicação completa
        """
        # Verificar número do processo
        if not PublicationValidator.validate_process_number(publication.process_number):
            return False

        # Verificar termos obrigatórios no conteúdo
        if not PublicationValidator.contains_required_terms(
            publication.content, required_terms
        ):
            return False

        # Verificar campos obrigatórios
        if not publication.authors:
            return False

        if not publication.content.strip():
            return False

        return True
