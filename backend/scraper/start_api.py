#!/usr/bin/env python3
"""
Script para iniciar a API do scraper.
"""

import os
import uvicorn
from pathlib import Path
import sys

# Adicionar src ao PYTHONPATH
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))


def main():
    """Inicia o servidor da API."""
    uvicorn.run(
        "src.infrastructure.web.scraper_api:app",
        host="0.0.0.0",
        port=int(os.getenv("SCRAPER_API_PORT", 5000)),
        reload=True,
    )


if __name__ == "__main__":
    main()
