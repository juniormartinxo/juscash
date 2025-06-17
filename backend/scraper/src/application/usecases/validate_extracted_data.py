"""
Use Case - Validação avançada de dados extraídos
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

from domain.entities.publication import Publication
from domain.services.publication_validator import PublicationValidator
from infrastructure.logging.logger import setup_logger

logger = setup_logger(__name__)


class ValidateExtractedDataUseCase:
    """
    Use case para validação avançada de dados extraídos
    """

    def __init__(self):
        self.validator = PublicationValidator()
        self.validation_rules = self._setup_validation_rules()

    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Configura regras de validação"""
        return {
            "process_number": {
                "required": True,
                "pattern": r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$",
                "weight": 0.3,
            },
            "authors": {
                "required": True,
                "min_length": 3,
                "max_count": 10,
                "weight": 0.2,
            },
            "content": {
                "required": True,
                "min_length": 50,
                "max_length": 10000,
                "weight": 0.2,
            },
            "defendant": {
                "expected_value": "Instituto Nacional do Seguro Social - INSS",
                "weight": 0.1,
            },
            "dates": {
                "availabilityDate_required": True,
                "max_future_days": 7,
                "weight": 0.1,
            },
            "monetary_values": {
                "min_value_cents": 100,  # R$ 1,00
                "max_value_cents": 100000000,  # R$ 1.000.000,00
                "weight": 0.1,
            },
        }

    async def execute(
        self, publications: List[Publication], required_terms: List[str]
    ) -> Tuple[List[Publication], List[Dict[str, Any]]]:
        """
        Valida lista de publicações extraídas

        Args:
            publications: Lista de publicações para validar
            required_terms: Termos obrigatórios que devem estar presentes

        Returns:
            Tuple contendo:
            - Lista de publicações válidas
            - Lista de relatórios de validação (incluindo inválidas)
        """
        logger.info(f"🔍 Validando {len(publications)} publicações extraídas")

        valid_publications = []
        validation_reports = []

        for i, publication in enumerate(publications):
            try:
                report = await self._validate_single_publication(
                    publication, required_terms
                )
                validation_reports.append(report)

                if report["is_valid"]:
                    valid_publications.append(publication)
                    logger.debug(
                        f"✅ Publicação {i + 1} válida: {publication.process_number}"
                    )
                else:
                    logger.warning(
                        f"⚠️  Publicação {i + 1} inválida: {report['errors']}"
                    )

            except Exception as error:
                error_report = {
                    "publication_index": i,
                    "process_number": getattr(publication, "process_number", "UNKNOWN"),
                    "is_valid": False,
                    "validation_score": 0.0,
                    "errors": [f"Erro durante validação: {error}"],
                    "warnings": [],
                    "validation_timestamp": datetime.now().isoformat(),
                }
                validation_reports.append(error_report)
                logger.error(f"❌ Erro ao validar publicação {i + 1}: {error}")

        logger.info(
            f"📊 Validação concluída: {len(valid_publications)}/{len(publications)} válidas"
        )

        return valid_publications, validation_reports

    async def _validate_single_publication(
        self, publication: Publication, required_terms: List[str]
    ) -> Dict[str, Any]:
        """Valida uma única publicação"""

        report = {
            "process_number": publication.process_number,
            "is_valid": True,
            "validation_score": 0.0,
            "errors": [],
            "warnings": [],
            "details": {},
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Validar número do processo
        process_score = self._validate_process_number(publication, report)

        # Validar autores
        authors_score = self._validate_authors(publication, report)

        # Validar conteúdo
        content_score = self._validate_content(publication, required_terms, report)

        # Validar réu
        defendant_score = self._validate_defendant(publication, report)

        # Validar datas
        dates_score = self._validate_dates(publication, report)

        # Validar valores monetários
        monetary_score = self._validate_monetary_values(publication, report)

        # Calcular score total
        total_score = (
            process_score * self.validation_rules["process_number"]["weight"]
            + authors_score * self.validation_rules["authors"]["weight"]
            + content_score * self.validation_rules["content"]["weight"]
            + defendant_score * self.validation_rules["defendant"]["weight"]
            + dates_score * self.validation_rules["dates"]["weight"]
            + monetary_score * self.validation_rules["monetary_values"]["weight"]
        )

        report["validation_score"] = total_score
        report["is_valid"] = len(report["errors"]) == 0 and total_score >= 0.7

        return report

    def _validate_process_number(
        self, publication: Publication, report: Dict[str, Any]
    ) -> float:
        """Valida número do processo"""
        if not publication.process_number:
            report["errors"].append("Número do processo não fornecido")
            return 0.0

        if not self.validator.validate_process_number(publication.process_number):
            report["errors"].append(
                f"Formato inválido do número do processo: {publication.process_number}"
            )
            return 0.0

        # Validação adicional: verificar se é um processo recente
        try:
            year_part = publication.process_number.split(".")[1]
            process_year = int(year_part)
            current_year = datetime.now().year

            if process_year < 2020 or process_year > current_year + 1:
                report["warnings"].append(f"Ano do processo suspeito: {process_year}")
                return 0.8
        except (IndexError, ValueError):
            report["warnings"].append("Não foi possível validar ano do processo")
            return 0.9

        report["details"]["process_number_valid"] = True
        return 1.0

    def _validate_authors(
        self, publication: Publication, report: Dict[str, Any]
    ) -> float:
        """Valida lista de autores"""
        if not publication.authors:
            report["errors"].append("Lista de autores vazia")
            return 0.0

        rules = self.validation_rules["authors"]

        # Verificar se há autores válidos
        valid_authors = [
            author
            for author in publication.authors
            if len(author.strip()) >= rules["min_length"]
        ]

        if not valid_authors:
            report["errors"].append("Nenhum autor válido encontrado")
            return 0.0

        if len(publication.authors) > rules["max_count"]:
            report["warnings"].append(
                f"Muitos autores ({len(publication.authors)}), pode ser erro de parsing"
            )
            return 0.7

        # Verificar nomes suspeitos
        suspicious_authors = [
            author
            for author in publication.authors
            if author.lower() in ["não identificado", "n/a", "sem nome"]
        ]

        if suspicious_authors:
            report["warnings"].append(f"Autores suspeitos: {suspicious_authors}")
            return 0.8

        report["details"]["authors_count"] = len(publication.authors)
        report["details"]["valid_authors_count"] = len(valid_authors)
        return 1.0

    def _validate_content(
        self,
        publication: Publication,
        required_terms: List[str],
        report: Dict[str, Any],
    ) -> float:
        """Valida conteúdo da publicação"""
        if not publication.content:
            report["errors"].append("Conteúdo da publicação vazio")
            return 0.0

        rules = self.validation_rules["content"]
        content_length = len(publication.content)

        if content_length < rules["min_length"]:
            report["errors"].append(
                f"Conteúdo muito curto: {content_length} caracteres"
            )
            return 0.0

        if content_length > rules["max_length"]:
            report["warnings"].append(
                f"Conteúdo muito longo: {content_length} caracteres"
            )

        # Verificar termos obrigatórios (pelo menos um deve estar presente)
        if not self.validator.contains_required_terms(
            publication.content, required_terms
        ):
            report["errors"].append(
                f"Nenhum dos termos obrigatórios encontrado: {required_terms}"
            )
            return 0.0

        # Verificar qualidade do conteúdo
        quality_score = self._assess_content_quality(publication.content)

        if quality_score < 0.5:
            report["warnings"].append(
                "Qualidade do conteúdo baixa (muitos caracteres especiais ou repetições)"
            )

        report["details"]["content_length"] = content_length
        report["details"]["content_quality"] = quality_score
        report["details"]["required_terms_found"] = required_terms

        return min(1.0, quality_score + 0.3)  # Bonus por ter termos obrigatórios

    def _validate_defendant(
        self, publication: Publication, report: Dict[str, Any]
    ) -> float:
        """Valida réu (deve ser sempre INSS)"""
        expected_defendant = self.validation_rules["defendant"]["expected_value"]

        if publication.defendant != expected_defendant:
            report["warnings"].append(
                f"Réu diferente do esperado: '{publication.defendant}' vs '{expected_defendant}'"
            )
            return 0.5

        report["details"]["defendant_correct"] = True
        return 1.0

    def _validate_dates(
        self, publication: Publication, report: Dict[str, Any]
    ) -> float:
        """Valida datas da publicação"""
        score = 1.0

        # Data de disponibilização é obrigatória
        if not publication.availability_date:
            report["errors"].append("Data de disponibilização não fornecida")
            return 0.0

        # Verificar se a data não é muito no futuro
        max_future_days = self.validation_rules["dates"]["max_future_days"]
        max_future_date = datetime.now() + timedelta(days=max_future_days)

        if publication.availability_date > max_future_date:
            report["errors"].append(
                f"Data de disponibilização muito no futuro: {publication.availability_date}"
            )
            return 0.0

        # Verificar consistência entre datas
        if publication.publication_date and publication.availability_date:
            if publication.publication_date > publication.availability_date:
                report["warnings"].append(
                    "Data de publicação posterior à data de disponibilização"
                )
                score = 0.8

        # Verificar se as datas são muito antigas (mais de 2 anos)
        two_years_ago = datetime.now() - timedelta(days=730)
        if publication.availability_date < two_years_ago:
            report["warnings"].append("Data de disponibilização muito antiga")
            score = 0.9

        report["details"]["dates_valid"] = True
        return score

    def _validate_monetary_values(
        self, publication: Publication, report: Dict[str, Any]
    ) -> float:
        """Valida valores monetários"""
        rules = self.validation_rules["monetary_values"]
        values = [
            ("gross_value", publication.gross_value),
            ("net_value", publication.net_value),
            ("interest_value", publication.interest_value),
            ("attorney_fees", publication.attorney_fees),
        ]

        valid_values_count = 0
        total_values_count = 0

        for value_name, value in values:
            if value is not None:
                total_values_count += 1

                # Verificar limites
                if value.amount_cents < rules["min_value_cents"]:
                    report["warnings"].append(
                        f"{value_name} muito baixo: R$ {value.to_real()}"
                    )
                elif value.amount_cents > rules["max_value_cents"]:
                    report["warnings"].append(
                        f"{value_name} muito alto: R$ {value.to_real()}"
                    )
                else:
                    valid_values_count += 1

        # Verificar consistências lógicas
        if publication.gross_value and publication.net_value:
            if (
                publication.net_value.amount_cents
                > publication.gross_value.amount_cents
            ):
                report["warnings"].append("Valor líquido maior que valor bruto")

        if total_values_count == 0:
            report["warnings"].append("Nenhum valor monetário encontrado")
            return 0.5

        report["details"]["monetary_values_count"] = total_values_count
        report["details"]["valid_monetary_values"] = valid_values_count

        return (
            valid_values_count / total_values_count if total_values_count > 0 else 0.5
        )

    def _assess_content_quality(self, content: str) -> float:
        """Avalia qualidade do conteúdo"""
        if not content:
            return 0.0

        # Calcular ratio de caracteres alfanuméricos
        alphanumeric_count = sum(1 for c in content if c.isalnum() or c.isspace())
        alphanumeric_ratio = alphanumeric_count / len(content)

        # Penalizar excesso de caracteres especiais
        if alphanumeric_ratio < 0.7:
            return 0.3

        # Verificar repetições excessivas
        words = content.lower().split()
        if len(words) > 0:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)

            if repetition_ratio < 0.3:  # Muita repetição
                return 0.4

        # Verificar comprimento das sentenças
        sentences = content.split(".")
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        )

        if avg_sentence_length < 3:  # Sentenças muito curtas
            return 0.6

        return min(1.0, alphanumeric_ratio + 0.2)
