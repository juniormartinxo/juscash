"""
Worker - Processador de publicações da fila Redis
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from domain.entities.publication import Publication, MonetaryValue
from infrastructure.queue.redis_queue_adapter import RedisQueueAdapter
from infrastructure.api.api_client_adapter import ApiClientAdapter

# from infrastructure.files.report_txt_saver import ReportTxtSaver  # Temporariamente desabilitado
from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class PublicationWorker:
    """
    Worker para processar publicações da fila Redis
    """

    def __init__(self):
        self.settings = get_settings()
        self.queue = RedisQueueAdapter()
        self.api_client = ApiClientAdapter()
        # self.report_saver = ReportTxtSaver()  # Temporariamente desabilitado
        self.is_running = False
        self._stop_event = asyncio.Event()

        # Configurar diretório de relatórios JSON
        self.json_dir = Path(self.settings.reports.json_dir)
        if not self.json_dir.exists():
            self.json_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Diretório JSON criado: {self.json_dir}")

    async def start(self):
        """Inicia o worker"""
        if self.is_running:
            logger.warning("⚠️  Worker já está executando")
            return

        self.is_running = True
        self._stop_event.clear()

        logger.info("🚀 Iniciando Publication Worker")
        logger.info("📊 Configurações:")
        logger.info(f"   📝 Fila: {self.settings.redis.queue_name}")
        logger.info(f"   🔄 Max tentativas: {self.settings.redis.max_retries}")
        logger.info(f"   ⏰ Delay retry: {self.settings.redis.retry_delay}s")
        logger.info(f"   📦 Batch size: {self.settings.redis.batch_size}")

        try:
            # Loop principal do worker
            while not self._stop_event.is_set():
                await self._process_batch()
                await self._process_delayed_publications()

                # Pequena pausa para não sobrecarregar
                await asyncio.sleep(1)

        except Exception as error:
            logger.error(f"❌ Erro no worker: {error}")
            raise
        finally:
            self.is_running = False
            logger.info("⏹️  Publication Worker finalizado")

    async def stop(self):
        """Para o worker gracefully"""
        logger.info("🛑 Parando Publication Worker...")
        self._stop_event.set()

        # Aguardar até 10 segundos para finalizar processamento atual
        for _ in range(10):
            if not self.is_running:
                break
            await asyncio.sleep(1)

        if self.is_running:
            logger.warning("⚠️  Worker ainda está executando após timeout")

    async def _process_batch(self):
        """Processa um lote de publicações"""
        batch_size = self.settings.redis.batch_size
        processed_count = 0

        for _ in range(batch_size):
            if self._stop_event.is_set():
                break

            # Tentar processar uma publicação
            publication_data = await self.queue.dequeue_publication()

            if not publication_data:
                # Fila vazia, parar o lote
                break

            success = await self._process_publication(publication_data)

            if success:
                processed_count += 1
                # Excluir arquivo JSON após sucesso
                await self._delete_json_file(publication_data)
            else:
                # Reenfileirar com retry ou mover para DLQ
                await self._handle_failed_publication(publication_data)

        if processed_count > 0:
            logger.info(
                f"📊 Lote processado: {processed_count} publicações enviadas para API"
            )

    async def _process_publication(self, publication_data: Dict[str, Any]) -> bool:
        """
        Processa uma publicação individual

        Args:
            publication_data: Dados da publicação

        Returns:
            True se processamento foi bem-sucedido
        """
        try:
            # Reconstituir entidade Publication
            publication = self._reconstruct_publication(publication_data)

            if not publication:
                logger.error(
                    f"❌ Erro ao reconstituir publicação: {publication_data.get('process_number')}"
                )
                return False

            # Enviar para API
            logger.debug(f"📤 Processando: {publication.process_number}")

            success = await self.api_client.save_publication(publication)

            if success:
                logger.debug(f"✅ Publicação processada: {publication.process_number}")
                return True
            else:
                logger.warning(f"⚠️  Falha ao processar: {publication.process_number}")
                return False

        except Exception as error:
            logger.error(f"❌ Erro ao processar publicação: {error}")
            logger.error(
                f"🔧 Dados: {publication_data.get('process_number', 'UNKNOWN')}"
            )
            return False

    async def _delete_json_file(self, publication_data: Dict[str, Any]) -> None:
        """
        Exclui o arquivo JSON após processamento bem-sucedido

        Args:
            publication_data: Dados da publicação
        """
        try:
            # Construir o caminho do arquivo
            process_number = publication_data.get("process_number", "")
            if not process_number:
                return

            safe_process_number = process_number.replace("/", "_").replace(".", "_")
            filename = f"{safe_process_number}.json"
            file_path = self.json_dir / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Arquivo JSON excluído: {filename}")
            else:
                logger.debug(f"⚠️ Arquivo JSON não encontrado: {filename}")

        except Exception as error:
            logger.error(f"❌ Erro ao excluir arquivo JSON: {error}")

    def _reconstruct_publication(self, publication_data: Dict[str, Any]) -> Publication:
        """
        Reconstitui entidade Publication a partir dos dados da fila

        Args:
            publication_data: Dados serializados da publicação

        Returns:
            Instância de Publication
        """
        try:
            from domain.entities.publication import Lawyer

            # Reconstituir publication_date
            publication_date = None
            if publication_data.get("publication_date"):
                publication_date = datetime.fromisoformat(
                    publication_data["publication_date"]
                )

            # Reconstituir availability_date (obrigatório)
            availability_date = datetime.now()
            if publication_data.get("availability_date"):
                availability_date = datetime.fromisoformat(
                    publication_data["availability_date"]
                )

            # Reconstituir lawyers
            lawyers = []
            for lawyer_data in publication_data.get("lawyers", []):
                if isinstance(lawyer_data, dict):
                    lawyers.append(
                        Lawyer(
                            name=lawyer_data.get("name", ""),
                            oab=lawyer_data.get("oab", ""),
                        )
                    )
                elif isinstance(lawyer_data, str):
                    # Formato string simples
                    lawyers.append(Lawyer(name=lawyer_data, oab=""))

            # Reconstituir valores monetários
            gross_value = None
            net_value = None
            interest_value = None
            attorney_fees = None

            monetary_values = publication_data.get("monetary_values", [])
            for mv_data in monetary_values:
                if isinstance(mv_data, dict):
                    amount_cents = mv_data.get("value", 0)
                    mv_type = mv_data.get("type", "").lower()

                    if "honorario" in mv_type or "attorney" in mv_type:
                        attorney_fees = MonetaryValue(amount_cents=amount_cents)
                    elif "juros" in mv_type or "interest" in mv_type:
                        interest_value = MonetaryValue(amount_cents=amount_cents)
                    elif "bruto" in mv_type or "gross" in mv_type:
                        gross_value = MonetaryValue(amount_cents=amount_cents)
                    elif "liquido" in mv_type or "net" in mv_type:
                        net_value = MonetaryValue(amount_cents=amount_cents)

            publication = Publication(
                process_number=publication_data["process_number"],
                publication_date=publication_date,
                availability_date=availability_date,
                authors=publication_data.get("authors", []),
                lawyers=lawyers,
                gross_value=gross_value,
                net_value=net_value,
                interest_value=interest_value,
                attorney_fees=attorney_fees,
                content=publication_data.get("content", ""),
                extraction_metadata=publication_data.get("metadata", {}),
            )

            return publication

        except Exception as error:
            logger.error(f"❌ Erro ao reconstituir publicação: {error}")
            logger.error(f"🔧 Dados: {publication_data}")
            return None

    async def _handle_failed_publication(self, publication_data: Dict[str, Any]):
        """
        Trata publicação que falhou no processamento

        Args:
            publication_data: Dados da publicação que falhou
        """
        retry_count = publication_data.get("retry_count", 0)
        max_retries = self.settings.redis.max_retries
        process_number = publication_data.get("process_number", "UNKNOWN")

        if retry_count < max_retries:
            # Reenfileirar com delay
            delay_seconds = self.settings.redis.retry_delay * (
                2**retry_count
            )  # Backoff exponencial

            logger.warning(
                f"🔄 Reenfileirando {process_number} (tentativa {retry_count + 1}/{max_retries}, delay: {delay_seconds}s)"
            )

            await self.queue.requeue_publication(publication_data, delay_seconds)
        else:
            # Máximo de tentativas atingido - mover para Dead Letter Queue e excluir arquivo
            logger.error(
                f"💀 Publicação {process_number} falhou após {max_retries} tentativas - movendo para DLQ"
            )
            await self._move_to_dead_letter_queue(publication_data)
            await self._delete_json_file(publication_data)

    async def _move_to_dead_letter_queue(self, publication_data: Dict[str, Any]):
        """
        Move publicação para Dead Letter Queue

        Args:
            publication_data: Dados da publicação
        """
        try:
            dlq_key = f"{self.settings.redis.queue_name}:dlq"

            # Adicionar timestamp de envio para DLQ
            publication_data["dlq_timestamp"] = asyncio.get_event_loop().time()
            publication_data["dlq_reason"] = "max_retries_exceeded"

            self.queue.redis_client.lpush(dlq_key, json.dumps(publication_data))

            logger.warning(
                f"💀 Publicação movida para DLQ: {publication_data.get('process_number')}"
            )

        except Exception as error:
            logger.error(f"❌ Erro ao mover para DLQ: {error}")

    async def _process_delayed_publications(self):
        """Processa fila com delay para mover publicações prontas"""
        try:
            await self.queue.process_delayed_queue()
        except Exception as error:
            logger.error(f"❌ Erro ao processar fila com delay: {error}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do worker

        Returns:
            Estatísticas do worker e da fila
        """
        queue_stats = self.queue.get_queue_stats()

        return {
            "worker_running": self.is_running,
            "queue_stats": queue_stats,
            "settings": {
                "queue_name": self.settings.redis.queue_name,
                "max_retries": self.settings.redis.max_retries,
                "retry_delay": self.settings.redis.retry_delay,
                "batch_size": self.settings.redis.batch_size,
            },
        }
