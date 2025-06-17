"""
Adapter - Cliente para comunicação com a API
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from domain.ports.scraping_repository import ScrapingRepositoryPort
from domain.entities.publication import Publication
from domain.entities.scraping_execution import ScrapingExecution
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

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
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Mínimo de 1 segundo entre requisições

        # Validar configurações críticas
        if not self.api_key:
            logger.error("❌ SCRAPER_API_KEY não configurada!")
            logger.error("   Configure a variável de ambiente SCRAPER_API_KEY")
        elif len(self.api_key) < 32:
            logger.warning("⚠️  SCRAPER_API_KEY parece muito curta (< 32 caracteres)")

        logger.debug(f"🔗 API Base URL: {self.base_url}")
        logger.debug(f"🔑 API Key configurada: {'✅' if self.api_key else '❌'}")
        logger.debug(f"⏰ Timeout: {self.timeout}s")

    async def _wait_for_rate_limit(self, retry_after: int = None):
        """Implementa rate limiting com backoff exponencial"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time

        # Se tiver retry_after, usa ele, senão usa o intervalo mínimo
        wait_time = max(
            retry_after or self._min_request_interval,
            self._min_request_interval - time_since_last_request,
        )

        if wait_time > 0:
            logger.debug(f"⏳ Aguardando {wait_time:.2f}s por rate limiting")
            await asyncio.sleep(wait_time)

        self._last_request_time = asyncio.get_event_loop().time()

    async def save_publication(self, publication: Publication) -> bool:
        """Salva publicação via API"""
        logger.debug(f"📤 Enviando publicação: {publication.process_number}")

        max_retries = 3
        retry_count = 0
        base_delay = 1.0

        while retry_count < max_retries:
            try:
                await self._wait_for_rate_limit()

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    api_data = publication.to_api_dict()

                    # Log detalhado para debug
                    logger.warning(
                        f"🔍 JSON completo sendo enviado para {publication.process_number}:"
                    )
                    import json

                    logger.warning(json.dumps(api_data, ensure_ascii=False, indent=2))

                    response = await client.post(
                        f"{self.base_url}/api/scraper/publications",
                        json=api_data,
                        headers={
                            "Content-Type": "application/json; charset=utf-8",
                            "X-API-Key": self.api_key,
                        },
                    )

                    if response.status_code == 201:
                        logger.debug(
                            f"✅ Publicação salva: {publication.process_number}"
                        )
                        return True
                    elif response.status_code == 400:
                        try:
                            error_data = response.json()
                            logger.warning(
                                f"⚠️  Validação falhou para {publication.process_number}:"
                            )
                            logger.warning(f"   📋 Erro da API: {error_data}")

                            # Tentar extrair detalhes específicos do erro
                            if isinstance(error_data, dict):
                                if "error" in error_data:
                                    logger.warning(
                                        f"   ❌ Mensagem: {error_data['error']}"
                                    )
                                if "details" in error_data:
                                    logger.warning(
                                        f"   🔍 Detalhes: {error_data['details']}"
                                    )
                                if "validation" in error_data:
                                    logger.warning(
                                        f"   📝 Validação: {error_data['validation']}"
                                    )
                                if "field" in error_data:
                                    logger.warning(
                                        f"   🏷️  Campo: {error_data['field']}"
                                    )

                        except Exception:
                            logger.warning(
                                f"⚠️  Validação falhou para {publication.process_number}: {response.text}"
                            )

                        # Log dos dados enviados para debug
                        api_data = publication.to_api_dict()
                        logger.warning(f"📤 Dados enviados para API:")
                        logger.warning(
                            f"   🔢 Número processo: {api_data.get('process_number')}"
                        )
                        logger.warning(
                            f"   📅 Data publicação: {api_data.get('publicationDate')}"
                        )
                        logger.warning(
                            f"   📅 Data disponibilização: {api_data.get('availabilityDate')}"
                        )
                        logger.warning(f"   👥 Autores: {api_data.get('authors')}")
                        logger.warning(f"   ⚖️  Advogados: {api_data.get('lawyers')}")
                        logger.warning(
                            f"   💰 Valores: gross={api_data.get('grossValue')}, net={api_data.get('netValue')}, interest={api_data.get('interestValue')}, fees={api_data.get('attorneyFees')}"
                        )
                        logger.warning(
                            f"   📝 Conteúdo (primeiros 100 chars): {api_data.get('content', '')[:100]}..."
                        )
                        return False
                    elif response.status_code == 429:
                        try:
                            error_data = response.json()
                            retry_after = int(error_data.get("retryAfter", 60))
                            logger.warning(
                                f"⚠️  Rate limit atingido para {publication.process_number}:"
                            )
                            logger.warning(f"   ⏰ Aguardar: {retry_after}s")
                            logger.warning(
                                f"   📊 Tentativa: {retry_count + 1}/{max_retries}"
                            )
                            logger.warning(f"   🔄 Resposta completa: {error_data}")
                        except:
                            retry_after = 60
                            logger.warning(
                                f"⚠️  Rate limit atingido para {publication.process_number} (resposta: {response.text})"
                            )

                        await self._wait_for_rate_limit(retry_after)
                        retry_count += 1
                        continue
                    elif response.status_code == 401:
                        logger.error(
                            f"🔐 Erro de autenticação para {publication.process_number}:"
                        )
                        logger.error("   ❌ API Key inválida ou não configurada")
                        logger.error("   🔧 Verifique a variável SCRAPER_API_KEY")
                        logger.error(
                            f"   📤 API Key enviada: {'***' + self.api_key[-4:] if self.api_key else 'NENHUMA'}"
                        )
                        return False  # Não tentar novamente para erro de auth
                    else:
                        logger.error(
                            f"❌ Erro HTTP {response.status_code} para {publication.process_number}: {response.text}"
                        )
                        retry_count += 1
                        await asyncio.sleep(base_delay * (2**retry_count))
                        continue

            except httpx.ConnectError as error:
                logger.error(f"🔌 Erro de conexão com a API: {error}")
                logger.error(f"🌐 Verifique se a API está rodando em: {self.base_url}")
                retry_count += 1
                await asyncio.sleep(base_delay * (2**retry_count))
                continue
            except httpx.TimeoutException:
                logger.error(
                    f"⏰ Timeout ao salvar publicação: {publication.process_number}"
                )
                retry_count += 1
                await asyncio.sleep(base_delay * (2**retry_count))
                continue
            except Exception as error:
                logger.error(f"❌ Erro ao salvar publicação: {error}")
                logger.error(f"🔧 Tipo do erro: {type(error).__name__}")
                retry_count += 1
                await asyncio.sleep(base_delay * (2**retry_count))
                continue

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
