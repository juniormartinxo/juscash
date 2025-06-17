#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para imprimir mensagens
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Navegar para o diretório do frontend
cd frontend || {
    print_error "Não foi possível acessar o diretório frontend"
    exit 1
}

# Instalar dependências
echo -e "${YELLOW}Instalando dependências do frontend...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}Dependências do frontend já instaladas!${NC}"
else
    pnpm install
    echo -e "${GREEN}Dependências do frontend instaladas com sucesso!${NC}"
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
docker build -t juscash-vite -f .docker/Dockerfile .

# Verificar se a construção foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Imagem Docker construída com sucesso!${NC}"
else
    echo "Erro ao construir a imagem Docker."
    exit 1
fi

# --- Adicione esta seção para iniciar o contêiner ---
echo -e "${YELLOW}Iniciando o contêiner Docker...${NC}"
docker run -d -p 5173:5173 --name juscash-frontend juscash-vite

# Verificar se o contêiner iniciou
if [ $? -eq 0 ]; then
    print_success "Contêiner 'juscash-frontend' iniciado com sucesso!"
    echo -e "Acesse a aplicação em ${YELLOW}http://localhost:5173${NC}"
else
    print_error "Falha ao iniciar o contêiner."
fi

cd ../

echo -e "${GREEN}Setup do frontend concluído com sucesso!${NC}"
echo -e "Para iniciar o frontend em modo de desenvolvimento, execute: ${YELLOW}docker run -p 5173:5173 juscash-vite${NC}"