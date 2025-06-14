"""
Adapter - Cliente para comunicação com a API
"""

import httpx
from typing import Dict, Any, Optional
from src.domain.ports.scraping_repository import ScrapingRepositoryPort
from src.domain.entities.publication import Publication
from src.domain.entities.scraping_execution import ScrapingExecution
from src.infrastructure.logging.logger import setup_logger
from src.infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class ApiClientAdapter(ScrapingRepositoryPort):
    """
    Implementação do repositório que comunica com a API via HTTP
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.api.base_url
        self.api_key = self.settings.api.scraper_api_key
        self.timeout = self.settings.api.timeout

    async def save_publication(self, publication: Publication) -> bool:
        """Salva publicação via API"""
        logger.debug(f"📤 Enviando publicação: {publication.process_number}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/scraper/publications",
                    json=publication.to_api_dict(),
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.api_key,
                    },
                )

                if response.status_code == 201:
                    logger.debug(f"✅ Publicação salva: {publication.process_number}")
                    return True
                elif response.status_code == 400:
                    logger.warning(f"⚠️  Validação falhou: {response.text}")
                    return False
                else:
                    logger.error(
                        f"❌ Erro HTTP {response.status_code}: {response.text}"
                    )
                    return False

        except httpx.ConnectError as error:
            logger.error(f"🔌 Erro de conexão com a API: {error}")
            logger.error(f"🌐 Verifique se a API está rodando em: {self.base_url}")
            return False
        except httpx.TimeoutException:
            logger.error(
                f"⏰ Timeout ao salvar publicação: {publication.process_number}"
            )
            return False
        except Exception as error:
            logger.error(f"❌ Erro ao salvar publicação: {error}")
            logger.error(f"🔧 Tipo do erro: {type(error).__name__}")
            return False

    async def save_scraping_execution(self, execution: ScrapingExecution) -> bool:
        """Salva informações da execução (logs locais)"""
        # Por enquanto, apenas logs. Pode ser implementado endpoint específico na API
        logger.info(f"📊 Execução concluída: {execution.execution_id}")
        logger.info(
            f"📈 Estatísticas: Found={execution.publications_found}, "
            f"New={execution.publications_new}, "
            f"Duplicated={execution.publications_duplicated}, "
            f"Failed={execution.publications_failed}"
        )
        return True

    async def check_publication_exists(self, process_number: str) -> bool:
        """Verifica se publicação já existe"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/publications",
                    params={"search": process_number, "limit": 1},
                    headers={"X-API-Key": self.api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("total", 0) > 0

                return False

        except httpx.ConnectError as error:
            logger.warning(f"🔌 Erro de conexão ao verificar existência: {error}")
            logger.warning(f"🌐 Verifique se a API está rodando em: {self.base_url}")
            return False  # Em caso de erro, assumir que não existe
        except Exception as error:
            logger.warning(f"⚠️  Erro ao verificar existência: {error}")
            logger.warning(f"🔧 Tipo do erro: {type(error).__name__}")
            return False  # Em caso de erro, assumir que não existe
