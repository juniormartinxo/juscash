#!/usr/bin/env python3
"""
Script executável para rodar o Multi-Date Multi-Worker Scraper
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


from multi_date_scraper import main
import asyncio

if __name__ == "__main__":
    print("🌟 Iniciando Multi-Date Multi-Worker Scraper...")
    print("📅 Data inicial: 17/03/2025")
    print("📅 Data final: Hoje")
    print("👥 Workers: 1")
    print("📂 Arquivo de progresso: src/scrap_workrs.json")
    print("-" * 60)

    asyncio.run(main())
