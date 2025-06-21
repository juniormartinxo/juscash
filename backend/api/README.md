# 📋 Sistema de Gerenciamento DJE - API

> API RESTful para gerenciamento de publicações do Diário da Justiça Eletrônico (DJE) de São Paulo, desenvolvida com Node.js, Express.js, TypeScript e Clean Architecture.

## 🏗️ Arquitetura

Este projeto segue os princípios de **Clean Architecture** (Arquitetura Hexagonal), garantindo separação clara de responsabilidades:

```txt
src/
├── domain/              # Entidades e regras de negócio
│   ├── entities/        # Entidades do domínio
│   ├── repositories/    # Contratos dos repositórios
│   └── services/        # Serviços do domínio
├── application/         # Casos de uso
│   └── usecases/        # Casos de uso da aplicação
├── infrastructure/      # Implementações técnicas
│   ├── database/        # Adapters do Prisma
│   ├── security/        # Autenticação JWT
│   └── web/            # Controllers, Routes, Middleware
└── shared/             # Utilitários compartilhados
    ├── config/         # Configurações
    ├── utils/          # Utilitários
    └── validation/     # Schemas de validação
```

## 🚀 Tecnologias

- **Node.js 20+** - Runtime JavaScript
- **Express.js 5.x** - Framework web
- **TypeScript** - Tipagem estática
- **Prisma ORM** - Object-Relational Mapping
- **PostgreSQL** - Banco de dados
- **JWT** - Autenticação
- **Zod** - Validação de schemas
- **Winston** - Sistema de logs
- **Docker** - Containerização

## 📋 Funcionalidades

### 🔐 Autenticação

- [x] Cadastro de usuários com validação de senha complexa
- [x] Login com JWT (Access + Refresh tokens)
- [x] Middleware de autenticação
- [x] Hash seguro de senhas (bcrypt)

### 📄 Publicações

- [x] Listagem paginada de publicações
- [x] Busca e filtros avançados
- [x] Atualização de status (Kanban)
- [x] Visualização detalhada

### 🛡️ Segurança

- [x] Rate limiting
- [x] Validação rigorosa de inputs
- [x] Sanitização de dados
- [x] Headers de segurança (Helmet)
- [x] CORS configurado

### 📊 Observabilidade

- [x] Logs estruturados (Winston)
- [x] Health check endpoint
- [x] Error handling centralizado
- [x] Request/Response logging

## 🛠️ Instalação e Uso

### Pré-requisitos

- Node.js 20+
- pnpm 8+
- Docker e Docker Compose
- PostgreSQL 16+ (opcional se usar Docker)

### 🚀 Configuração Rápida

```bash
# Clonar o repositório
git clone <repository-url>
cd dje-management-api

# Executar setup automático
pnpm run setup
```

O script `setup` irá:

1. Instalar dependências
2. Criar arquivo `.env` a partir do `.env.example`
3. Subir PostgreSQL e Redis com Docker
4. Executar migrações do banco
5. Popular dados iniciais (seeds)

### 🐳 Com Docker (Recomendado)

```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs da API
docker-compose logs -f api

# Parar serviços
docker-compose down
```

### 💻 Desenvolvimento Local

```bash
# Instalar dependências
pnpm install

# Copiar arquivo de ambiente
cp .env.example .env

# Configurar variáveis no .env
# DATABASE_URL="postgresql://dje_user:dje_password@localhost:5432/dje_db"
# JWT_ACCESS_SECRET="your-super-secret-key"

# Executar migrações
pnpm prisma:migrate

# Gerar cliente Prisma
pnpm prisma:generate

# Popular dados iniciais
pnpm db:seed

# Iniciar em modo desenvolvimento
pnpm dev
```

## 📋 Variáveis de Ambiente

```bash
# Database
DATABASE_URL="postgresql://user:password@host:port/database"

# JWT Secrets (OBRIGATÓRIO ALTERAR EM PRODUÇÃO!)
JWT_ACCESS_SECRET="your-super-secret-access-key-min-32-chars"
JWT_REFRESH_SECRET="your-super-secret-refresh-key-min-32-chars"

# Server
API_PORT=3001
NODE_ENV=development
CORS_ORIGIN="http://localhost:3000"

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info
```

## 🔗 Endpoints da API

### Autenticação

#### POST `/api/auth/register`

Cadastrar novo usuário.

**Body:**

```json
{
  "name": "João Silva",
  "email": "joao@exemplo.com",
  "password": "MinhaSenh@123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "name": "João Silva",
      "email": "joao@exemplo.com"
    },
    "tokens": {
      "accessToken": "jwt-token",
      "refreshToken": "refresh-token"
    }
  }
}
```

#### POST `/api/auth/login`

Fazer login.

**Body:**

```json
{
  "email": "joao@exemplo.com",
  "password": "MinhaSenh@123"
}
```

### Publicações (Requer Autenticação)

#### GET `/api/publications`

