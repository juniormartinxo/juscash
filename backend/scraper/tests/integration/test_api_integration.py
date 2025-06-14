"""
Testes de integração com a API
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx

from src.infrastructure.api.api_client_adapter import ApiClientAdapter
from src.domain.entities.publication import Publication


class TestApiClientAdapter:
    """Testes de integração com cliente da API"""

    @pytest.fixture
    def api_client(self):
        return ApiClientAdapter()

    @pytest.mark.asyncio
    async def test_save_publication_success(self, api_client, sample_publication):
        """Testa salvamento bem-sucedido de publicação"""
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": {"publication": {"id": "test-id"}},
        }

        # Mock do cliente HTTP
        with pytest.mock.patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await api_client.save_publication(sample_publication)

            assert result is True

    @pytest.mark.asyncio
    async def test_save_publication_validation_error(
        self, api_client, sample_publication
    ):
        """Testa erro de validação na API"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Validation error"

        with pytest.mock.patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await api_client.save_publication(sample_publication)

            assert result is False

    @pytest.mark.asyncio
    async def test_save_publication_timeout(self, api_client, sample_publication):
        """Testa timeout na requisição"""
        with pytest.mock.patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            result = await api_client.save_publication(sample_publication)

            assert result is False
