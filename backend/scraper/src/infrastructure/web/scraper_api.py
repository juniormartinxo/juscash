"""
API REST para execução de comandos do scraper.
"""

import os
import sys
import subprocess
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar caminhos
SCRIPT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

app = FastAPI(
    title="Scraper API", description="API para execução de comandos do scraper"
)

# Configurar CORS para permitir requisições do frontend
cors_origins = os.getenv(
    "CORS_ORIGIN", "http://localhost:5173,http://localhost:3000,http://localhost:8080"
).split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScraperCommand(BaseModel):
    """Modelo para execução de comandos do scraper."""

    command: str
    args: Optional[Dict[str, Any]] = None


class ScraperArgs(BaseModel):
    """Modelo para argumentos opcionais dos comandos do scraper."""

    args: Optional[Dict[str, Any]] = None


class ScrapingRequest(BaseModel):
    """Modelo para requisição de scraping com datas específicas."""

    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    headless: bool = True


def validate_date_range(start_date: str, end_date: str) -> None:
    """
    Valida formato e lógica das datas.

    Args:
        start_date: Data inicial no formato YYYY-MM-DD
        end_date: Data final no formato YYYY-MM-DD

    Raises:
        HTTPException: Se as datas são inválidas
    """
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"

    # Validar formato
    if not re.match(date_pattern, start_date):
        raise HTTPException(
            status_code=400,
            detail=f"Formato de start_date inválido. Use YYYY-MM-DD, recebido: {start_date}",
        )

    if not re.match(date_pattern, end_date):
        raise HTTPException(
            status_code=400,
            detail=f"Formato de end_date inválido. Use YYYY-MM-DD, recebido: {end_date}",
        )

    # Validar se as datas são válidas e se end_date não é anterior a start_date
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        if end_date_obj < start_date_obj:
            raise HTTPException(
                status_code=400,
                detail=f"Data final ({end_date}) não pode ser anterior à data inicial ({start_date})",
            )

        # verifica se as datas não são maiores que hoje
        if end_date_obj > datetime.now():
            raise HTTPException(
                status_code=400,
                detail=f"Data final ({end_date}) não pode ser maior que a data atual ({datetime.now().strftime('%Y-%m-%d')})",
            )

        if start_date_obj > datetime.now():
            raise HTTPException(
                status_code=400,
                detail=f"Data inicial ({start_date}) não pode ser maior que a data atual ({datetime.now().strftime('%Y-%m-%d')})",
            )

    except ValueError as e:
        if "Data final" not in str(e):  # Se não foi nosso erro customizado
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar datas: {e}",
            )
        raise  # Re-raise nosso erro customizado