Listar publicações com filtros.

**Query Parameters:**

- `page` (number): Página (padrão: 1)
- `limit` (number): Itens por página (padrão: 30)
- `status` (string): Status da publicação
- `startDate` (ISO string): Data inicial
- `endDate` (ISO string): Data final
- `search` (string): Termo de busca

**Headers:**

```txt
Authorization: Bearer <access-token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "publications": [...],
    "pagination": {
      "current": 1,
      "total": 10,
      "count": 150,
      "perPage": 30
    }
  }
}
```

#### GET `/api/publications/:id`

Obter publicação específica.

#### PUT `/api/publications/:id/status`

Atualizar status da publicação.

**Body:**

```json
{
  "status": "LIDA"
}
```

### Utilitários

#### GET `/health`

Health check do serviço.

#### GET `/api`

Documentação básica da API.

## 🗄️ Modelo de Dados

### User

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

### Publication

```typescript
interface Publication {
  id: string;
  process_number: string;
  publicationDate?: Date;
  availability_date: Date;
  authors: string[];
  defendant: string; // Sempre "INSS"
  lawyers?: Array<{ name: string; oab: string }>;
  gross_value?: number; // Em centavos
  net_value?: number;
  interest_value?: number;
  attorney_fees?: number;
  content: string;
  status: 'NOVA' | 'LIDA' | 'ENVIADA_PARA_ADV' | 'CONCLUIDA';
  createdAt: Date;
  updatedAt: Date;
}
```

## 🧪 Testes

```bash
# Executar testes (a implementar)
pnpm test

# Coverage (a implementar)
pnpm test:coverage
```

## 📊 Monitoring e Logs

### Health Check

```bash
curl http://localhost:3001/health
```

### Logs

Os logs são salvos em:

- `logs/error.log` - Apenas erros
- `logs/combined.log` - Todos os logs
- Console (desenvolvimento)

### Métricas

- Rate limiting por IP/usuário
- Tempo de resposta das requisições
- Contadores de erro por endpoint

## 🚀 Deploy

### Build para Produção

```bash
# Build da aplicação
pnpm build

# Executar migrações em produção
pnpm prisma:migrate:deploy

# Iniciar aplicação
pnpm start
```

### Docker em Produção

```bash
# Build da imagem
docker build -t dje-api .

# Executar container
docker run -p 3001:3001 --env-file .env dje-api
```

### Variáveis Obrigatórias em Produção

```bash
NODE_ENV=production
DATABASE_URL="postgresql://..."
JWT_ACCESS_SECRET="strong-secret-min-32-chars"
JWT_REFRESH_SECRET="another-strong-secret-min-32-chars"
```

## 🔒 Segurança

### Validação de Senhas

- Mínimo 8 caracteres
- Pelo menos 1 letra maiúscula
- Pelo menos 1 letra minúscula
- Pelo menos 1 número
- Pelo menos 1 caractere especial

### Rate Limiting

- 100 requisições por 15 minutos por IP/usuário
- Configurável via variáveis de ambiente

### Tokens JWT

- Access token: 15 minutos
- Refresh token: 7 dias
- Secrets robustos obrigatórios em produção

## 🤝 Desenvolvimento

### Comandos Úteis

```bash
# Desenvolvimento com reload automático
pnpm dev

# Lint e formatação
pnpm lint

# Type checking
pnpm type-check

# Prisma Studio (interface visual do banco)
pnpm prisma:studio

# Reset completo do banco
pnpm prisma:reset
```

### Estrutura de Commits

```txt
feat: nova funcionalidade
fix: correção de bug
docs: documentação
style: formatação
refactor: refatoração
test: testes
chore: manutenção
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🔧 Troubleshooting

### Problemas com Permissões do Prisma

Se você encontrar erros de permissão ao gerar o Prisma Client, como:

```bash
EACCES: permission denied, copyfile '.../node_modules/.pnpm/@prisma+client@6.9.0_prisma@6.9.0_typescript@5.8.3__typescript@5.8.3/node_modules/@prisma/client/runtime/library.d.ts'
```

Execute o script de setup que já está configurado para resolver este problema:

```bash
# Executar o script de setup
pnpm run setup
```

Este script irá:

1. Criar o diretório de geração do Prisma se não existir
2. Ajustar as permissões corretamente
3. Instalar as dependências
4. Gerar o Prisma Client

Se preferir resolver manualmente:

```bash
# Criar diretório se não existir
mkdir -p src/generated/prisma

# Ajustar permissões
chmod -R 755 src/generated/prisma

# Gerar Prisma Client novamente
pnpm prisma:generate
```

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique a documentação acima
2. Consulte os logs em `logs/`
3. Abra uma issue no repositório
4. Entre em contato: <amjr.box@gmail.com>

---

**Desenvolvido com ❤️ por Junior Martins**

*Sistema criado para o teste técnico da JusCash - Gerenciamento de Publicações DJE/SP*
