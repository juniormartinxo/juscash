"""
API REST para execução de comandos do scraper.
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
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


class ScraperCommand(BaseModel):
    """Modelo para execução de comandos do scraper."""

    command: str
    args: Optional[Dict[str, Any]] = None


class ScraperArgs(BaseModel):
    """Modelo para argumentos opcionais dos comandos do scraper."""

    args: Optional[Dict[str, Any]] = None


def run_command_background(command: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Executa um comando do scraper em background."""
    try:
        cmd = []

        logger.info(f"📋 Executando comando: {command}")
        logger.info(f"📂 Diretório de trabalho: {SCRIPT_DIR}")

        if command == "monitor":
            cmd = [
                sys.executable,
                str(SCRIPT_DIR / "monitor_json_files.py"),
                "--api-endpoint",
                args.get("api_endpoint", "http://localhost:8000"),
                "--monitored-path",
                str(SCRIPT_DIR / "reports" / "json"),
                "--log-path",
                str(SCRIPT_DIR / "reports" / "log"),
            ]
        elif command == "scraper":
            cmd = [sys.executable, str(SCRIPT_DIR / "scraper_cli.py"), "run"]
            if args:
                for key, value in args.items():
                    cmd.extend([f"--{key}", str(value)])
        elif command == "multi_date_scraper":
            script_path = SCRIPT_DIR / "run_multi_date_scraper.py"
            logger.info(f"🔍 Verificando se o script existe: {script_path}")
            logger.info(f"📄 Arquivo existe: {script_path.exists()}")

            if not script_path.exists():
                raise FileNotFoundError(f"Script não encontrado: {script_path}")

            cmd = [sys.executable, str(script_path)]
            if args:
                for key, value in args.items():
                    cmd.extend([f"--{key}", str(value)])
        elif command == "scraper_cli":
            cmd = [sys.executable, str(SCRIPT_DIR / "scraper_cli.py"), "run"]
            if args:
                for key, value in args.items():
                    cmd.extend([f"--{key}", str(value)])
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


@app.post("/run")
async def run_command(command: ScraperCommand, background_tasks: BackgroundTasks):
    """
    Executa um comando do scraper.

    Comandos disponíveis:
    - monitor: Inicia o monitoramento de arquivos JSON
    - scraper: Executa o scraper básico (scraper_cli.py run)
    - multi_date_scraper: Executa o scraper para múltiplas datas
    - scraper_cli: Executa o scraper via CLI (mesmo que 'scraper')
    """
    try:
        background_tasks.add_task(run_command_background, command.command, command.args)
        return {"status": "success", "message": f"Comando {command.command} iniciado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Retorna o status dos serviços do scraper."""
    status = {"monitor": False, "scraper": False, "multi_date_scraper": False}
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
            ["pgrep", "-f", "scraper_cli.py"], capture_output=True, text=True
        )
        if result.stdout.strip():
            status["scraper"] = True
            pids["scraper"] = result.stdout.strip().split("\n")

        result = subprocess.run(
            ["pgrep", "-f", "run_multi_date_scraper.py"], capture_output=True, text=True
        )
        if result.stdout.strip():
            status["multi_date_scraper"] = True
            pids["multi_date_scraper"] = result.stdout.strip().split("\n")

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
        elif service == "scraper":
            subprocess.run(["pkill", "-f", "scraper_cli.py"], check=True)
        elif service == "multi_date_scraper":
            subprocess.run(["pkill", "-f", "run_multi_date_scraper.py"], check=True)
        else:
            raise HTTPException(status_code=400, detail=f"Serviço inválido: {service}")

        return {"status": "success", "message": f"Serviço {service} parado"}
    except subprocess.CalledProcessError:
        return {"status": "success", "message": f"Serviço {service} não estava rodando"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run/multi-date-scraper")
async def run_multi_date_scraper(
    background_tasks: BackgroundTasks, request: Optional[ScraperArgs] = None
):
    """Executa o scraper para múltiplas datas em background."""
    try:
        args = request.args if request else None
        background_tasks.add_task(run_command_background, "multi_date_scraper", args)
        return {
            "status": "success",
            "message": "Multi-date scraper iniciado em background",
            "command": "python run_multi_date_scraper.py",
            "args": args,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run/scraper-cli")
async def run_scraper_cli(
    background_tasks: BackgroundTasks, request: Optional[ScraperArgs] = None
):
    """Executa o scraper CLI em background."""
    try:
        args = request.args if request else None
        background_tasks.add_task(run_command_background, "scraper_cli", args)
        return {
            "status": "success",
            "message": "Scraper CLI iniciado em background",
            "command": "python scraper_cli.py run",
            "args": args,
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
            "run_command": "POST /run",
            "run_multi_date_scraper": "POST /run/multi-date-scraper",
            "run_scraper_cli": "POST /run/scraper-cli",
            "status": "GET /status",
            "stop_service": "POST /stop/{service}",
            "debug_paths": "GET /debug/paths",
            "debug_test_command": "POST /debug/test-command",
            "docs": "GET /docs",
        },
        "available_services": ["monitor", "scraper", "multi_date_scraper"],
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
        "run_multi_date_scraper_exists": (
            script_dir / "run_multi_date_scraper.py"
        ).exists(),
        "run_multi_date_scraper_path": str(script_dir / "run_multi_date_scraper.py"),
        "run_multi_date_scraper_is_executable": os.access(
            script_dir / "run_multi_date_scraper.py", os.X_OK
        ),
    }


@app.post("/debug/test-command")
async def test_command():
    """Testa a execução do comando multi_date_scraper de forma síncrona para debug."""
    try:
        script_path = SCRIPT_DIR / "run_multi_date_scraper.py"

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
