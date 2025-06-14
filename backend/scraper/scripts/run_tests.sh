# run_tests.sh
#!/bin/bash

# Script para executar todos os testes do scraper

echo "🧪 Executando testes do scraper DJE-SP"
echo "========================================"

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "📝 Crie o arquivo .env com base no exemplo fornecido"
    exit 1
fi

# Carregar variáveis de ambiente
source .env

# Verificar se SCRAPER_API_KEY está definida
if [ -z "$SCRAPER_API_KEY" ]; then
    echo "❌ SCRAPER_API_KEY não definida no .env"
    echo "🔑 Configure a variável SCRAPER_API_KEY no arquivo .env"
    exit 1
fi

echo "✅ Configuração validada"
echo ""

# Teste 1: Conexão com a API
echo "🔗 Teste 1: Conexão com a API"
python test_api_connection.py
if [ $? -ne 0 ]; then
    echo "❌ Teste de conexão com API falhou"
    exit 1
fi
echo ""

# Teste 2: Scraping manual (comentado para não executar por padrão)
echo "🕷️  Teste 2: Scraping manual (pular em desenvolvimento)"
echo "⚠️  Para executar: python test_scraper_manual.py"
echo ""

# Teste 3: Validação de dependências
echo "📦 Teste 3: Validação de dependências"
python -c "
import sys
try:
    import playwright
    import httpx
    import loguru
    import pydantic
    print('✅ Todas as dependências estão instaladas')
except ImportError as e:
    print(f'❌ Dependência faltando: {e}')
    sys.exit(1)
"
if [ $? -ne 0 ]; then
    echo "❌ Dependências não instaladas corretamente"
    exit 1
fi

echo ""
echo "🎉 Todos os testes passaram!"
echo "🚀 O scraper está pronto para uso"
