#!/usr/bin/env python3
"""
Script para executar o scraper e criar diretórios necessários
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Configurar o diretório base
BASE_DIR = Path(__file__).parent
SCRAPER_DIR = BASE_DIR / "backend" / "scraper"

# Criar diretórios de saída (sem subdiretórios de data)
REPORTS_DIR = SCRAPER_DIR / "reports"
TXT_DIR = REPORTS_DIR / "txt"
JSON_DIR = REPORTS_DIR / "json"

# Criar diretórios se não existirem
TXT_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 Diretório TXT: {TXT_DIR}")
print(f"📁 Diretório JSON: {JSON_DIR}")

# Mudar para o diretório do scraper
os.chdir(SCRAPER_DIR)

# Configurar PYTHONPATH
os.environ["PYTHONPATH"] = str(SCRAPER_DIR)

# Executar o scraper
print("🚀 Iniciando scraper...")
subprocess.run([sys.executable, "-m", "src.main"])