# Como Inserir Registros no Banco de Dados usando a API

## 1. Autenticação

Primeiro, você precisa se autenticar para obter um token:

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu-email@exemplo.com",
    "password": "sua-senha"
  }'
```

Resposta:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "...",
      "name": "...",
      "email": "..."
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "..."
    }
  }
}
```

## 2. Inserir uma Publicação

Use o token obtido na autenticação para fazer a requisição POST:

```bash
curl -X POST http://localhost:3000/api/publications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "processNumber": "1234567-89.2024.8.26.0100",
    "publicationDate": "2024-03-15T00:00:00.000Z",
    "availabilityDate": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva Santos", "Maria Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dr. Carlos Advogado",
        "oab": "123456"
      },
      {
        "name": "Dra. Ana Jurista", 
        "oab": "789012"
      }
    ],
    "grossValue": 150000,
    "netValue": 135000,
    "interestValue": 10000,
    "attorneyFees": 5000,
    "content": "Conteúdo completo da publicação do DJE sobre aposentadoria por invalidez...",
    "status": "NOVA",
    "scrapingSource": "DJE-SP",
    "caderno": "3",
    "instancia": "1",
    "local": "Capital",
    "parte": "1",
    "extractionMetadata": {
      "extraction_date": "2024-03-17T10:30:00.000Z",
      "source_url": "https://dje.tjsp.jus.br/...",
      "confidence_score": 0.95
    }
  }'
```

## 3. Exemplo com JavaScript/Node.js

```javascript
const axios = require('axios');

async function createPublication() {
  try {
    // 1. Fazer login
    const loginResponse = await axios.post('http://localhost:3000/api/auth/login', {
      email: 'seu-email@exemplo.com',
      password: 'sua-senha'
    });

    const token = loginResponse.data.data.tokens.accessToken;

    // 2. Criar publicação
    const publicationData = {
      processNumber: '1234567-89.2024.8.26.0100',
      publicationDate: '2024-03-15T00:00:00.000Z',
      availabilityDate: '2024-03-17T00:00:00.000Z',
      authors: ['João Silva Santos', 'Maria Oliveira'],
      defendant: 'Instituto Nacional do Seguro Social - INSS',
      lawyers: [
        { name: 'Dr. Carlos Advogado', oab: '123456' },
        { name: 'Dra. Ana Jurista', oab: '789012' }
      ],
      grossValue: 150000, // R$ 1.500,00 em centavos
      netValue: 135000,   // R$ 1.350,00 em centavos
      interestValue: 10000, // R$ 100,00 em centavos
      attorneyFees: 5000,   // R$ 50,00 em centavos
      content: 'Conteúdo completo da publicação do DJE sobre aposentadoria por invalidez...',
      status: 'NOVA'
    };

    const response = await axios.post('http://localhost:3000/api/publications', publicationData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('Publicação criada:', response.data);
    return response.data;

  } catch (error) {
    console.error('Erro:', error.response?.data || error.message);
    throw error;
  }
}

// Executar
createPublication();
```

## 4. Campos Obrigatórios

Os seguintes campos são **obrigatórios**:

- `processNumber`: Número do processo (string)
- `availabilityDate`: Data de disponibilidade (ISO string)
- `authors`: Array com pelo menos um autor (array de strings)
- `content`: Conteúdo da publicação (string)

## 5. Campos Opcionais

Todos os outros campos são opcionais e têm valores padrão:

- `defendant`: Padrão "Instituto Nacional do Seguro Social - INSS"
- `status`: Padrão "NOVA"
- `scrapingSource`: Padrão "DJE-SP"
- `caderno`: Padrão "3"
- `instancia`: Padrão "1"
- `local`: Padrão "Capital"
- `parte`: Padrão "1"

## 6. Valores Monetários

Os valores monetários devem ser enviados em **centavos**:

- R$ 1.500,00 = 150000 centavos
- R$ 100,50 = 10050 centavos

## 7. Status Válidos

- `NOVA`: Publicação nova (padrão)
- `LIDA`: Publicação lida
- `ENVIADA_PARA_ADV`: Enviada para advogado
- `CONCLUIDA`: Concluída

## 8. Resposta de Sucesso

```json
{
  "success": true,
  "data": {
    "publication": {
      "id": "cm123456789",
      "processNumber": "1234567-89.2024.8.26.0100",
      "publicationDate": "2024-03-15T00:00:00.000Z",
      "availabilityDate": "2024-03-17T00:00:00.000Z",
      "authors": ["João Silva Santos", "Maria Oliveira"],
      "defendant": "Instituto Nacional do Seguro Social - INSS",
      "lawyers": [
        { "name": "Dr. Carlos Advogado", "oab": "123456" }
      ],
      "grossValue": 150000,
      "netValue": 135000,
      "interestValue": 10000,
      "attorneyFees": 5000,
      "content": "Conteúdo completo da publicação...",
      "status": "NOVA",
      "createdAt": "2024-03-17T10:30:00.000Z",
      "updatedAt": "2024-03-17T10:30:00.000Z"
    }
  }
}
```

## 9. Endpoint para Scraper (Novo!)

### Autenticação via API Key

Para scrapers/bots, use o endpoint específico que não requer login de usuário:

```bash
curl -X POST http://localhost:3000/api/scraper/publications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key-do-scraper-aqui" \
  -d '{
    "processNumber": "1234567-89.2024.8.26.0100",
    "publicationDate": "2024-03-15T00:00:00.000Z",
    "availabilityDate": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva Santos", "Maria Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dr. Carlos Advogado",
        "oab": "123456"
      }
    ],
    "grossValue": 150000,
    "netValue": 135000,
    "interestValue": 10000,
    "attorneyFees": 5000,
    "content": "Conteúdo completo da publicação...",
    "status": "NOVA",
    "scrapingSource": "DJE-SP",
    "extractionMetadata": {
      "extraction_date": "2024-03-17T10:30:00.000Z",
      "source_url": "https://dje.tjsp.jus.br/...",
      "confidence_score": 0.95
    }
  }'
```

### Configuração da API Key

Adicione no seu arquivo `.env`:

```bash
SCRAPER_API_KEY="sua-chave-secreta-longa-e-segura-aqui"
```

### Vantagens do Endpoint Scraper

- **Sem necessidade de login**: Não precisa fazer autenticação de usuário
- **Rate limiting específico**: 1000 requests por 15 minutos (vs 100 para usuários)
- **Logs de auditoria**: Identificação clara da origem "SCRAPER"
- **Mesma validação**: Mantém toda a segurança de validação de dados

## 10. Tratamento de Erros

### Erro de Validação (400)

```json
{
  "success": false,
  "error": "Process number is required"
}
```

### Erro de Autenticação (401)

```json
{
  "success": false,
  "error": "Authorization token required"
}
```

### Erro de API Key (400/401)

```json
{
  "success": false,
  "error": "X-API-Key header is required"
}
```

```json
{
  "success": false,
  "error": "Invalid API Key"
}
```

### Erro de Processo Duplicado (500)

```json
{
  "success": false,
  "error": "Unique constraint failed on the fields: (`process_number`)"
}
```
