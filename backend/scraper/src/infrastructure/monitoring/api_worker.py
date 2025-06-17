"""
Improved API Worker with better error handling and validation.
"""

import json
import logging
import re
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import redis
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class APIWorkerError(Exception):
    """Base exception for API Worker errors."""

    pass


class ValidationError(APIWorkerError):
    """Raised when data validation fails."""

    pass


class APIError(APIWorkerError):
    """Raised when API request fails."""

    pass


class APIWorker:
    """Improved worker for processing JSON files from Redis queue."""

    def __init__(
        self,
        redis_url: str,
        api_endpoint: str,
        log_path: str,
        queue_name: str = "json_files_queue",
        processing_queue: str = "json_files_processing",
        failed_queue: str = "json_files_failed",
        max_retries: int = 5,
        processing_interval: float = 0.5,
        api_key: str = "scraper-dj-1t0blW7epxd72BnoGezVjjXUtmbE11WXp0oSDhXJUFNo3ZEC5UVDhYfjLJX1Jqb12fbRB4ZUjP",
    ):
        """Initialize the improved API worker."""
        self.redis_url = redis_url
        self.api_endpoint = api_endpoint
        self.log_path = Path(log_path)
        self.queue_name = queue_name
        self.processing_queue = processing_queue
        self.failed_queue = failed_queue
        self.max_retries = max_retries
        self.processing_interval = processing_interval
        self.redis_client: Optional[redis.Redis] = None
        self.api_key = api_key

        # Ensure log directory exists with proper permission handling
        self._ensure_log_directory()

        # Configure HTTP session
        self.session = self._create_http_session()

    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists with correct permissions."""
        try:
            self.log_path.mkdir(parents=True, exist_ok=True)
            # Tentar escrever um arquivo de teste
            test_file = self.log_path / "test_permissions.txt"
            test_file.write_text("test")
            test_file.unlink()
            logger.info(f"📁 Log directory ready: {self.log_path}")
        except PermissionError:
            # Se não conseguir escrever, usar diretório temporário
            import tempfile

            self.log_path = Path(tempfile.gettempdir()) / "juscash_logs"
            self.log_path.mkdir(exist_ok=True)
            logger.warning(f"⚠️ Using temp directory for logs: {self.log_path}")
        except Exception as e:
            logger.error(f"❌ Error setting up log directory: {e}")

    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with improved configuration."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=0,  # We handle retries manually
            backoff_factor=0,
            status_forcelist=[],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "JusCash-Scraper-Worker/1.0",
                "Accept": "application/json",
            }
        )

        return session

    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis with improved error handling."""
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=30,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                client.ping()
                logger.info("✅ Successfully connected to Redis")
                return client

            except redis.ConnectionError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Redis connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                else:
                    logger.error("❌ Failed to connect to Redis after all retries")
                    raise

    def _validate_and_format_date(
        self, date_field: Any, field_name: str, file_name: str
    ) -> str:
        """
        Valida e formata data para o formato ISO 8601 datetime completo.
        Retorna string no formato: "YYYY-MM-DDTHH:MM:SS.sssZ"
        """
        if not date_field or date_field is None:
            logger.warning(
                f"Campo {field_name} está vazio em {file_name}, usando data atual"
            )
            return datetime.now().isoformat() + "Z"

        try:
            # Se já é string, processar
            if isinstance(date_field, str):
                date_field = date_field.strip()
                if not date_field or date_field.lower() in ["none", "null", ""]:
                    return datetime.now().isoformat() + "Z"

                # Se já está no formato datetime ISO, validar e retornar
                if "T" in date_field:
                    try:
                        # Tentar parse como datetime ISO
                        parsed_dt = datetime.fromisoformat(
                            date_field.replace("Z", "+00:00")
                        )
                        return parsed_dt.isoformat() + "Z"
                    except ValueError:
                        pass

                # Se é apenas data (YYYY-MM-DD), adicionar tempo
                try:
                    parsed_date = datetime.strptime(date_field, "%Y-%m-%d")
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    pass

                # Tentar formato brasileiro (DD/MM/YYYY)
                try:
                    parsed_date = datetime.strptime(date_field, "%d/%m/%Y")
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    pass

                # Tentar formato americano (MM/DD/YYYY)
                try:
                    parsed_date = datetime.strptime(date_field, "%m/%d/%Y")
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    pass

                # Tentar outros formatos comuns
                common_formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%d/%m/%Y %H:%M",
                ]

                for fmt in common_formats:
                    try:
                        parsed_dt = datetime.strptime(date_field, fmt)
                        return parsed_dt.isoformat() + "Z"
                    except ValueError:
                        continue

            # Se é objeto datetime ou date, converter
            elif isinstance(date_field, datetime):
                return date_field.isoformat() + "Z"

            elif isinstance(date_field, date):
                # Converter date para datetime (meia-noite)
                dt = datetime.combine(date_field, datetime.min.time())
                return dt.isoformat() + "Z"

            # Se chegou até aqui, formato não reconhecido
            logger.warning(
                f"Formato de data não reconhecido para {field_name} em {file_name}: {date_field}, usando data atual"
            )
            return datetime.now().isoformat() + "Z"

        except Exception as e:
            logger.error(f"Erro ao processar data {field_name} em {file_name}: {e}")
            return datetime.now().isoformat() + "Z"

    def _safe_numeric_value(self, value: Any, default: int = 0) -> int:
        """Converte valor para inteiro de forma segura."""
        if value is None or value == "" or str(value).strip() == "":
            return default

        try:
            if isinstance(value, str):
                # Remover caracteres não numéricos exceto vírgula/ponto
                clean_value = re.sub(r"[^\d,.-]", "", value.strip())
                if not clean_value:
                    return default

                clean_value = clean_value.replace(",", ".")
                return int(float(clean_value) * 100)  # Converter para centavos

            return int(float(value) * 100) if value else default

        except (ValueError, TypeError) as e:
            logger.warning(f"Valor monetário inválido: {value} -> usando {default}")
            return default

    def _validate_json_data(self, data: Dict[str, Any], file_name: str) -> bool:
        """
        Validate JSON data before sending to API with Zod-compatible datetime format.
        """
        try:
            required_fields = [
                "process_number",
                "availability_date",
                "authors",
                "content",
            ]

            # Sanitizar conteúdo
            if data.get("content"):
                content = str(data["content"])
                dangerous_patterns = [
                    r"';|\s*;",
                    r"\|\|",
                    r"&&",
                    r"\bOR\b",
                    r"\bAND\b",
                    r"\bSELECT\b",
                    r"\bINSERT\b",
                    r"\bUPDATE\b",
                    r"\bDELETE\b",
                    r"\bDROP\b",
                    r"\bCREATE\b",
                    r"\bALTER\b",
                    r"\bEXEC\b",
                    r"\bUNION\b",
                ]

                for pattern in dangerous_patterns:
                    content = re.sub(pattern, "", content, flags=re.IGNORECASE)

                data["content"] = content.replace("'", "''")

            # Tratar valores monetários (mantém como está)
            def safe_numeric_value(value: Any, default: int = 0) -> int:
                if value is None or value == "" or str(value).strip() == "":
                    return default
                try:
                    if isinstance(value, str):
                        clean_value = re.sub(r"[^\d,.-]", "", value.strip())
                        if not clean_value:
                            return default
                        clean_value = clean_value.replace(",", ".")
                        return int(float(clean_value) * 100)
                    return int(float(value) * 100) if value else default
                except (ValueError, TypeError):
                    logger.warning(f"Valor monetário inválido em {file_name}: {value}")
                    return default

            data["gross_value"] = safe_numeric_value(data.get("gross_value"))
            data["net_value"] = safe_numeric_value(data.get("net_value"))
            data["interest_value"] = safe_numeric_value(data.get("interest_value"))
            data["attorney_fees"] = safe_numeric_value(data.get("attorney_fees"))

            # Tratar array de advogados
            if data.get("lawyers") is None:
                data["lawyers"] = []
            elif not isinstance(data["lawyers"], list):
                logger.warning(f"Campo lawyers não é array em {file_name}, convertendo")
                data["lawyers"] = []

            # Validar campos obrigatórios
            for field in required_fields:
                if field not in data:
                    logger.error(f"Campo obrigatório '{field}' ausente em {file_name}")
                    return False

                if not data[field] and field != "lawyers":
                    logger.error(
                        f"Campo obrigatório '{field}' está vazio em {file_name}"
                    )
                    return False

            # Validar tipos específicos
            if not isinstance(data["process_number"], str):
                logger.error(f"process_number deve ser string em {file_name}")
                return False

            if not isinstance(data["authors"], list) or len(data["authors"]) == 0:
                logger.error(f"authors deve ser array não-vazio em {file_name}")
                return False

            if not isinstance(data["content"], str):
                logger.error(f"content deve ser string em {file_name}")
                return False

            # Validar e formatar campos de data usando ISO-8601 DateTime
            data["publication_date"] = self._validate_and_format_date(
                data.get("publication_date"), "publication_date", file_name
            )

            data["availability_date"] = self._validate_and_format_date(
                data.get("availability_date"), "availability_date", file_name
            )

            # Validar valores monetários
            monetary_fields = [
                "gross_value",
                "net_value",
                "interest_value",
                "attorney_fees",
            ]
            for field in monetary_fields:
                if field in data and data[field] is not None:
                    if not isinstance(data[field], int) or data[field] < 0:
                        logger.error(
                            f"{field} deve ser inteiro não-negativo em {file_name}"
                        )
                        return False

            # Validar array de advogados
            if not isinstance(data["lawyers"], list):
                logger.error(f"lawyers deve ser array em {file_name}")
                return False

            for i, lawyer in enumerate(data["lawyers"]):
                if not isinstance(lawyer, dict):
                    logger.error(f"lawyers[{i}] deve ser objeto em {file_name}")
                    return False
                if "name" not in lawyer or not lawyer["name"]:
                    logger.error(f"lawyers[{i}].name é obrigatório em {file_name}")
                    return False

            logger.debug(f"✅ Validação com formato datetime passou para {file_name}")
            return True

        except Exception as e:
            logger.error(f"💥 Erro na validação para {file_name}: {e}", exc_info=True)
            return False

    def _send_to_api(
        self, data: Dict[str, Any], file_name: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send JSON data to API endpoint with improved error handling.
        Returns: Tuple of (success, error_message, error_code)
        """
        try:
            # Validate data before sending
            if not self._validate_json_data(data, file_name):
                return False, "Data validation failed", "VALIDATION_ERROR"

            # Prepare headers
            headers = {
                "X-Source-File": file_name,
                "X-Worker-ID": "api-worker-1",
                "X-Timestamp": datetime.now().isoformat(),
                "x-api-key": self.api_key,
            }

            url = f"{self.api_endpoint.rstrip('/')}/api/scraper/publications"

            # CORREÇÃO: Log detalhado para debug
            logger.debug(f"🚀 Enviando para API: {url}")
            logger.debug(f"📄 Arquivo: {file_name}")
            logger.debug(f"📊 Dados: {json.dumps(data, indent=2, default=str)}")

            # Send request
            response = self.session.post(
                url,
                json=data,
                headers=headers,
                timeout=30,
            )

            # Log response para debug
            logger.debug(f"📥 Resposta API: {response.status_code} - {response.text}")

            # Handle different response codes
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Successfully sent {file_name} to API")
                return True, None, None

            elif response.status_code == 400:
                # Validation error - don't retry
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                    error_code = error_data.get("code", "BAD_REQUEST")
                except:
                    error_msg = response.text
                    error_code = "BAD_REQUEST"

                logger.error(f"❌ Validation error for {file_name}: {error_msg}")
                return False, error_msg, error_code

            elif response.status_code == 409:
                # Duplicate - don't retry, consider as success
                logger.warning(f"⚠️ Duplicate publication {file_name} (already exists)")
                return True, None, None

            elif response.status_code == 429:
                # Rate limit - retry with longer delay
                logger.warning(f"⏳ Rate limited for {file_name}")
                return False, "Rate limited", "RATE_LIMIT"

            elif response.status_code >= 500:
                # Server error - retry
                error_msg = f"Server error {response.status_code}: {response.text}"
                logger.warning(f"🔄 Server error for {file_name}: {error_msg}")
                return False, error_msg, "SERVER_ERROR"

            else:
                # Other client errors - don't retry
                error_msg = f"Client error {response.status_code}: {response.text}"
                logger.error(f"❌ Client error for {file_name}: {error_msg}")
                return False, error_msg, "CLIENT_ERROR"

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            logger.warning(f"⏰ Timeout for {file_name}")
            return False, error_msg, "TIMEOUT"

        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - API may be down"
            logger.warning(f"🔌 Connection error for {file_name}")
            return False, error_msg, "CONNECTION_ERROR"

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                f"💥 Unexpected error for {file_name}: {error_msg}", exc_info=True
            )
            return False, error_msg, "UNEXPECTED_ERROR"

    def _calculate_backoff(
        self, retry_count: int, error_code: Optional[str] = None
    ) -> float:
        """Calculate backoff delay based on error type and retry count."""
        base_delay = 2**retry_count  # Exponential backoff

        # Adjust delay based on error type
        if error_code == "RATE_LIMIT":
            return min(base_delay * 2, 120)  # Longer delay for rate limits
        elif error_code == "CONNECTION_ERROR":
            return min(base_delay * 1.5, 60)  # Medium delay for connection issues
        else:
            return min(base_delay, 60)  # Standard delay

    def _should_retry(self, error_code: Optional[str]) -> bool:
        """Determine if error should be retried."""
        # Don't retry validation errors or client errors
        no_retry_codes = ["VALIDATION_ERROR", "BAD_REQUEST", "CLIENT_ERROR"]
        return error_code not in no_retry_codes

    def _process_item(self, queue_item: Dict[str, Any]) -> bool:
        """Process a single queue item with improved error handling."""
        file_path = queue_item.get("file_path")
        file_name = queue_item.get("file_name")
        retry_count = queue_item.get("retry_count", 0)

        logger.info(
            f"🔄 Processing {file_name} (attempt {retry_count + 1}/{self.max_retries})"
        )

        # Read JSON file
        json_data = self._read_json_file(file_path)
        if json_data is None:
            self._log_failure(queue_item, "Failed to read JSON file", "FILE_READ_ERROR")
            return False

        # Send to API
        success, error_message, error_code = self._send_to_api(json_data, file_name)

        if success:
            return True

        # Handle retry logic
        retry_count += 1
        queue_item["retry_count"] = retry_count
        queue_item["last_error"] = error_message
        queue_item["last_error_code"] = error_code

        # Check if should retry
        if not self._should_retry(error_code) or retry_count >= self.max_retries:
            # Don't retry or max retries reached
            self._log_failure(
                queue_item, error_message or "Processing failed", error_code
            )
            self.redis_client.lpush(self.failed_queue, json.dumps(queue_item))

            if not self._should_retry(error_code):
                logger.error(
                    f"❌ Not retrying {file_name} due to error type: {error_code}"
                )
            else:
                logger.error(f"❌ Max retries reached for {file_name}")
            return False

        # Calculate backoff and re-queue
        backoff_delay = self._calculate_backoff(retry_count, error_code)
        logger.info(
            f"⏳ Retrying {file_name} after {backoff_delay}s (error: {error_code})"
        )

        # Sleep for backoff period
        time.sleep(backoff_delay)

        # Re-queue the item
        self.redis_client.lpush(self.queue_name, json.dumps(queue_item))
        return False

    def _read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON file with better error handling."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"Successfully read {file_path}")
                return data
        except FileNotFoundError:
            logger.error(f"📁 File not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"🔧 Invalid JSON in file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"💥 Error reading file {file_path}: {e}")
            return None

    def _log_failure(
        self, queue_item: Dict[str, Any], error_message: str, error_code: str = None
    ) -> None:
        """Log failed processing attempt with improved details."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_name": queue_item.get("file_name"),
            "file_path": queue_item.get("file_path"),
            "error_message": error_message,
            "error_code": error_code,
            "retry_count": queue_item.get("retry_count", 0),
            "first_detected": queue_item.get("detected_at"),
            "last_error": queue_item.get("last_error"),
            "last_error_code": queue_item.get("last_error_code"),
            "processing_duration": (
                datetime.now()
                - datetime.fromisoformat(
                    queue_item.get("detected_at", datetime.now().isoformat())
                )
            ).total_seconds(),
        }

        # Create log file name with date
        log_file = self.log_path / f"failures_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            # Read existing logs or create new list
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new log entry
            logs.append(log_entry)

            # Write back to file
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            logger.info(
                f"📝 Logged failure for {queue_item.get('file_name')} to {log_file}"
            )

        except PermissionError as e:
            # Tentar usar diretório temporário como fallback
            logger.warning(
                f"⚠️ Erro de permissão: {e}. Tentando diretório temporário..."
            )
            try:
                import tempfile

                temp_log_path = Path(tempfile.gettempdir()) / "juscash_logs"
                temp_log_path.mkdir(exist_ok=True)

                temp_log_file = (
                    temp_log_path / f"failures_{datetime.now().strftime('%Y%m%d')}.json"
                )

                # Read existing logs or create new list
                if temp_log_file.exists():
                    with open(temp_log_file, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                else:
                    logs = []

                # Append new log entry
                logs.append(log_entry)

                # Write back to file
                with open(temp_log_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)

                logger.info(
                    f"📝 Logged failure for {queue_item.get('file_name')} to temp file: {temp_log_file}"
                )

            except Exception as temp_e:
                logger.error(f"💥 Erro também no diretório temporário: {temp_e}")
                # Como último recurso, apenas logar no console
                logger.error(f"📊 Falha não salva: {log_entry}")

        except Exception as e:
            logger.error(f"💥 Error writing to log file: {e}")
            # Tentar pelo menos logar no console
            logger.error(f"📊 Falha não salva: {log_entry}")

    def start(self) -> None:
        """Start the improved worker service."""
        try:
            # Connect to Redis
            self.redis_client = self._connect_redis()

            logger.info("🚀 Improved API Worker started")
            logger.info(f"📋 Processing queue: {self.queue_name}")
            logger.info(f"🎯 API endpoint: {self.api_endpoint}")
            logger.info(f"⏱️ Processing interval: {self.processing_interval}s")
            logger.info(f"🔄 Max retries: {self.max_retries}")

            processed_count = 0
            success_count = 0

            while True:
                try:
                    # Use blocking pop with timeout
                    result = self.redis_client.brpoplpush(
                        self.queue_name,
                        self.processing_queue,
                        timeout=30,
                    )

                    if result:
                        processed_count += 1

                        # Parse queue item
                        try:
                            queue_item = json.loads(result)
                        except json.JSONDecodeError:
                            logger.error(f"💥 Invalid JSON in queue: {result}")
                            self.redis_client.lrem(self.processing_queue, 1, result)
                            continue

                        # Process the item
                        success = self._process_item(queue_item)

                        if success:
                            success_count += 1

                        # Remove from processing queue
                        self.redis_client.lrem(self.processing_queue, 1, result)

                        # Log statistics every 10 items
                        if processed_count % 10 == 0:
                            success_rate = (success_count / processed_count) * 100
                            logger.info(
                                f"📊 Processed: {processed_count}, Success: {success_count} ({success_rate:.1f}%)"
                            )

                        # Wait before processing next item
                        time.sleep(self.processing_interval)

                    # Periodic Redis connection check
                    if int(time.time()) % 30 == 0:
                        try:
                            self.redis_client.ping()
                        except redis.ConnectionError:
                            logger.warning(
                                "🔌 Lost Redis connection, attempting to reconnect..."
                            )
                            self.redis_client = self._connect_redis()

                except redis.TimeoutError:
                    logger.debug("⏰ Redis operation timed out, retrying...")
                    time.sleep(1)
                    continue

                except KeyboardInterrupt:
                    logger.info("⏹️ Worker interrupted by user")
                    break

                except Exception as e:
                    logger.error(f"💥 Error processing queue item: {e}", exc_info=True)
                    time.sleep(5)

        except Exception as e:
            logger.error(f"🚨 Worker failed: {e}", exc_info=True)
            raise

        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the worker service."""
        logger.info("🛑 Stopping worker...")

        if self.redis_client:
            # Move any items from processing queue back to main queue
            moved_count = 0
            while True:
                item = self.redis_client.rpoplpush(
                    self.processing_queue, self.queue_name
                )
                if not item:
                    break
                moved_count += 1

            if moved_count > 0:
                logger.info(
                    f"🔄 Moved {moved_count} items from processing queue back to main queue"
                )

            self.redis_client.close()
            logger.info("🔌 Redis connection closed")

        if self.session:
            self.session.close()
            logger.info("🌐 HTTP session closed")

        logger.info("✅ Worker stopped successfully")

    def get_stats(self) -> Dict[str, Any]:
        """Get current worker statistics."""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        try:
            return {
                "queue_size": self.redis_client.llen(self.queue_name),
                "processing_size": self.redis_client.llen(self.processing_queue),
                "failed_size": self.redis_client.llen(self.failed_queue),
                "timestamp": datetime.now().isoformat(),
                "worker_status": "running",
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main entry point for the improved API worker."""
    import argparse
    import signal
    import sys

    # Determine base path relative to this script
    script_dir = Path(__file__).parent.parent.parent.parent

    parser = argparse.ArgumentParser(
        description="Improved API worker service for JusCash DJE system",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--redis-url", help="Redis connection URL (overrides environment variable)"
    )
    parser.add_argument(
        "--api-endpoint", required=True, help="API endpoint URL for sending JSON data"
    )
    parser.add_argument(
        "--log-path",
        default=str(script_dir / "reports" / "log"),
        help="Path for storing error logs",
    )
    parser.add_argument(
        "--max-retries", type=int, default=5, help="Maximum number of retry attempts"
    )
    parser.add_argument(
        "--interval", type=float, default=0.5, help="Processing interval in seconds"
    )
    parser.add_argument(
        "--queue-name", default="json_files_queue", help="Redis queue name"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]

    # Tentar adicionar file handler, mas usar só console se houver erro de permissão
    try:
        log_file_path = (
            Path(args.log_path) / f"worker_{datetime.now().strftime('%Y%m%d')}.log"
        )
        handlers.append(logging.FileHandler(log_file_path))
    except PermissionError:
        print(
            f"⚠️ Warning: Cannot write to log file in {args.log_path}, logging only to console"
        )
    except Exception as e:
        print(f"⚠️ Warning: Error setting up log file: {e}, logging only to console")

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Get Redis URL from args or environment
    try:
        from ..config.settings import Settings

        settings = Settings()
        redis_url = args.redis_url or settings.redis_url or "redis://localhost:6379/0"
    except ImportError:
        redis_url = args.redis_url or "redis://localhost:6379/0"

    logger.info("🎬 Starting JusCash API Worker")
    logger.info(f"🔗 Redis URL: {redis_url}")
    logger.info(f"🎯 API Endpoint: {args.api_endpoint}")
    logger.info(f"📁 Log Path: {args.log_path}")

    # Create worker
    worker = APIWorker(
        redis_url=redis_url,
        api_endpoint=args.api_endpoint,
        log_path=args.log_path,
        queue_name=args.queue_name,
        max_retries=args.max_retries,
        processing_interval=args.interval,
    )

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Test API endpoint before starting
        try:
            response = worker.session.get(
                args.api_endpoint.replace("/publications", "/health"), timeout=10
            )
            if response.status_code == 200:
                logger.info("✅ API health check passed")
            else:
                logger.warning(f"⚠️ API health check returned {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ API health check failed: {e}")

        # Start worker
        worker.start()

    except KeyboardInterrupt:
        logger.info("⏹️ Worker stopped by user")
    except Exception as e:
        logger.error(f"🚨 Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
