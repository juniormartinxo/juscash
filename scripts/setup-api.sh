#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Iniciando setup da infraestrutura da API...${NC}"

cd backend/api

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não encontrado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro.${NC}"
    exit 1
fi

# Verificar se o pnpm está instalado
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}pnpm não encontrado. Instalando pnpm...${NC}"
    npm install -g pnpm
fi

# Instalar dependências
echo -e "${YELLOW}Instalando dependências da API...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}Dependências da API já instaladas!${NC}"
else
    pnpm install
    echo -e "${GREEN}Dependências da API instaladas com sucesso!${NC}"
fi

# Verificar arquivos necessários
required_files=(".npmrc" "pnpm-lock.yaml" "package.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Arquivo $file não encontrado!${NC}"
        exit 1
    fi
done

# Construir a imagem Docker
echo -e "${YELLOW}Construindo imagem Docker...${NC}"
docker build -t juscash-api -f .docker/Dockerfile .

# Verificar se a construção foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Imagem Docker construída com sucesso!${NC}"
else
    echo "Erro ao construir a imagem Docker."
    exit 1
fi

cd ../../

echo -e "${GREEN}Setup concluído com sucesso!${NC}"
echo -e "Para iniciar a API em modo de desenvolvimento, execute: ${YELLOW}docker run -p 3000:3000 juscash-api${NC}"
