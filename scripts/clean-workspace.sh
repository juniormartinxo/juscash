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

if [ -f "backend/scraper/src/scrap_workers.json" ]; then
    echo "📝 Removendo arquivo scrap_workers.json do scraper..."
    rm backend/scraper/src/scrap_workers.json
fi

# Verificar se a pasta reports existe
if [ -d "backend/scraper/reports" ]; then
    # verificar se a pasta reports/json existe
    if [ -d "backend/scraper/reports/json" ]; then
        echo "📝 Removendo arquivos .json do scraper..."
        rm backend/scraper/reports/**/*.json
    fi
    
    if [ -d "backend/scraper/reports/pdf" ]; then
        echo "📝 Removendo arquivos .pdf do scraper..."
        rm backend/scraper/reports/**/*.pdf
    fi
fi



echo "✨ Limpeza concluída com sucesso!" 