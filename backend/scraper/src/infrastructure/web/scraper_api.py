"""
API REST para execução de comandos do scraper.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

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


def run_command_background(command: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Executa um comando do scraper em background."""
    try:
        cmd = []

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
        else:
            raise ValueError(f"Comando inválido: {command}")

        # Executa o comando
        subprocess.Popen(
            cmd, cwd=str(SCRIPT_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        raise


@app.post("/run")
async def run_command(command: ScraperCommand, background_tasks: BackgroundTasks):
    """
    Executa um comando do scraper.

    Comandos disponíveis:
    - monitor: Inicia o monitoramento de arquivos JSON
    - scraper: Executa o scraper
    """
    try:
        background_tasks.add_task(run_command_background, command.command, command.args)
        return {"status": "success", "message": f"Comando {command.command} iniciado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Retorna o status dos serviços do scraper."""
    status = {"monitor": False, "scraper": False}

    try:
        # Verifica processos python rodando
        result = subprocess.run(
            ["pgrep", "-f", "monitor_json_files.py"], capture_output=True, text=True
        )
        status["monitor"] = bool(result.stdout.strip())

        result = subprocess.run(
            ["pgrep", "-f", "scraper_cli.py"], capture_output=True, text=True
        )
        status["scraper"] = bool(result.stdout.strip())

        return status
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
        else:
            raise HTTPException(status_code=400, detail=f"Serviço inválido: {service}")

        return {"status": "success", "message": f"Serviço {service} parado"}
    except subprocess.CalledProcessError:
        return {"status": "success", "message": f"Serviço {service} não estava rodando"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
