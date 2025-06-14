from typing import List, Optional
import aiohttp
from datetime import datetime
import json

from src.core.entities.publication import Publication
from src.core.ports.database_port import DatabasePort
from src.shared.exceptions import DatabaseException
from src.shared.logger import get_logger

logger = get_logger(__name__)


class APIRepository(DatabasePort):
    """
    Adaptador para comunicação com a API.

    Responsável por enviar os dados extraídos do DJE para a API,
    que por sua vez será responsável pela persistência.
    """

    def __init__(self, api_url: str):
        """
        Inicializa o repositório da API.

        Args:
            api_url: URL base da API
        """
        self.api_url = api_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_execution_id: Optional[str] = None

    async def initialize(self) -> None:
        """Inicializa a sessão HTTP."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                base_url=self.api_url, headers={"Content-Type": "application/json"}
            )
            logger.info("Sessão HTTP inicializada")

    async def start_scraping_execution(
        self,
        execution_type: str = "MANUAL",
        criteria: Optional[dict] = None,
        max_publications: Optional[int] = None,
    ) -> str:
        """
        Inicia uma nova execução de scraping na API.

        Args:
            execution_type: Tipo de execução
            criteria: Critérios de busca
            max_publications: Limite de publicações

        Returns:
            ID da execução
        """
        try:
            await self.initialize()

            payload = {
                "execution_type": execution_type,
                "criteria": criteria,
                "max_publications": max_publications,
                "started_at": datetime.now().isoformat(),
            }

            async with self.session.post(
                "/api/scraping-executions", json=payload
            ) as response:
                if response.status != 201:
                    raise DatabaseException(
                        "start_scraping_execution",
                        f"API retornou status {response.status}",
                    )

                data = await response.json()
                self.current_execution_id = data["id"]
                logger.info(
                    f"Execução de scraping iniciada: {self.current_execution_id}"
                )
                return self.current_execution_id

        except Exception as e:
            logger.error(f"Erro ao iniciar execução de scraping: {str(e)}")
            raise DatabaseException("start_scraping_execution", str(e))

    async def save_publication(self, publication: Publication) -> Publication:
        """
        Envia uma publicação para a API.

        Args:
            publication: Publicação a ser salva

        Returns:
            Publicação salva com ID atualizado
        """
        try:
            await self.initialize()

            payload = {
                "publication": publication.to_dict(),
                "scraping_execution_id": self.current_execution_id,
            }

            async with self.session.post("/api/publications", json=payload) as response:
                if response.status != 201:
                    raise DatabaseException(
                        "save_publication", f"API retornou status {response.status}"
                    )

                data = await response.json()
                return Publication.from_dict(data)

        except Exception as e:
            logger.error(f"Erro ao salvar publicação: {str(e)}")
            raise DatabaseException("save_publication", str(e))

    async def save_publications(
        self, publications: List[Publication]
    ) -> List[Publication]:
        """
        Envia múltiplas publicações para a API.

        Args:
            publications: Lista de publicações a serem salvas

        Returns:
            Lista de publicações salvas
        """
        try:
            await self.initialize()

            payload = {
                "publications": [pub.to_dict() for pub in publications],
                "scraping_execution_id": self.current_execution_id,
            }

            async with self.session.post(
                "/api/publications/batch", json=payload
            ) as response:
                if response.status != 201:
                    raise DatabaseException(
                        "save_publications", f"API retornou status {response.status}"
                    )

                data = await response.json()
                return [Publication.from_dict(pub) for pub in data]

        except Exception as e:
            logger.error(f"Erro ao salvar publicações: {str(e)}")
            raise DatabaseException("save_publications", str(e))

    async def finish_scraping_execution(
        self,
        execution_id: str,
        status: str,
        stats: dict,
        error_details: Optional[dict] = None,
    ) -> None:
        """
        Finaliza uma execução de scraping na API.

        Args:
            execution_id: ID da execução
            status: Status final
            stats: Estatísticas da execução
            error_details: Detalhes de erro se houver
        """
        try:
            await self.initialize()

            payload = {
                "status": status,
                "stats": stats,
                "error_details": error_details,
                "finished_at": datetime.now().isoformat(),
            }

            async with self.session.patch(
                f"/api/scraping-executions/{execution_id}", json=payload
            ) as response:
                if response.status != 200:
                    raise DatabaseException(
                        "finish_scraping_execution",
                        f"API retornou status {response.status}",
                    )

                logger.info(f"Execução de scraping finalizada: {execution_id}")

        except Exception as e:
            logger.error(f"Erro ao finalizar execução de scraping: {str(e)}")
            raise DatabaseException("finish_scraping_execution", str(e))

    async def close(self) -> None:
        """Fecha a sessão HTTP."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Sessão HTTP fechada")
