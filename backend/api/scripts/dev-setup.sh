#!/bin/bash

# Garante que o script pare se houver algum erro
set -e

echo "🔧 Configurando ambiente de desenvolvimento..."

# Cria o diretório de geração do Prisma se não existir
mkdir -p src/generated/prisma

# Ajusta as permissões do diretório de geração do Prisma
echo "📁 Ajustando permissões do diretório Prisma..."
chmod -R 755 src/generated/prisma

# Gera o Prisma Client
echo "⚡ Gerando Prisma Client..."
pnpm prisma:generate

# Gerar cliente Prisma
echo "Gerando cliente Prisma..."
npx prisma generate

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env
fi

# Verificar se o diretório dist existe
if [ ! -d "dist" ]; then
    echo "Criando diretório dist..."
    mkdir dist
fi

echo "✅ Setup concluído com sucesso!"
