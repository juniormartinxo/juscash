#!/bin/bash

echo "🧹 Iniciando limpeza do workspace..."

# Remover arquivos .env.backup.* na raiz
echo "📝 Removendo arquivos .env.backup.*..."
rm -f .env.backup.*

# Remover todas as pastas node_modules
echo "📦 Removendo pastas node_modules..."
find . -type d -name "node_modules" -exec rm -rf {} +

# Remover todos os arquivos pnpm-lock.yaml
echo "🔒 Removendo arquivos pnpm-lock.yaml..."
find . -type f -name "pnpm-lock.yaml" -delete

# Remover pasta venv do scraper
echo "🐍 Removendo pasta venv do scraper..."
rm -rf backend/scraper/venv

# Remover a pasta generated do backend
echo "🔒 Removendo pasta generated do Prisma no backend..."
rm -rf backend/generated

echo "✨ Limpeza concluída com sucesso!" 