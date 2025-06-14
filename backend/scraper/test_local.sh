#!/bin/bash

# Define cores para a saída para melhor visualização
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sem Cor

# Armazena o primeiro argumento em uma variável
SCRIPT_ALVO=$1

# --- PASSO 1: Executar o teste ---
echo -e "${GREEN}PASSO 1: Executando teste...${NC}"
echo "--------------------------------------------------"
python -m src.local.${SCRIPT_ALVO}
echo "--------------------------------------------------"
echo -e "${GREEN}Teste de conexão finalizado.${NC}\n"