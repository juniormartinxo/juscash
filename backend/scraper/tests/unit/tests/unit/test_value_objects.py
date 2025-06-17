import pytest

from src.shared.value_objects import process_number, Status, ScrapingCriteria, DJEUrl
from src.shared.exceptions import ValidationException


class Testprocess_number:
    """Testes unitários para process_number."""

    def test_valid_cnj_format(self):
        """Testa número no formato CNJ válido."""
        process = process_number("1234567-89.2024.8.26.0100")
        assert str(process) == "1234567-89.2024.8.26.0100"
        assert process.get_sequential_number() == "1234567"
        assert process.get_court_code() == "0100"

    def test_alternative_formats(self):
        """Testa formatos alternativos aceitos."""
        process = process_number("123456/2024")
        assert str(process) == "123456/2024"
        assert process.get_sequential_number() is None  # Não é formato CNJ

    def test_invalid_format_raises_error(self):
        """Testa que formato inválido levanta erro."""
        with pytest.raises(ValueError):
            process_number("")

        with pytest.raises(ValueError):
            process_number("@#$%")

    def test_equality_and_hash(self):
        """Testa igualdade e hash para uso em sets."""
        process1 = process_number("1234567-89.2024.8.26.0100")
        process2 = process_number("1234567-89.2024.8.26.0100")
        process3 = process_number("7654321-98.2024.8.26.0100")

        assert process1 == process2
        assert process1 != process3
        assert hash(process1) == hash(process2)
        assert hash(process1) != hash(process3)


class TestScrapingCriteria:
    """Testes unitários para ScrapingCriteria."""
    
    def test_valid_criteria(self, sample_criteria):
        """Testa criação de critérios válidos."""
        assert len(sample_criteria.required_terms) == 2
        assert sample_criteria.caderno == "3"
        assert sample_criteria.get_caderno_description() == "Caderno 3 - Judicial - 1ª Instância - Capital Parte 1"
    
    def test_empty_terms_raises_error(self):
        """Testa que termos vazios levantam erro."""
        with pytest.raises(ValueError):
            ScrapingCriteria(required_terms=())
        
        with pytest.raises(ValueError):
            ScrapingCriteria(required_terms=("", "  "))
    
    def test_matches_content(self, sample_criteria):
        """Testa verificação de conteúdo."""
        content = "Este processo envolve o Instituto Nacional do Seguro Social e INSS"
        assert sample_criteria.matches_content(content)
        
        content_invalid = "Este processo não tem os termos necessários"
        assert not sample_criteria.matches_content(content_invalid)


class TestDJEUrl:
    """Testes unitários para DJEUrl."""
    
    def test_main_url(self):
        """Testa URL principal."""
        dje_url = DJEUrl()
        assert dje_url.get_main_url() == "https://dje.tjsp.jus.br/cdje/index.do"
    
    def test_consultation_url(self):
        """Testa URL de consulta."""
        dje_url = DJEUrl()
        url = dje_url.get_consultation_url(
            volume="19",
            diary="4093", 
            notebook="12",
            page="3772"
        )
        expected = "https://dje.tjsp.jus.br/cdje/consultaSimples.do?cdVolume=19&nuDiario=4093&cdCaderno=12&nuSeqpagina=3772"
        assert url == expected
    
    def test_is_valid_dje_url(self):
        """Testa validação de URLs do DJE."""
        dje_url = DJEUrl()
        
        assert dje_url.is_valid_dje_url("https://dje.tjsp.jus.br/cdje/index.do")
        assert dje_url.is_valid_dje_url("https://dje.tjsp.jus.br/qualquer/pagina")
        assert not dje_url.is_valid_dje_url("https://outro-site.com")
        assert not dje_url.is_valid_dje_url("http://dje.tjsp.jus.br")  # HTTP vs HTTPS
