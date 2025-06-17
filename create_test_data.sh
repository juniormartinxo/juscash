#!/bin/bash

echo "🧪 Criando dados de teste para o KanbanBoard..."

# Login e obter token
echo "🔐 Fazendo login..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}' | \
  grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Erro ao obter token de autenticação"
    exit 1
fi

echo "✅ Token obtido com sucesso"

# Criar publicações de teste
echo "📝 Criando publicações de teste..."

# Publicação NOVA 1
curl -s -X POST http://localhost:8000/api/publications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "1000001-12.2024.8.26.0001",
    "availabilityDate": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "authors": ["João Silva", "Maria Santos"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Publicação de teste para status NOVA - Processo de aposentadoria por invalidez",
    "status": "NOVA"
  }' > /dev/null && echo "✅ Criada publicação NOVA 1" || echo "⚠️  Publicação NOVA 1 já existe ou erro"

# Publicação NOVA 2
curl -s -X POST http://localhost:8000/api/publications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "1000002-12.2024.8.26.0001",
    "availabilityDate": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "authors": ["Pedro Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Publicação de teste para status NOVA - Auxílio doença",
    "status": "NOVA"
  }' > /dev/null && echo "✅ Criada publicação NOVA 2" || echo "⚠️  Publicação NOVA 2 já existe ou erro"

# Publicação LIDA
curl -s -X POST http://localhost:8000/api/publications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "1000003-12.2024.8.26.0001",
    "availabilityDate": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "authors": ["Ana Costa"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Publicação de teste para status LIDA - Benefício por incapacidade",
    "status": "LIDA"
  }' > /dev/null && echo "✅ Criada publicação LIDA" || echo "⚠️  Publicação LIDA já existe ou erro"

# Publicação ENVIADA_PARA_ADV
curl -s -X POST http://localhost:8000/api/publications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "1000004-12.2024.8.26.0001",
    "availabilityDate": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "authors": ["Carlos Ferreira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Publicação de teste para status ENVIADA_PARA_ADV - Revisão de benefício",
    "status": "ENVIADA_PARA_ADV"
  }' > /dev/null && echo "✅ Criada publicação ENVIADA_PARA_ADV" || echo "⚠️  Publicação ENVIADA_PARA_ADV já existe ou erro"

# Publicação CONCLUIDA
curl -s -X POST http://localhost:8000/api/publications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "1000005-12.2024.8.26.0001",
    "availabilityDate": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "authors": ["Lucia Mendes"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "content": "Publicação de teste para status CONCLUIDA - Processo finalizado",
    "status": "CONCLUIDA"
  }' > /dev/null && echo "✅ Criada publicação CONCLUIDA" || echo "⚠️  Publicação CONCLUIDA já existe ou erro"

echo ""
echo "🎉 Dados de teste criados! Agora teste o KanbanBoard."
echo "🌐 Acesse: http://localhost:5173" 