def run_command_background(command: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Executa um comando do scraper em background."""
    try:
        cmd = []

        logger.info(f"📋 Executando comando: {command}")
        logger.info(f"📂 Diretório de trabalho: {SCRIPT_DIR}")

        if command == "monitor":
            api_endpoint = os.getenv("API_BASE_URL", "http://localhost:8000")
            if args and "api_endpoint" in args:
                api_endpoint = args["api_endpoint"]

            cmd = [
                sys.executable,
                str(SCRIPT_DIR / "monitor_json_files.py"),
                "--api-endpoint",
                api_endpoint,
                "--monitored-path",
                str(SCRIPT_DIR / "reports" / "json"),
                "--log-path",
                str(SCRIPT_DIR / "reports" / "log"),
            ]
        elif command == "scraping":
            cmd = [sys.executable, str(SCRIPT_DIR / "scraping.py"), "run"]
            if args and "start_date" in args and "end_date" in args:
                cmd.extend(
                    [
                        "--start-date",
                        args["start_date"],
                        "--end-date",
                        args["end_date"],
                        "--headless" if args.get("headless", True) else "--no-headless",
                    ]
                )
            else:
                raise ValueError(
                    f"Comando {command} requer argumentos start_date e end_date"
                )
        else:
            raise ValueError(f"Comando inválido: {command}")

        logger.info(f"🚀 Comando completo: {' '.join(cmd)}")

        # Executa o comando sem capturar stdout/stderr para permitir debug
        process = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            # Removido stdout=subprocess.PIPE, stderr=subprocess.PIPE para permitir logs
        )

        logger.info(f"✅ Processo iniciado com PID: {process.pid}")

    except Exception as e:
        logger.error(f"❌ Erro ao executar comando: {e}")
        print(f"Erro ao executar comando: {e}")
        raise


def run_scraping_py_background(
    start_date: str, end_date: str, headless: bool = True
) -> None:
    """Executa o scraping.py com datas específicas em background."""
    try:
        # Verificar se o arquivo scraping.py existe
        scraping_py_path = SCRIPT_DIR / "scraping.py"

        if not scraping_py_path.exists():
            raise FileNotFoundError(
                f"scraping.py não encontrado em: {scraping_py_path}"
            )

        # verifica se a data final é maior que a data inicial
        if datetime.strptime(end_date, "%Y-%m-%d") < datetime.strptime(
            start_date, "%Y-%m-%d"
        ):
            raise ValueError("A data final não pode ser menor que a data inicial")

        # Construir comando
        cmd = [
            sys.executable,
            str(scraping_py_path),
            "run",
            "--start-date",
            start_date,
            "--end-date",
            end_date,
        ]

        # Adicionar flag headless se necessário
        if headless:
            cmd.append("--headless")
        else:
            cmd.append("--no-headless")

        logger.info(f"🚀 Executando scraping.py: {' '.join(cmd)}")
        logger.info(f"📂 Diretório: {SCRIPT_DIR}")
        logger.info(f"📅 Período: {start_date} até {end_date}")
        logger.info(f"🖥️ Modo: {'headless' if headless else 'com interface'}")

        # Executa o comando
        process = subprocess.Popen(
            cmd, cwd=str(SCRIPT_DIR), env={**os.environ, "PYTHONPATH": str(SCRIPT_DIR)}
        )

        logger.info(f"✅ Scraping iniciado com PID: {process.pid}")

    except Exception as e:
        logger.error(f"❌ Erro ao executar scraping.py: {e}")
        print(f"Erro ao executar scraping.py: {e}")
        raise


@app.get("/status")
async def get_status():
    """Retorna o status dos serviços do scraper."""
    status = {"monitor": False, "scraping": False}
    pids = {}

    try:
        # Verifica processos python rodando
        result = subprocess.run(
            ["pgrep", "-f", "monitor_json_files.py"], capture_output=True, text=True
        )
        if result.stdout.strip():
            status["monitor"] = True
            pids["monitor"] = result.stdout.strip().split("\n")

        result = subprocess.run(
            ["pgrep", "-f", "scraping.py"], capture_output=True, text=True
        )

        if result.stdout.strip():
            status["scraping"] = True
            pids["scraping"] = result.stdout.strip().split("\n")

        return {
            "status": status,
            "pids": pids,
            "script_directory": str(SCRIPT_DIR),
            "python_executable": sys.executable,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop/{service}")
async def stop_service(service: str):
    """Para um serviço específico do scraper."""
    try:
        if service == "monitor":
            subprocess.run(["pkill", "-f", "monitor_json_files.py"], check=True)
        elif service == "scraping":
            subprocess.run(["pkill", "-f", "scraping.py"], check=True)
        else:
            raise HTTPException(status_code=400, detail=f"Serviço inválido: {service}")

        return {"status": "success", "message": f"Serviço {service} parado"}
    except subprocess.CalledProcessError:
        return {"status": "success", "message": f"Serviço {service} não estava rodando"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
async def run_scraping_manual(
    background_tasks: BackgroundTasks, request: ScrapingRequest
):
    """
    Executa o scraping.py com datas específicas (equivalente ao comando manual).

    Este endpoint executa exatamente o mesmo comando que você executaria manualmente:
    python scraping.py run --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--headless]
    """
    try:
        # Validar formato e lógica das datas
        validate_date_range(request.start_date, request.end_date)

        # Executar scraping em background
        background_tasks.add_task(
            run_scraping_py_background,
            request.start_date,
            request.end_date,
            request.headless,
        )

        command_str = f"python scraping.py run --start-date {request.start_date} --end-date {request.end_date}"
        if request.headless:
            command_str += " --headless"
        else:
            command_str += " --no-headless"

        return {
            "status": "success",
            "message": f"Scraping iniciado para período {request.start_date} até {request.end_date}",
            "command": command_str,
            "parameters": {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "headless": request.headless,
            },
            "note": "Mesmo comando que você executaria manualmente via terminal",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scraping/monitor")
async def run_scraping_monitor(
    background_tasks: BackgroundTasks, api_endpoint: str = "http://localhost:8000"
):
    """
    Executa o monitoramento de arquivos JSON.
    """
    args = {"api_endpoint": api_endpoint}
    background_tasks.add_task(run_command_background, "monitor", args)
    return {"status": "success", "message": "Monitoramento de arquivos JSON iniciado"}


@app.post("/scraping/today")
async def run_scraping_today(background_tasks: BackgroundTasks, headless: bool = True):
    """
    Executa o scraping da data atual (hoje) - conveniência.

    Equivale a:
    python scraping.py run --start-date HOJE --end-date HOJE [--headless]
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # Usar o mesmo endpoint interno
        background_tasks.add_task(run_scraping_py_background, today, today, headless)

        command_str = f"python scraping.py run --start-date {today} --end-date {today}"
        if headless:
            command_str += " --headless"
        else:
            command_str += " --no-headless"

        return {
            "status": "success",
            "message": f"Scraping da data atual ({today}) iniciado",
            "command": command_str,
            "parameters": {
                "start_date": today,
                "end_date": today,
                "headless": headless,
            },
            "note": "Execução automática da data atual",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Informações básicas da API."""
    return {
        "name": "Scraper API",
        "version": "1.0.0",
        "description": "API para execução de comandos do scraper DJE",
        "endpoints": {
            "run_scraping": "POST /run",
            "run_scraping_today": "POST /scraping/today",
            "run_scraping_monitor": "POST /scraping/monitor",
            "status": "GET /status",
            "stop_service": "POST /stop/{service}",
            "debug_paths": "GET /debug/paths",
            "debug_test_command": "POST /debug/test-command",
            "docs": "GET /docs",
        },
        "available_services": ["monitor", "scraping"],
        "debug_info": {
            "script_directory": str(SCRIPT_DIR),
            "python_executable": sys.executable,
        },
    }


@app.get("/debug/paths")
async def debug_paths():
    """Retorna informações de debug sobre caminhos e arquivos."""
    script_dir = SCRIPT_DIR

    return {
        "script_directory": str(script_dir),
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
        "files_in_script_dir": [f.name for f in script_dir.iterdir() if f.is_file()],
        "scraping_exists": (script_dir / "scraping.py").exists(),
        "scraping_path": str(script_dir / "scraping.py"),
        "scraping_is_executable": os.access(script_dir / "scraping.py", os.X_OK),
    }


@app.post("/debug/test-command")
async def test_command():
    """Testa a execução do comando scraping de forma síncrona para debug."""
    try:
        script_path = SCRIPT_DIR / "scraping.py"

        if not script_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Script não encontrado: {script_path}"
            )

        cmd = [sys.executable, str(script_path)]

        logger.info(f"🧪 Testando comando: {' '.join(cmd)}")

        # Executa de forma síncrona para capturar a saída
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=30,  # Timeout de 30 segundos para evitar travamento
        )

        return {
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "error": "Comando expirou após 30 segundos",
            "message": "O script pode estar rodando corretamente mas demora mais que 30 segundos",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
