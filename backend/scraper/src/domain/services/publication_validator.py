"""
Serviço de domínio para validação de publicações
"""

import re
from typing import List
from domain.entities.publication import Publication


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
    ) -> tuple[bool, str]:
        """
        Valida uma publicação completa

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Verificar número do processo
        if not PublicationValidator.validate_process_number(publication.process_number):
            return False, f"Número do processo inválido: '{publication.process_number}'"

        # Verificar termos obrigatórios no conteúdo
        if not PublicationValidator.contains_required_terms(
            publication.content, required_terms
        ):
            missing_terms = []
            content_lower = publication.content.lower()
            for term in required_terms:
                if term.lower() not in content_lower:
                    missing_terms.append(term)
            return False, f"Termos obrigatórios ausentes: {missing_terms}"

        # Verificar campos obrigatórios
        if not publication.authors:
            return False, "Campo 'authors' está vazio ou None"

        if not publication.content.strip():
            return False, "Campo 'content' está vazio"

        # Verificar se availability_date está presente
        if not publication.availability_date:
            return False, "Campo 'availability_date' está ausente"

        # Verificar se authors contém apenas strings válidas
        for i, author in enumerate(publication.authors):
            if not author or not author.strip():
                return False, f"Autor na posição {i} está vazio: '{author}'"
            if len(author.strip()) < 3:
                return False, f"Autor na posição {i} muito curto: '{author}'"

        return True, "Publicação válida"
