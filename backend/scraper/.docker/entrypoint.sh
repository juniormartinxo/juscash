#!/bin/bash

# Inicia o primeiro processo em background
echo "Iniciando src.main..."
python -m src.main &

# Inicia a API do Scraper
echo "Iniciando src.infrastructure.web.scraper_api..."
python -m src.infrastructure.web.scraper_api &

# Inicia o segundo processo em background
echo "Iniciando monitor_json_files.py..."
python monitor_json_files.py &

# Inicia o terceiro processo em foreground para manter o container ativo
# Se este processo terminar, o container para.
echo "Iniciando scraper_cli.py..."
python scraper_cli.py run

# Opcional: Se todos pudessem rodar em background, você usaria 'wait'
# wait -n
# exit $?