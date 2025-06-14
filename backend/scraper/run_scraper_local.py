#!/usr/bin/env python3
"""
Script para executar o scraper localmente
Simula a execução do Docker com PYTHONPATH correto
"""

import os
import sys
import subprocess

# Configurar o diretório de trabalho
scraper_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(scraper_dir)

# Configurar variáveis de ambiente
os.environ["PYTHONPATH"] = scraper_dir
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["POSTGRES_URL_ASYNC"] = (
    "postgresql+asyncpg://juscash_user:juscash_pass@localhost:5432/juscash_db"
)
os.environ["REDIS_URL"] = "redis://localhost:6379"

print("🚀 Iniciando Scraper DJE-SP (modo local)")
print(f"📁 Diretório: {scraper_dir}")
print(f"🐍 Python: {sys.executable}")
print(f"📦 PYTHONPATH: {os.environ['PYTHONPATH']}")
print("")

# Executar o scraper como módulo (igual ao Docker)
cmd = [sys.executable, "-m", "src.main"]

try:
    print(f"🔧 Comando: {' '.join(cmd)}")
    print("")

    # Executar o comando
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

except KeyboardInterrupt:
    print("\n⚠️ Execução interrompida pelo usuário")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    sys.exit(1)
