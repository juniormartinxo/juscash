# scraper_cli.py
"""
Script principal da CLI
"""

#!/usr/bin/env python3

import sys
from pathlib import Path

# Adicionar src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src/local/"))

from src.cli.commands import cli

if __name__ == "__main__":
    cli()
