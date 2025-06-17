#!/bin/bash
set -e

echo "🚀 Iniciando sistema de scraping..."

# Criar diretórios necessários
mkdir -p /app/reports/json /app/reports/log /app/logs /tmp

echo "📁 Diretórios criados:"
ls -la /app/reports/

# Verificar se os arquivos Python existem
echo "🔍 Verificando arquivos Python..."
if [ ! -f "/app/src/main.py" ]; then
    echo "❌ Arquivo /app/src/main.py não encontrado!"
    ls -la /app/src/
    exit 1
fi

# Verificar variáveis de ambiente importantes
echo "🔧 Verificando variáveis de ambiente..."
echo "PYTHONPATH: ${PYTHONPATH:-'não definido'}"
echo "API_BASE_URL: ${API_BASE_URL:-'não definido'}"

# Testar se Python funciona
echo "🐍 Testando Python..."
python --version
python -c "import sys; print('Python path:', sys.path)"

# Verificar configuração do supervisor
echo "📋 Verificando configuração do supervisor..."
if [ ! -f "/etc/supervisor/conf.d/supervisord.conf" ]; then
    echo "❌ Arquivo de configuração do supervisor não encontrado!"
    exit 1
fi

echo "✅ Configuração do supervisor encontrada:"
cat /etc/supervisor/conf.d/supervisord.conf

# Garantir permissões corretas no diretório de socket
mkdir -p /tmp
chmod 755 /tmp

# Validar configuração do supervisor
echo "🧪 Testando configuração do supervisor..."
supervisord -t -c /etc/supervisor/conf.d/supervisord.conf

# Limpar possíveis processos anteriores
echo "🔄 Limpando processos supervisor existentes..."
pkill -f supervisord || true
rm -f /tmp/supervisor.sock || true
rm -f /tmp/supervisord.pid || true

sleep 2

# Iniciar supervisord em background
echo "🎯 Iniciando Supervisor..."
supervisord -c /etc/supervisor/conf.d/supervisord.conf

# Aguardar o socket ficar disponível
echo "⏳ Aguardando socket do supervisor ficar disponível..."
for i in {1..10}; do
    SOCK=$(find / -name "supervisor.sock" | head -n 1)
    if [ -S "$SOCK" ]; then
        echo "✅ Socket encontrado em $SOCK"
        break
    fi
    echo "⏳ Aguardando socket..."
    sleep 1
done

# Verificar status dos processos do supervisor
if [ -S "$SOCK" ]; then
    echo "📊 Status dos processos no supervisor:"
    supervisorctl -s unix://$SOCK status
else
    echo "❌ Socket supervisor.sock não encontrado! Verifique se o supervisor está rodando corretamente."
    exit 1
fi

# Mantém o container ativo exibindo os logs
echo "🟢 Sistema em execução. Acompanhando logs..."
tail -f /app/logs/*.log
