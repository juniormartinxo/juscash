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
    print_error ">>> Não foi possível acessar o diretório frontend"
    exit 1
}

# Instalar dependências
echo -e "${YELLOW}Instalando dependências do vite...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}Dependências do vite já instaladas!${NC}"
else
    pnpm install
    echo -e "${GREEN}Dependências do vite instaladas com sucesso!${NC}"
fi

# Verificar arquivos necessários
required_files=(".npmrc" "pnpm-lock.yaml" "package.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Arquivo $file não encontrado!${NC}"
        exit 1
    fi
done

cd ..

# Construir a imagem Docker
echo ""
echo -e "${YELLOW}Construindo imagem do Vite com Docker...${NC}"
echo ""
docker compose up -d vite --build --remove-orphans

# Verificar se o contêiner iniciou
if [ $? -eq 0 ]; then
    print_success "Contêiner 'juscash-vite' iniciado com sucesso!"
    echo ""
    echo -e "Acesse a aplicação em ${YELLOW}http://localhost:5173${NC}"
    echo ""
else
    print_error ">>> Falha ao iniciar o contêiner."
    echo ""
fi

echo -e "${GREEN}Setup do Vite concluído com sucesso!${NC}"
echo ""
