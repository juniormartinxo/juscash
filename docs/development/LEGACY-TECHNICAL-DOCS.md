# 🔧 Documentação Técnica - JusCash

> Sistema de Gerenciamento de Publicações do Diário da Justiça Eletrônico (DJE-SP)  
> Documentação Técnica Completa para Desenvolvedores e Administradores

---

## 📖 Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Tecnologias Utilizadas](#tecnologias-utilizadas)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [API REST](#api-rest)
5. [Banco de Dados](#banco-de-dados)
6. [Sistema de Scraping](#sistema-de-scraping)
7. [Frontend React](#frontend-react)
8. [Infraestrutura e DevOps](#infraestrutura-e-devops)
9. [Segurança](#segurança)
10. [Monitoramento e Logs](#monitoramento-e-logs)
11. [Instalação e Configuração](#instalação-e-configuração)
12. [Guias de Desenvolvimento](#guias-de-desenvolvimento)

---

## 🏗️ Visão Geral da Arquitetura

### Arquitetura do Sistema

O JusCash foi desenvolvido seguindo os princípios de **Clean Architecture** (Arquitetura Hexagonal), garantindo:

- **Separação clara de responsabilidades**
- **Independência de frameworks**
- **Testabilidade**
- **Flexibilidade para mudanças**
- **Escalabilidade**

```mermaid
graph TB
    subgraph "Frontend"
        UI[React + TypeScript]
        UI --> Components[Componentes UI]
        UI --> Hooks[Custom Hooks]
        UI --> Services[API Services]
    end

    subgraph "API Backend"
        Controllers[Controllers]
        UseCases[Use Cases]
        Domain[Domain Layer]
        Repositories[Repositories]
        Infrastructure[Infrastructure]
    end

    subgraph "Scraper Python"
        ScrapingOrchestrator[Scraping Orchestrator]
        WebScraper[Web Scraper]
        DataValidator[Data Validator]
        FileManager[File Manager]
    end

    subgraph "Banco de Dados"
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis Cache)]
    end

    UI --> Controllers
    Controllers --> UseCases
    UseCases --> Domain
    UseCases --> Repositories
    Repositories --> Infrastructure
    Infrastructure --> PostgreSQL

    ScrapingOrchestrator --> WebScraper
    ScrapingOrchestrator --> DataValidator
    DataValidator --> FileManager
    ScrapingOrchestrator --> PostgreSQL
    
    Infrastructure --> Redis
    ScrapingOrchestrator --> Redis
```

### Princípios Arquiteturais

#### 1. Clean Architecture (Backend)

- **Domain Layer**: Entidades, regras de negócio e contratos
- **Application Layer**: Casos de uso e orquestração
- **Infrastructure Layer**: Implementações técnicas
- **Web Layer**: Controllers, middlewares e rotas

#### 2. Component-Based Architecture (Frontend)

- **Componentes Reutilizáveis**: UI components isolados
- **Custom Hooks**: Lógica compartilhada
- **Context API**: Gerenciamento de estado global
- **Service Layer**: Comunicação com API

#### 3. Hexagonal Architecture (Scraper)

- **Portas e Adaptadores**: Interfaces bem definidas
- **Domínio Isolado**: Lógica de negócio independente
- **Adaptadores**: Implementações específicas

---

## 💻 Tecnologias Utilizadas

### Backend (Node.js)

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Node.js** | 20+ | Runtime JavaScript |
| **Express.js** | 5.x | Framework web |
| **TypeScript** | 5.x | Tipagem estática |
| **Prisma ORM** | 5.x | Object-Relational Mapping |
| **JWT** | 9.x | Autenticação |
| **Zod** | 3.x | Validação de schemas |
| **Winston** | 3.x | Sistema de logs |
| **bcrypt** | 5.x | Hash de senhas |
| **Helmet** | 7.x | Segurança HTTP |
| **CORS** | 2.x | Cross-Origin Resource Sharing |

### Frontend (React)

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **React** | 18.x | Framework UI |
| **TypeScript** | 5.x | Tipagem estática |
| **Vite** | 5.x | Build tool |
| **Tailwind CSS** | 3.x | Framework CSS |
| **Lucide React** | 0.x | Ícones |
| **React Hook Form** | 7.x | Gerenciamento de formulários |
| **React DnD** | 16.x | Drag and Drop |
| **Axios** | 1.x | Cliente HTTP |

### Scraper (Python)

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Python** | 3.11+ | Runtime |
| **Playwright** | 1.x | Automação web |
| **SQLAlchemy** | 2.x | ORM Python |
| **Pydantic** | 2.x | Validação de dados |
| **APScheduler** | 3.x | Agendamento de tarefas |
| **Loguru** | 0.x | Sistema de logs |
| **Redis** | 4.x | Cache e filas |
| **Requests** | 2.x | Cliente HTTP |

### Banco de Dados

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **PostgreSQL** | 16+ | Banco relacional |
| **Redis** | 7+ | Cache e sessões |

### DevOps e Infraestrutura

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Docker** | 24+ | Containerização |
| **Docker Compose** | 2.x | Orquestração local |
| **Nginx** | 1.x | Proxy reverso |
| **Git** | 2.x | Controle de versão |

---

## 📁 Estrutura do Projeto

### Estrutura Geral

```
juscash/
├── backend/
│   ├── api/                    # API REST Node.js
│   └── scraper/               # Sistema de scraping Python
├── frontend/                  # Interface React
├── database/                  # Configurações de banco
├── docs/                      # Documentação
├── scripts/                   # Scripts utilitários
├── docker-compose.yml         # Orquestração Docker
└── README.md                  # Documentação principal
```

### Backend API (Node.js)

```
backend/api/
├── src/
│   ├── domain/               # Camada de domínio
│   │   ├── entities/         # Entidades do negócio
│   │   ├── repositories/     # Contratos dos repositórios
│   │   └── services/         # Serviços de domínio
│   ├── application/          # Camada de aplicação
│   │   └── usecases/         # Casos de uso
│   ├── infrastructure/       # Camada de infraestrutura
│   │   ├── database/         # Adaptadores Prisma
│   │   ├── security/         # JWT e autenticação
│   │   └── web/             # Controllers e rotas
│   └── shared/              # Código compartilhado
│       ├── config/          # Configurações
│       ├── utils/           # Utilitários
│       └── validation/      # Schemas Zod
├── prisma/                  # Schema e migrações
├── tests/                   # Testes automatizados
└── package.json             # Dependências Node.js
```

### Scraper Python

```
backend/scraper/
├── src/
│   ├── domain/              # Camada de domínio
│   │   ├── entities/        # Entidades do scraping
│   │   ├── ports/           # Interfaces/contratos
│   │   └── services/        # Serviços de domínio
│   ├── application/         # Camada de aplicação
│   │   ├── services/        # Orquestração
│   │   └── usecases/        # Casos de uso
│   ├── infrastructure/      # Camada de infraestrutura
│   │   ├── web/            # Adaptadores web
│   │   ├── database/       # Adaptadores banco
│   │   ├── files/          # Gerenciamento arquivos
│   │   └── monitoring/     # Monitoramento
│   └── main.py             # Ponto de entrada
├── requirements.txt         # Dependências Python
└── config/                 # Configurações
```

### Frontend React

```
frontend/
├── src/
│   ├── components/          # Componentes UI
│   │   ├── ui/             # Componentes base
│   │   ├── KanbanBoard.tsx # Board principal
│   │   └── ...
│   ├── pages/              # Páginas da aplicação
│   ├── services/           # Serviços API
│   ├── hooks/              # Custom hooks
│   ├── contexts/           # Contextos React
│   ├── types/              # Definições TypeScript
│   └── lib/                # Utilitários
├── public/                 # Arquivos estáticos
└── package.json            # Dependências React
```

---

## 🌐 API REST

### Documentação Swagger/OpenAPI

A API possui documentação completa Swagger disponível em:

- **Local**: `${API_BASE_URL}-docs`
- **Produção**: `https://[seu-dominio]/api-docs`

### Endpoints Principais

#### Autenticação

##### POST `/api/auth/register`

Registra um novo usuário no sistema.

**Request Body:**

```json
{
  "name": "João Silva",
  "email": "joao@exemplo.com",
  "password": "MinhaSenh@123"
}
```

**Response (201):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "cm123456789",
      "name": "João Silva",
      "email": "joao@exemplo.com",
      "isActive": true,
      "createdAt": "2024-01-15T10:30:00.000Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  },
  "message": "Usuário registrado com sucesso"
}
```

##### POST `/api/auth/login`

Autentica um usuário existente.

**Request Body:**

```json
{
  "email": "joao@exemplo.com",
  "password": "MinhaSenh@123"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "cm123456789",
      "name": "João Silva",
      "email": "joao@exemplo.com",
      "isActive": true
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  },
  "message": "Login realizado com sucesso"
}
```

##### POST `/api/auth/refresh`

Renova o token de acesso usando o refresh token.

**Request Body:**

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

##### POST `/api/auth/logout`

Realiza logout invalidando o refresh token.

#### Publicações

##### GET `/api/publications`

Lista publicações com paginação e filtros.

**Query Parameters:**

- `page` (number): Página (padrão: 1)
- `limit` (number): Itens por página (padrão: 20, máx: 100)
- `status` (enum): Filtro por status
- `search` (string): Busca por texto
- `processNumber` (string): Filtro por número do processo
- `startDate` (date): Data inicial
- `endDate` (date): Data final
- `authors` (string): Filtro por autores
- `defendant` (string): Filtro por réu

**Response (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "cm123456789",
      "processNumber": "1234567-89.2023.4.03.6100",
      "publicationDate": "2023-12-15",
      "availabilityDate": "2023-12-16",
      "authors": ["João Silva", "Maria Santos"],
      "defendant": "Instituto Nacional do Seguro Social - INSS",
      "grossValue": 50000,
      "netValue": 45000,
      "interestValue": 5000,
      "attorneyFees": 10000,
      "content": "Conteúdo da publicação...",
      "status": "NOVA",
      "createdAt": "2023-12-16T08:00:00.000Z",
      "updatedAt": "2023-12-16T08:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false
  }
}
```

##### GET `/api/publications/:id`

Busca uma publicação específica por ID.

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "cm123456789",
    "processNumber": "1234567-89.2023.4.03.6100",
    "publicationDate": "2023-12-15",
    "availabilityDate": "2023-12-16",
    "authors": ["João Silva", "Maria Santos"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": {
      "author": ["Dr. João Advogado - OAB/SP 123456"],
      "defendant": ["Dr. Maria Procuradora - OAB/SP 654321"]
    },
    "grossValue": 50000,
    "netValue": 45000,
    "interestValue": 5000,
    "attorneyFees": 10000,
    "content": "Conteúdo completo da publicação...",
    "status": "NOVA",
    "scrapingSource": "DJE-SP",
    "caderno": "3",
    "instancia": "1",
    "local": "Capital",
    "parte": "1",
    "extractionMetadata": {
      "extractedAt": "2023-12-16T08:00:00.000Z",
      "source": "automated_scraping",
      "confidence": 0.95
    },
    "createdAt": "2023-12-16T08:00:00.000Z",
    "updatedAt": "2023-12-16T08:00:00.000Z"
  }
}
```

##### PUT `/api/publications/:id/status`

Atualiza o status de uma publicação.

**Request Body:**

```json
{
  "status": "LIDA",
  "notes": "Publicação analisada e aprovada para próxima etapa"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "cm123456789",
    "status": "LIDA",
    "updatedAt": "2023-12-16T14:30:00.000Z"
  },
  "message": "Status atualizado com sucesso"
}
```

#### Métricas e Saúde

##### GET `/api/health`

Verifica a saúde do sistema.

**Response (200):**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2023-12-16T14:30:00.000Z",
    "uptime": 86400,
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "redis": "connected"
    },
    "metrics": {
      "totalPublications": 1500,
      "todayPublications": 25,
      "activeUsers": 5
    }
  }
}
```

##### GET `/api/metrics`

Retorna métricas detalhadas do sistema.

### Middlewares

#### 1. Autenticação (authMiddleware)

- Valida JWT tokens
- Verifica se usuário está ativo
- Adiciona dados do usuário ao request

#### 2. Rate Limiting (rateLimitMiddleware)

- Limita requisições por IP/usuário
- Configurável por endpoint
- Padrão: 100 req/15min

#### 3. Validação (validationMiddleware)

- Valida request body com schemas Zod
- Sanitiza dados de entrada
- Retorna erros formatados

#### 4. Logging (loggingMiddleware)

- Registra todas as requisições
- Inclui timing e status codes
- Logs estruturados com Winston

#### 5. Segurança (securityMiddleware)

- Headers de segurança (Helmet)
- Proteção CORS
- Sanitização XSS

### Tratamento de Erros

```typescript
// Estrutura padrão de erro
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos fornecidos",
    "details": [
      {
        "field": "email",
        "message": "Email deve ser válido"
      }
    ]
  },
  "timestamp": "2023-12-16T14:30:00.000Z",
  "path": "/api/auth/register"
}
```

#### Códigos de Erro HTTP

| Código | Descrição | Uso |
|--------|-----------|-----|
| 400 | Bad Request | Dados inválidos ou malformados |
| 401 | Unauthorized | Token inválido ou expirado |
| 403 | Forbidden | Usuário sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Conflito de dados (ex: email já existe) |
| 422 | Unprocessable Entity | Dados válidos mas regra de negócio violada |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Erro interno do servidor |

---

## 🗄️ Banco de Dados

### Schema do PostgreSQL

#### Diagrama de Relacionamentos

```mermaid
erDiagram
    User ||--o{ UserRefreshToken : has
    User ||--o{ UserSession : has
    User ||--o{ AuthLog : generates
    User ||--o{ PublicationLog : creates

    Publication ||--o{ PublicationLog : has
    Publication }o--|| ScrapingExecution : belongs_to

    ScrapingExecution ||--o{ Publication : contains
    ScrapingExecution ||--o{ ScrapingLog : generates
    ScrapingExecution ||--o{ ScrapingConfiguration : uses
```

#### Tabelas Principais

##### users

Tabela central de usuários do sistema.

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,              -- CUID2
    name VARCHAR NOT NULL,               -- Nome completo
    email VARCHAR UNIQUE NOT NULL,       -- Email único
    password_hash VARCHAR NOT NULL,      -- Hash bcrypt da senha
    last_password_change TIMESTAMP,     -- Última alteração de senha
    is_password_temporary BOOLEAN DEFAULT true, -- Senha temporária
    is_active BOOLEAN DEFAULT true,     -- Usuário ativo
    created_at TIMESTAMP DEFAULT NOW(), -- Data de criação
    updated_at TIMESTAMP DEFAULT NOW(), -- Última atualização
    deactivated_at TIMESTAMP           -- Data de desativação
);

-- Índices para performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_active ON users(is_active, created_at);
```

##### publications

Tabela principal de publicações do DJE.

```sql
CREATE TABLE publications (
    id VARCHAR PRIMARY KEY,              -- CUID2
    process_number VARCHAR UNIQUE NOT NULL, -- Número CNJ do processo
    publication_date DATE,               -- Data oficial da publicação
    availability_date DATE,              -- Data de disponibilização
    authors TEXT[] NOT NULL,             -- Array de autores
    defendant VARCHAR DEFAULT 'Instituto Nacional do Seguro Social - INSS',
    lawyers JSONB,                       -- Advogados estruturados
    gross_value BIGINT,                  -- Valor bruto em centavos
    net_value BIGINT,                    -- Valor líquido em centavos
    interest_value BIGINT,               -- Valor de juros em centavos
    attorney_fees BIGINT,                -- Honorários em centavos
    content TEXT NOT NULL,               -- Conteúdo completo
    status publication_status DEFAULT 'NOVA', -- Status do workflow
    created_at TIMESTAMP DEFAULT NOW(), -- Data de criação
    updated_at TIMESTAMP DEFAULT NOW(), -- Última atualização
    scraping_source VARCHAR DEFAULT 'DJE-SP', -- Fonte do scraping
    caderno VARCHAR DEFAULT '3',         -- Caderno do DJE
    instancia VARCHAR DEFAULT '1',       -- Instância judicial
    local VARCHAR DEFAULT 'Capital',     -- Local da publicação
    parte VARCHAR DEFAULT '1',           -- Parte do processo
    extraction_metadata JSONB,          -- Metadados da extração
    scraping_execution_id VARCHAR       -- FK para execução do scraping
);

-- Índices otimizados
CREATE INDEX idx_publications_process_number ON publications(process_number);
CREATE INDEX idx_publications_status ON publications(status);
CREATE INDEX idx_publications_availability_date ON publications(availability_date);
CREATE INDEX idx_publications_created_at ON publications(created_at);
CREATE INDEX idx_publications_status_date ON publications(status, availability_date);
CREATE INDEX idx_publications_source_caderno ON publications(scraping_source, caderno);
CREATE INDEX idx_publications_defendant ON publications(defendant);

-- Índice para busca textual
CREATE INDEX idx_publications_content_search ON publications 
USING gin(to_tsvector('portuguese', content));

-- Índice para busca em autores
CREATE INDEX idx_publications_authors ON publications USING gin(authors);
```

##### scraping_executions

Registra execuções do sistema de scraping.

```sql
CREATE TABLE scraping_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_type scraping_execution_type NOT NULL, -- SCHEDULED, MANUAL, TEST
    status scraping_execution_status DEFAULT 'RUNNING', -- RUNNING, SUCCESS, FAILED
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    execution_time_seconds INTEGER,
    publications_found INTEGER DEFAULT 0,
    publications_new INTEGER DEFAULT 0,
    publications_duplicated INTEGER DEFAULT 0,
    publications_failed INTEGER DEFAULT 0,
    publications_saved INTEGER DEFAULT 0,
    criteria_used JSONB,                 -- Critérios utilizados
    max_publications_limit INTEGER,     -- Limite máximo configurado
    scraper_version VARCHAR,             -- Versão do scraper
    browser_user_agent VARCHAR,         -- User agent utilizado
    error_details JSONB                  -- Detalhes de erros
);

-- Índices para relatórios
CREATE INDEX idx_scraping_executions_type_date ON scraping_executions(execution_type, started_at);
CREATE INDEX idx_scraping_executions_status_date ON scraping_executions(status, started_at);
```

##### publication_logs

Auditoria de ações nas publicações.

```sql
CREATE TABLE publication_logs (
    id VARCHAR PRIMARY KEY,
    publication_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    action publication_log_action NOT NULL, -- VIEW, STATUS_CHANGE, EDIT, etc.
    old_data JSONB,                      -- Estado anterior
    new_data JSONB,                      -- Estado novo
    notes TEXT,                          -- Observações
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (publication_id) REFERENCES publications(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Índices para auditoria
CREATE INDEX idx_publication_logs_publication_date ON publication_logs(publication_id, created_at);
CREATE INDEX idx_publication_logs_user_date ON publication_logs(user_id, created_at);
CREATE INDEX idx_publication_logs_action_date ON publication_logs(action, created_at);
```

#### Enums Principais

```sql
-- Status das publicações
CREATE TYPE publication_status AS ENUM (
    'NOVA',
    'LIDA', 
    'ENVIADA_PARA_ADV',
    'CONCLUIDA'
);

-- Tipos de execução do scraping
CREATE TYPE scraping_execution_type AS ENUM (
    'SCHEDULED',
    'MANUAL',
    'TEST'
);

-- Status da execução do scraping
CREATE TYPE scraping_execution_status AS ENUM (
    'RUNNING',
    'SUCCESS',
    'FAILED',
    'CANCELLED'
);

-- Ações de log das publicações
CREATE TYPE publication_log_action AS ENUM (
    'VIEW',
    'STATUS_CHANGE',
    'EDIT',
    'CREATE',
    'DELETE'
);
```

### Estratégias de Performance

#### 1. Indexação Inteligente

- Índices compostos para consultas frequentes
- Índices GIN para arrays e busca textual
- Índices parciais para dados ativos

#### 2. Particionamento

```sql
-- Particionamento por data para publicações antigas
CREATE TABLE publications_2023 PARTITION OF publications
FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE publications_2024 PARTITION OF publications
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

#### 3. Otimizações de Query

- LIMIT com OFFSET otimizado para paginação
- Cursor-based pagination para grandes datasets
- Query planning para consultas complexas

#### 4. Connection Pooling

```typescript
// Configuração Prisma
{
  datasource: {
    provider: "postgresql",
    url: env("DATABASE_URL")
  },
  generator: {
    provider: "prisma-client-js",
    output: "../src/generated/prisma"
  }
}

// Pool de conexões otimizado
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL
    }
  },
  log: ['query', 'info', 'warn', 'error']
})
```

### Backup e Recuperação

#### 1. Backup Automático

```bash
#!/bin/bash
# Script de backup diário

DB_NAME="juscash_db"
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup completo
pg_dump -h localhost -U postgres $DB_NAME > $BACKUP_DIR/full_backup_$DATE.sql

# Compactação
gzip $BACKUP_DIR/full_backup_$DATE.sql

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "full_backup_*.sql.gz" -mtime +30 -delete
```

#### 2. Point-in-Time Recovery

- WAL archiving habilitado
- Backup incremental contínuo
- Restore para momento específico

#### 3. Replicação

- Streaming replication para read replicas
- Failover automático configurado
- Monitoramento de lag de replicação

---

# 🔧 Documentação Técnica - JusCash (Parte 2)

## 🕷️ Sistema de Scraping

### Arquitetura do Scraper

O sistema de scraping é desenvolvido em Python seguindo os princípios de **Arquitetura Hexagonal**, garantindo separação clara entre lógica de negócio e implementações técnicas.

```mermaid
graph TB
    subgraph "Application Layer"
        Orchestrator[Scraping Orchestrator]
        UseCases[Use Cases]
    end
    
    subgraph "Domain Layer"
        Entities[Entities]
        Services[Domain Services]
        Ports[Ports/Interfaces]
    end
    
    subgraph "Infrastructure Layer"
        WebAdapter[Web Scraper Adapter]
        DBAdapter[Database Adapter]
        FileAdapter[File Adapter]
        MonitoringAdapter[Monitoring Adapter]
    end
    
    subgraph "External Systems"
        DJE[DJE Website]
        PostgreSQL[(PostgreSQL)]
        Files[JSON Files]
        API[JusCash API]
    end
    
    Orchestrator --> UseCases
    UseCases --> Services
    Services --> Entities
    UseCases --> Ports
    
    Ports --> WebAdapter
    Ports --> DBAdapter
    Ports --> FileAdapter
    Ports --> MonitoringAdapter
    
    WebAdapter --> DJE
    DBAdapter --> PostgreSQL
    FileAdapter --> Files
    MonitoringAdapter --> API
```

### Componentes Principais

#### 1. Scraping Orchestrator

**Localização**: `backend/scraper/src/application/services/scraping_orchestrator.py`

Responsável por orquestrar todo o processo de scraping:

```python
class ScrapingOrchestrator:
    def __init__(self, web_scraper, data_validator, file_saver, db_repository):
        self.web_scraper = web_scraper
        self.data_validator = data_validator
        self.file_saver = file_saver
        self.db_repository = db_repository
    
    async def execute_scraping(self, criteria: ScrapingCriteria) -> ScrapingResult:
        """
        Executa o processo completo de scraping
        """
        execution = await self.start_execution(criteria)
        
        try:
            # 1. Extrair publicações do DJE
            raw_publications = await self.web_scraper.extract_publications(criteria)
            
            # 2. Validar e processar dados
            validated_publications = []
            for raw_pub in raw_publications:
                if self.data_validator.is_valid(raw_pub):
                    publication = self.data_validator.process(raw_pub)
                    validated_publications.append(publication)
            
            # 3. Salvar em arquivos de backup
            await self.file_saver.save_publications(validated_publications)
            
            # 4. Persistir no banco de dados
            saved_count = await self.db_repository.save_publications(validated_publications)
            
            # 5. Finalizar execução
            await self.complete_execution(execution, saved_count)
            
            return ScrapingResult(
                success=True,
                publications_found=len(raw_publications),
                publications_saved=saved_count
            )
            
        except Exception as e:
            await self.fail_execution(execution, str(e))
            raise
```

#### 2. Web Scraper Adapter

**Localização**: `backend/scraper/src/infrastructure/web/dje_scraper_adapter.py`

Implementa a extração de dados do DJE usando Playwright:

```python
class DJEScraperAdapter:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def extract_publications(self, criteria: ScrapingCriteria) -> List[RawPublication]:
        """
        Extrai publicações do DJE baseado nos critérios
        """
        await self.initialize_browser()
        
        try:
            # 1. Navegar para o DJE
            await self.navigate_to_dje()
            
            # 2. Preencher formulário de busca
            await self.fill_search_form(criteria)
            
            # 3. Submeter busca
            await self.submit_search()
            
            # 4. Extrair resultados
            publications = await self.extract_results()
            
            return publications
            
        finally:
            await self.cleanup_browser()
    
    async def navigate_to_dje(self):
        """Navega para a página do DJE"""
        url = "https://dje.tjsp.jus.br/cdje/consultaSimples.do"
        await self.page.goto(url, wait_until="networkidle")
        
    async def fill_search_form(self, criteria: ScrapingCriteria):
        """Preenche o formulário de busca"""
        # Selecionar caderno
        await self.page.select_option("#caderno", criteria.caderno)
        
        # Selecionar instância
        await self.page.select_option("#instancia", criteria.instancia)
        
        # Data de publicação
        await self.page.fill("#dtPublicacao", criteria.publication_date.strftime("%d/%m/%Y"))
        
        # Termos de busca (se especificados)
        if criteria.search_terms:
            await self.page.fill("#palavrasChave", " ".join(criteria.search_terms))
    
    async def extract_results(self) -> List[RawPublication]:
        """Extrai as publicações dos resultados"""
        publications = []
        
        # Aguardar carregamento dos resultados
        await self.page.wait_for_selector(".resultadoLista")
        
        # Extrair cada publicação
        publication_elements = await self.page.query_selector_all(".publicacao")
        
        for element in publication_elements:
            try:
                publication_data = await self.extract_publication_data(element)
                publications.append(RawPublication(**publication_data))
            except Exception as e:
                logger.warning(f"Erro ao extrair publicação: {e}")
                continue
        
        return publications
```

#### 3. Content Parser

**Localização**: `backend/scraper/src/infrastructure/web/enhanced_content_parser.py`

Processa o conteúdo das publicações extraindo informações estruturadas:

```python
class EnhancedContentParser:
    def __init__(self):
        self.value_patterns = {
            'gross_value': r'valor\s+bruto[:\s]+r\$\s*([\d.,]+)',
            'net_value': r'valor\s+líquido[:\s]+r\$\s*([\d.,]+)',
            'attorney_fees': r'honorários[:\s]+r\$\s*([\d.,]+)',
            'interest_value': r'juros[:\s]+r\$\s*([\d.,]+)'
        }
        
    def parse_publication(self, raw_content: str) -> ParsedPublication:
        """
        Processa o conteúdo bruto da publicação
        """
        return ParsedPublication(
            process_number=self.extract_process_number(raw_content),
            authors=self.extract_authors(raw_content),
            defendant=self.extract_defendant(raw_content),
            lawyers=self.extract_lawyers(raw_content),
            values=self.extract_values(raw_content),
            content=self.clean_content(raw_content)
        )
    
    def extract_process_number(self, content: str) -> Optional[str]:
        """Extrai o número do processo"""
        pattern = r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})'
        match = re.search(pattern, content)
        return match.group(1) if match else None
    
    def extract_values(self, content: str) -> Dict[str, int]:
        """Extrai valores monetários convertendo para centavos"""
        values = {}
        
        for value_type, pattern in self.value_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    # Converter para centavos
                    value_cents = int(float(value_str) * 100)
                    values[value_type] = value_cents
                except ValueError:
                    continue
        
        return values
```

### Configuração e Agendamento

#### 1. Configurações Dinâmicas

**Localização**: `backend/scraper/src/infrastructure/config/settings.py`

```python
class ScrapingSettings:
    # Configurações do DJE
    DJE_BASE_URL = "https://dje.tjsp.jus.br"
    DJE_TIMEOUT = 30000  # 30 segundos
    
    # Configurações do navegador
    BROWSER_HEADLESS = True
    BROWSER_USER_AGENT = "Mozilla/5.0 (compatible; JusCashBot/1.0)"
    
    # Configurações de retry
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # segundos
    
    # Filtros automáticos
    REQUIRED_TERMS = ["Instituto Nacional", "INSS", "Seguro Social"]
    EXCLUDED_TERMS = ["arquivado", "extinto"]
    
    # Limites de segurança
    MAX_PUBLICATIONS_PER_RUN = 1000
    MAX_EXECUTION_TIME = 3600  # 1 hora
    
    @classmethod
    def load_from_env(cls):
        """Carrega configurações das variáveis de ambiente"""
        return cls(
            dje_caderno=os.getenv('DJE_CADERNO', '3'),
            dje_instancia=os.getenv('DJE_INSTANCIA', '1'),
            browser_headless=os.getenv('SCRAPING_HEADLESS', 'true').lower() == 'true',
            required_terms=os.getenv('SCRAPING_REQUIRED_TERMS', '').split(',')
        )
```

#### 2. Agendamento Automático

**Localização**: `backend/scraper/src/infrastructure/scheduler/scheduler_adapter.py`

```python
class SchedulerAdapter:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start_daily_scraping(self):
        """Inicia agendamento diário de scraping"""
        self.scheduler.add_job(
            func=self.execute_daily_scraping,
            trigger="cron",
            hour=8,  # 8h da manhã
            minute=0,
            timezone="America/Sao_Paulo",
            id="daily_scraping",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Agendamento diário de scraping iniciado")
    
    async def execute_daily_scraping(self):
        """Executa scraping diário automaticamente"""
        try:
            criteria = ScrapingCriteria(
                publication_date=datetime.now().date() - timedelta(days=1),  # Dia anterior
                caderno="3",
                instancia="1",
                search_terms=settings.REQUIRED_TERMS
            )
            
            orchestrator = get_scraping_orchestrator()
            result = await orchestrator.execute_scraping(criteria)
            
            logger.info(f"Scraping diário concluído: {result.publications_saved} publicações salvas")
            
        except Exception as e:
            logger.error(f"Erro no scraping diário: {e}")
            await self.send_error_alert(e)
```

### Monitoramento e Alertas

#### 1. Sistema de Monitoramento

**Localização**: `backend/scraper/src/infrastructure/monitoring/monitoring_service.py`

```python
class MonitoringService:
    def __init__(self, api_client):
        self.api_client = api_client
        
    async def track_execution(self, execution_id: str, metrics: Dict):
        """Registra métricas de execução"""
        await self.api_client.post("/api/scraping/executions/{execution_id}/metrics", metrics)
        
    async def send_health_check(self):
        """Envia status de saúde do scraper"""
        health_data = {
            "status": "healthy",
            "last_execution": self.get_last_execution_time(),
            "system_metrics": self.get_system_metrics(),
            "pending_tasks": self.get_pending_tasks_count()
        }
        
        await self.api_client.post("/api/scraping/health", health_data)
    
    def get_system_metrics(self) -> Dict:
        """Coleta métricas do sistema"""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": time.time() - psutil.boot_time()
        }
```

---

## ⚛️ Frontend React

### Arquitetura do Frontend

O frontend é desenvolvido em React com TypeScript, seguindo padrões modernos de desenvolvimento:

```mermaid
graph TB
    subgraph "Components Layer"
        Pages[Pages]
        Components[UI Components]
        Layout[Layout Components]
    end
    
    subgraph "State Management"
        Context[React Context]
        Hooks[Custom Hooks]
        LocalState[Local State]
    end
    
    subgraph "Services Layer"
        API[API Service]
        Auth[Auth Service]
        Storage[Storage Service]
    end
    
    subgraph "Utils Layer"
        Validation[Validation]
        Formatting[Formatting]
        Constants[Constants]
    end
    
    Pages --> Components
    Pages --> Context
    Components --> Hooks
    Context --> API
    Hooks --> API
    API --> Auth
    Components --> Validation
    Components --> Formatting
```

### Componentes Principais

#### 1. KanbanBoard Component

**Localização**: `frontend/src/components/KanbanBoard.tsx`

Componente central da aplicação que implementa o board Kanban:

```typescript
interface KanbanBoardProps {
  filters: SearchFilters
}

export function KanbanBoard({ filters }: KanbanBoardProps) {
  const [columns, setColumns] = useState<Map<PublicationStatus, KanbanColumn>>(new Map())
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState<Set<PublicationStatus>>(new Set())
  
  // Configuração das colunas
  const COLUMN_CONFIG: Record<PublicationStatus, { title: React.ReactNode; color: string }> = {
    NOVA: { title: 'Nova Publicação', color: 'bg-blue-50 border-blue-200' },
    LIDA: { title: 'Publicação Lida', color: 'bg-yellow-50 border-yellow-200' },
    ENVIADA_PARA_ADV: { title: 'Enviar para Advogado', color: 'bg-orange-50 border-orange-200' },
    CONCLUIDA: { title: 'Concluído', color: 'bg-green-50 border-green-200' }
  }
  
  // Carregamento de dados com paginação
  const loadPublications = useCallback(async (
    status: PublicationStatus,
    page: number = 1,
    reset: boolean = false
  ) => {
    try {
      const response = await apiService.getPublications(page, 30, {
        ...filters,
        status
      })
      
      setColumns(prev => {
        const newColumns = new Map(prev)
        const existingColumn = newColumns.get(status)
        const existingPublications = reset ? [] : existingColumn?.publications || []
        
        newColumns.set(status, {
          id: status,
          title: COLUMN_CONFIG[status].title,
          publications: [...existingPublications, ...response.data],
          count: response.total || 0
        })
        
        return newColumns
      })
      
    } catch (error) {
      toast({
        title: "Erro ao carregar publicações",
        description: `Erro ao carregar ${status}`,
        variant: "destructive"
      })
    }
  }, [filters, toast])
  
  // Drag and Drop
  const onDragEnd = useCallback(async (result: DropResult) => {
    if (!result.destination) return
    
    const sourceStatus = result.source.droppableId as PublicationStatus
    const destStatus = result.destination.droppableId as PublicationStatus
    
    if (sourceStatus === destStatus) return
    
    // Validar movimento
    if (!isValidMove(sourceStatus, destStatus)) {
      toast({
        title: "Movimento não permitido",
        description: "Este movimento não é permitido pelas regras do sistema",
        variant: "destructive"
      })
      return
    }
    
    try {
      // Atualizar no servidor
      await apiService.updatePublicationStatus(publicationId, destStatus)
      
      // Atualizar estado local
      updateColumnState(publicationId, sourceStatus, destStatus)
      
    } catch (error) {
      toast({
        title: "Erro ao mover publicação",
        description: "Não foi possível alterar o status da publicação",
        variant: "destructive"
      })
    }
  }, [])
  
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="flex gap-6 h-full overflow-x-auto">
        {columnOrder.map(status => (
          <KanbanColumn
            key={status}
            status={status}
            column={columns.get(status)}
            loading={loading || loadingMore.has(status)}
            onLoadMore={() => loadMoreItems(status)}
            onPublicationClick={setSelectedPublication}
          />
        ))}
      </div>
      
      {selectedPublication && (
        <PublicationModal
          publication={selectedPublication}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </DragDropContext>
  )
}
```

#### 2. SearchFilters Component

**Localização**: `frontend/src/components/SearchFilters.tsx`

Implementa o sistema de filtros avançados:

```typescript
interface SearchFiltersProps {
  onFiltersChange: (filters: SearchFilters) => void
  initialFilters?: SearchFilters
}

export function SearchFilters({ onFiltersChange, initialFilters }: SearchFiltersProps) {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters || {})
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFiltersChange(newFilters)
  }
  
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      {/* Filtros Básicos */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Input
          placeholder="Buscar por texto..."
          value={filters.search || ''}
          onChange={(e) => handleFilterChange('search', e.target.value)}
        />
        
        <Input
          placeholder="Número do processo"
          value={filters.processNumber || ''}
          onChange={(e) => handleFilterChange('processNumber', e.target.value)}
        />
        
        <Input
          type="date"
          placeholder="Data inicial"
          value={filters.startDate || ''}
          onChange={(e) => handleFilterChange('startDate', e.target.value)}
        />
        
        <Input
          type="date"
          placeholder="Data final"
          value={filters.endDate || ''}
          onChange={(e) => handleFilterChange('endDate', e.target.value)}
        />
      </div>
      
      {/* Filtros Avançados */}
      {showAdvanced && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            placeholder="Autores"
            value={filters.authors || ''}
            onChange={(e) => handleFilterChange('authors', e.target.value)}
          />
          
          <Input
            placeholder="Réu"
            value={filters.defendant || ''}
            onChange={(e) => handleFilterChange('defendant', e.target.value)}
          />
          
          <Select
            value={filters.status}
            onValueChange={(value) => handleFilterChange('status', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="NOVA">Nova</SelectItem>
              <SelectItem value="LIDA">Lida</SelectItem>
              <SelectItem value="ENVIADA_PARA_ADV">Enviada</SelectItem>
              <SelectItem value="CONCLUIDA">Concluída</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}
      
      {/* Controles */}
      <div className="mt-4 flex justify-between items-center">
        <Button
          variant="outline"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? 'Ocultar' : 'Mostrar'} Filtros Avançados
        </Button>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setFilters({})
              onFiltersChange({})
            }}
          >
            Limpar Filtros
          </Button>
          
          <Button onClick={() => onFiltersChange(filters)}>
            Aplicar Filtros
          </Button>
        </div>
      </div>
    </div>
  )
}
```

### Serviços de API

#### 1. API Service

**Localização**: `frontend/src/services/api.ts`

Centraliza todas as chamadas para a API:

```typescript
class ApiService {
  private baseURL: string
  private axios: AxiosInstance
  
  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:3001'
    
    this.axios = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    this.setupInterceptors()
  }
  
  private setupInterceptors() {
    // Request interceptor - adiciona token de autenticação
    this.axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('accessToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    
    // Response interceptor - trata refresh de token
    this.axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await this.refreshToken()
          // Retry request original
          return this.axios.request(error.config)
        }
        return Promise.reject(error)
      }
    )
  }
  
  // Autenticação
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.axios.post('/api/auth/login', { email, password })
    this.setTokens(response.data.data.tokens)
    return response.data
  }
  
  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await this.axios.post('/api/auth/register', userData)
    this.setTokens(response.data.data.tokens)
    return response.data
  }
  
  async refreshToken(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken')
    if (!refreshToken) {
      this.logout()
      return
    }
    
    try {
      const response = await this.axios.post('/api/auth/refresh', { refreshToken })
      this.setTokens(response.data.data.tokens)
    } catch (error) {
      this.logout()
      throw error
    }
  }
  
  // Publicações
  async getPublications(
    page: number = 1,
    limit: number = 20,
    filters: SearchFilters = {}
  ): Promise<PaginatedResponse<Publication>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v != null && v !== '')
      )
    })
    
    const response = await this.axios.get(`/api/publications?${params}`)
    return response.data
  }
  
  async getPublicationById(id: string): Promise<Publication> {
    const response = await this.axios.get(`/api/publications/${id}`)
    return response.data.data
  }
  
  async updatePublicationStatus(
    id: string,
    status: PublicationStatus,
    notes?: string
  ): Promise<Publication> {
    const response = await this.axios.put(`/api/publications/${id}/status`, {
      status,
      notes
    })
    return response.data.data
  }
  
  // Utilitários
  private setTokens(tokens: { accessToken: string; refreshToken: string }) {
    localStorage.setItem('accessToken', tokens.accessToken)
    localStorage.setItem('refreshToken', tokens.refreshToken)
  }
  
  logout() {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    window.location.href = '/login'
  }
  
  isAuthenticated(): boolean {
    return !!localStorage.getItem('accessToken')
  }
}

export const apiService = new ApiService()
```

### Hooks Customizados

#### 1. usePublications Hook

**Localização**: `frontend/src/hooks/usePublications.ts`

```typescript
export function usePublications(filters: SearchFilters) {
  const [publications, setPublications] = useState<Publication[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    total: 0
  })
  
  const loadPublications = useCallback(async (page: number = 1, reset: boolean = false) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiService.getPublications(page, 20, filters)
      
      setPublications(prev => reset ? response.data : [...prev, ...response.data])
      setPagination({
        page: response.pagination.page,
        totalPages: response.pagination.totalPages,
        total: response.pagination.total
      })
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }, [filters])
  
  const loadMore = useCallback(() => {
    if (pagination.page < pagination.totalPages && !loading) {
      loadPublications(pagination.page + 1, false)
    }
  }, [pagination, loading, loadPublications])
  
  const refresh = useCallback(() => {
    loadPublications(1, true)
  }, [loadPublications])
  
  useEffect(() => {
    loadPublications(1, true)
  }, [loadPublications])
  
  return {
    publications,
    loading,
    error,
    pagination,
    loadMore,
    refresh,
    hasMore: pagination.page < pagination.totalPages
  }
}
```

# 🔧 Documentação Técnica - JusCash (Parte 3)

## 🐳 Infraestrutura e DevOps

### Containerização com Docker

#### 1. Docker Compose Configuration

**Localização**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Banco de Dados PostgreSQL
  postgres:
    image: postgres:16-alpine
    container_name: juscash_postgres
    environment:
      POSTGRES_DB: juscash_db
      POSTGRES_USER: juscash_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - juscash_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U juscash_user -d juscash_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Cache Redis
  redis:
    image: redis:7-alpine
    container_name: juscash_redis
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./database/redis/redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - juscash_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # API Backend
  api:
    build:
      context: ./backend/api
      dockerfile: Dockerfile
      target: production
    container_name: juscash_api
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://juscash_user:${POSTGRES_PASSWORD}@postgres:5432/juscash_db
      REDIS_URL: redis://redis:6379
      JWT_ACCESS_SECRET: ${JWT_ACCESS_SECRET}
      JWT_REFRESH_SECRET: ${JWT_REFRESH_SECRET}
      API_PORT: 3001
    ports:
      - "3001:3001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - juscash_network
    healthcheck:
      test: ["CMD", "curl", "-f", "${API_BASE_URL}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Scraper Python
  scraper:
    build:
      context: ./backend/scraper
      dockerfile: Dockerfile
    container_name: juscash_scraper
    environment:
      DATABASE_URL: postgresql://juscash_user:${POSTGRES_PASSWORD}@postgres:5432/juscash_db
      REDIS_URL: redis://redis:6379
      API_BASE_URL: http://api:3001
      SCRAPING_HEADLESS: "true"
      SCRAPING_TIMEOUT: 30000
    volumes:
      - scraper_data:/app/data
      - scraper_logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      api:
        condition: service_healthy
    networks:
      - juscash_network
    restart: unless-stopped

  # Frontend Web
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: http://localhost:3001
    container_name: juscash_frontend
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - juscash_network
    restart: unless-stopped

  # Proxy Reverso Nginx
  nginx:
    image: nginx:alpine
    container_name: juscash_nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - api
    networks:
      - juscash_network
    restart: unless-stopped

networks:
  juscash_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  scraper_data:
  scraper_logs:
```

#### 2. Dockerfile - API Backend

**Localização**: `backend/api/Dockerfile`

```dockerfile
# Multi-stage build para otimização
FROM node:20-alpine AS base

# Instalar dependências do sistema
RUN apk add --no-cache \
    libc6-compat \
    ca-certificates \
    tzdata

# Configurar timezone
ENV TZ=America/Sao_Paulo

WORKDIR /app

# Copiar arquivos de dependências
COPY package.json pnpm-lock.yaml ./
COPY prisma ./prisma/

# Instalar pnpm
RUN npm install -g pnpm

# === STAGE: Dependencies ===
FROM base AS deps
RUN pnpm install --frozen-lockfile

# === STAGE: Development ===
FROM base AS development
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Gerar cliente Prisma
RUN pnpm prisma generate

EXPOSE 3001
CMD ["pnpm", "dev"]

# === STAGE: Builder ===
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Gerar cliente Prisma e build
RUN pnpm prisma generate
RUN pnpm build

# === STAGE: Production ===
FROM node:20-alpine AS production

RUN apk add --no-cache \
    libc6-compat \
    ca-certificates \
    dumb-init

# Criar usuário não-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 --gid 1001 --shell /bin/sh nodejs

WORKDIR /app

# Copiar arquivos necessários
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nodejs:nodejs /app/prisma ./prisma

USER nodejs

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node dist/health-check.js

# Usar dumb-init para handling de sinais
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
```

#### 3. Dockerfile - Scraper Python

**Localização**: `backend/scraper/Dockerfile`

```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Playwright browsers
RUN pip install playwright==1.40.0
RUN playwright install --with-deps chromium

# Criar usuário não-root
RUN groupadd --gid 1001 scraper && \
    useradd --uid 1001 --gid scraper --shell /bin/bash --create-home scraper

WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY --chown=scraper:scraper . .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs && \
    chown -R scraper:scraper /app

USER scraper

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

EXPOSE 8080

CMD ["python", "-m", "src.main"]
```

### Configuração de Produção

#### 1. Nginx Configuration

**Localização**: `nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;
    
    # Upstream servers
    upstream api_backend {
        server api:3001;
        keepalive 32;
    }
    
    upstream frontend_backend {
        server frontend:80;
        keepalive 32;
    }
    
    # Main server block
    server {
        listen 80;
        listen 443 ssl http2;
        server_name juscash.com.br www.juscash.com.br;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        
        # Gzip compression
        gzip on;
        gzip_comp_level 6;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Auth routes with stricter rate limiting
        location /api/auth/ {
            limit_req zone=auth burst=10 nodelay;
            
            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Frontend application
        location / {
            proxy_pass http://frontend_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 🔒 Segurança

### Estratégias de Segurança

#### 1. Autenticação JWT

O sistema utiliza JWT com estratégia de refresh token:

```typescript
// Configuração JWT
const JWT_CONFIG = {
  accessToken: {
    expiresIn: '15m',
    algorithm: 'HS256'
  },
  refreshToken: {
    expiresIn: '7d',
    algorithm: 'HS256'
  }
}

// Middleware de autenticação
export const authMiddleware = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const token = extractTokenFromHeader(req.headers.authorization)
    
    if (!token) {
      return res.status(401).json({
        success: false,
        error: { code: 'NO_TOKEN', message: 'Token de acesso não fornecido' }
      })
    }
    
    const decoded = jwt.verify(token, process.env.JWT_ACCESS_SECRET!) as JWTPayload
    
    // Verificar se usuário ainda está ativo
    const user = await userRepository.findById(decoded.userId)
    if (!user || !user.isActive) {
      return res.status(401).json({
        success: false,
        error: { code: 'USER_INACTIVE', message: 'Usuário inativo ou não encontrado' }
      })
    }
    
    req.user = user
    next()
    
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({
        success: false,
        error: { code: 'TOKEN_EXPIRED', message: 'Token expirado' }
      })
    }
    
    return res.status(401).json({
      success: false,
      error: { code: 'INVALID_TOKEN', message: 'Token inválido' }
    })
  }
}
```

#### 2. Rate Limiting

Implementação de rate limiting por IP e usuário:

```typescript
import rateLimit from 'express-rate-limit'
import RedisStore from 'rate-limit-redis'

// Store Redis para rate limiting
const redisStore = new RedisStore({
  sendCommand: (...args: string[]) => redisClient.call(...args)
})

// Rate limiting geral
export const generalRateLimit = rateLimit({
  store: redisStore,
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 100, // máximo 100 requests por IP
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Muitas requisições. Tente novamente em alguns minutos.'
    }
  },
  standardHeaders: true,
  legacyHeaders: false
})

// Rate limiting para autenticação
export const authRateLimit = rateLimit({
  store: redisStore,
  windowMs: 15 * 60 * 1000,
  max: 5, // máximo 5 tentativas de login por IP
  skipSuccessfulRequests: true,
  message: {
    success: false,
    error: {
      code: 'AUTH_RATE_LIMIT_EXCEEDED',
      message: 'Muitas tentativas de login. Tente novamente em 15 minutos.'
    }
  }
})
```

#### 3. Validação e Sanitização

Usando Zod para validação robusta:

```typescript
import { z } from 'zod'

// Schema de validação para registro
export const registerSchema = z.object({
  name: z.string()
    .min(2, 'Nome deve ter pelo menos 2 caracteres')
    .max(100, 'Nome deve ter no máximo 100 caracteres')
    .regex(/^[a-zA-ZÀ-ÿ\s]+$/, 'Nome deve conter apenas letras e espaços'),
    
  email: z.string()
    .email('Email deve ser válido')
    .max(255, 'Email deve ter no máximo 255 caracteres')
    .toLowerCase(),
    
  password: z.string()
    .min(8, 'Senha deve ter pelo menos 8 caracteres')
    .max(128, 'Senha deve ter no máximo 128 caracteres')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/, 
           'Senha deve conter ao menos: 1 minúscula, 1 maiúscula, 1 número e 1 símbolo')
})

// Middleware de validação
export const validateSchema = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      const validated = schema.parse(req.body)
      req.body = validated
      next()
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Dados inválidos fornecidos',
            details: error.errors.map(err => ({
              field: err.path.join('.'),
              message: err.message
            }))
          }
        })
      }
      next(error)
    }
  }
}
```

#### 4. Proteção contra Ataques

```typescript
import helmet from 'helmet'
import cors from 'cors'

// Configuração de segurança
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"]
    }
  },
  crossOriginEmbedderPolicy: false
}))

// CORS configurado
app.use(cors({
  origin: (origin, callback) => {
    const allowedOrigins = process.env.CORS_ORIGIN?.split(',') || []
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true)
    } else {
      callback(new Error('Não permitido pelo CORS'))
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))
```

### Auditoria e Logs de Segurança

#### 1. Log de Autenticação

```typescript
// AuthLog model para auditoria
interface AuthLogData {
  ipAddress?: string
  userAgent?: string
  email: string
  userId?: string
  action: 'LOGIN' | 'LOGOUT' | 'REGISTER' | 'PASSWORD_CHANGE'
  status: 'SUCCESS' | 'FAILED'
  failureReason?: string
  deviceInfo?: object
  locationInfo?: object
}

// Service para logs de autenticação
export class AuthLogService {
  async logAuthEvent(data: AuthLogData): Promise<void> {
    await prisma.authLog.create({
      data: {
        ...data,
        createdAt: new Date()
      }
    })
    
    // Log crítico para arquivo
    if (data.status === 'FAILED') {
      logger.warn('Authentication failure', {
        email: data.email,
        ipAddress: data.ipAddress,
        action: data.action,
        failureReason: data.failureReason
      })
    }
  }
  
  async detectSuspiciousActivity(email: string): Promise<boolean> {
    const recentFailures = await prisma.authLog.count({
      where: {
        email,
        action: 'LOGIN',
        status: 'FAILED',
        createdAt: {
          gte: new Date(Date.now() - 15 * 60 * 1000) // últimos 15 minutos
        }
      }
    })
    
    return recentFailures >= 5
  }
}
```

---

## 📊 Monitoramento e Logs

### Sistema de Logs

#### 1. Configuração Winston

```typescript
import winston from 'winston'

// Configuração do logger
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'juscash-api',
    version: process.env.npm_package_version
  },
  transports: [
    // Console para desenvolvimento
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    
    // Arquivo para produção
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),
    
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 5242880,
      maxFiles: 5
    })
  ]
})
```

#### 2. Métricas de Performance

```typescript
// Middleware de métricas
export const metricsMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now()
  
  res.on('finish', () => {
    const duration = Date.now() - startTime
    const route = req.route?.path || req.path
    
    logger.info('HTTP Request', {
      method: req.method,
      url: req.url,
      route,
      statusCode: res.statusCode,
      duration,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      userId: req.user?.id
    })
    
    // Métricas para Prometheus (se configurado)
    if (process.env.ENABLE_METRICS === 'true') {
      httpRequestDuration.observe(
        { method: req.method, route, status_code: res.statusCode },
        duration / 1000
      )
      
      httpRequestsTotal.inc({
        method: req.method,
        route,
        status_code: res.statusCode
      })
    }
  })
  
  next()
}
```

### Health Checks

#### 1. Health Check Endpoint

```typescript
// Health check completo
export const healthCheck = async (req: Request, res: Response) => {
  const startTime = Date.now()
  
  try {
    // Verificar conexão com banco
    const dbCheck = await checkDatabase()
    
    // Verificar conexão com Redis
    const redisCheck = await checkRedis()
    
    // Verificar métricas do sistema
    const systemMetrics = await getSystemMetrics()
    
    const healthData = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version,
      environment: process.env.NODE_ENV,
      responseTime: Date.now() - startTime,
      services: {
        database: dbCheck.status,
        redis: redisCheck.status
      },
      metrics: systemMetrics
    }
    
    const overallStatus = [dbCheck.status, redisCheck.status].every(status => status === 'healthy')
      ? 'healthy'
      : 'unhealthy'
    
    res.status(overallStatus === 'healthy' ? 200 : 503).json({
      success: true,
      data: { ...healthData, status: overallStatus }
    })
    
  } catch (error) {
    logger.error('Health check failed', error)
    
    res.status(503).json({
      success: false,
      data: {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    })
  }
}

async function checkDatabase(): Promise<{ status: string; responseTime: number }> {
  const start = Date.now()
  
  try {
    await prisma.$queryRaw`SELECT 1`
    return {
      status: 'healthy',
      responseTime: Date.now() - start
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - start
    }
  }
}
```

---

## ⚙️ Instalação e Configuração

### Instalação Completa

#### 1. Pré-requisitos do Sistema

**Para Desenvolvimento:**

```bash
# Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# pnpm
npm install -g pnpm

# Python 3.11+
sudo apt-get install python3.11 python3.11-pip python3.11-venv

# Docker e Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin

# PostgreSQL (se não usar Docker)
sudo apt-get install postgresql-16 postgresql-client-16

# Git
sudo apt-get install git
```

#### 2. Setup Automatizado

**Script de Instalação:**

```bash
#!/bin/bash
# install.sh - Script de instalação automática

set -e

echo "🚀 Iniciando instalação do JusCash..."

# Verificar pré-requisitos
command -v node >/dev/null 2>&1 || { echo "Node.js não encontrado. Instale Node.js 20+"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python3 não encontrado. Instale Python 3.11+"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker não encontrado. Instale Docker"; exit 1; }

# Clonar repositório (se necessário)
if [ ! -d "juscash" ]; then
  echo "📥 Clonando repositório..."
  git clone https://github.com/seu-usuario/juscash.git
  cd juscash
fi

# Configurar variáveis de ambiente
echo "🔧 Configurando variáveis de ambiente..."
if [ ! -f .env ]; then
  cp .env.example .env
  
  # Gerar secrets JWT aleatórios
  JWT_ACCESS_SECRET=$(openssl rand -base64 32)
  JWT_REFRESH_SECRET=$(openssl rand -base64 32)
  POSTGRES_PASSWORD=$(openssl rand -base64 16)
  
  sed -i "s/your-super-secret-access-key-min-32-chars/$JWT_ACCESS_SECRET/g" .env
  sed -i "s/your-super-secret-refresh-key-min-32-chars/$JWT_REFRESH_SECRET/g" .env
  sed -i "s/your-postgres-password/$POSTGRES_PASSWORD/g" .env
  
  echo "✅ Arquivo .env criado com secrets aleatórios"
fi

# Instalar dependências do backend
echo "📦 Instalando dependências do backend..."
cd backend/api
pnpm install
cd ../..

# Instalar dependências do frontend
echo "📦 Instalando dependências do frontend..."
cd frontend
pnpm install
cd ..

# Configurar Python virtual environment
echo "🐍 Configurando ambiente Python..."
cd backend/scraper
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
cd ../..

# Subir serviços com Docker
echo "🐳 Iniciando serviços com Docker..."
docker-compose up -d postgres redis

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Executar migrações do banco
echo "🗄️ Executando migrações do banco..."
cd backend/api
pnpm prisma migrate deploy
pnpm prisma generate
cd ../..

# Executar seeds (dados iniciais)
echo "🌱 Populando dados iniciais..."
cd backend/api
pnpm db:seed
cd ../..

echo "✅ Instalação concluída com sucesso!"
echo ""
echo "🎯 Próximos passos:"
echo "1. Inicie a API: cd backend/api && pnpm dev"
echo "2. Inicie o frontend: cd frontend && pnpm dev"
echo "3. Inicie o scraper: cd backend/scraper && source venv/bin/activate && python -m src.main"
echo ""
echo "🌐 URLs de acesso:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:3001"
echo "   API Docs: ${API_BASE_URL}-docs"
```

#### 3. Configuração Manual

**Passo a Passo Detalhado:**

1. **Clonar Repositório:**

```bash
git clone https://github.com/seu-usuario/juscash.git
cd juscash
```

2. **Configurar Variáveis de Ambiente:**

```bash
cp .env.example .env
# Editar .env com suas configurações
```

3. **Backend API:**

```bash
cd backend/api
pnpm install
pnpm prisma generate
pnpm prisma migrate dev
pnpm db:seed
pnpm dev
```

4. **Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

5. **Scraper Python:**

```bash
cd backend/scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m src.main --test
```

### Configuração de Produção

#### 1. Variáveis de Ambiente

```bash
# .env.production
NODE_ENV=production
API_PORT=3001

# Database
DATABASE_URL=postgresql://user:password@host:5432/juscash_db

# JWT Secrets (ALTERAR EM PRODUÇÃO!)
JWT_ACCESS_SECRET=seu-secret-super-seguro-de-no-minimo-32-caracteres
JWT_REFRESH_SECRET=seu-refresh-secret-super-seguro-de-no-minimo-32-caracteres

# CORS
CORS_ORIGIN=https://seu-dominio.com,https://www.seu-dominio.com

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info

# Redis
REDIS_URL=redis://localhost:6379

# Scraper
SCRAPING_HEADLESS=true
SCRAPING_TIMEOUT=30000
SCRAPING_MAX_RETRIES=3
```

#### 2. Deploy com Docker

```bash
# Build e deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde dos serviços
docker-compose ps
docker-compose logs -f

# Executar migrações
docker-compose exec api pnpm prisma migrate deploy
```

#### 3. Monitoramento

```bash
# Logs em tempo real
docker-compose logs -f api
docker-compose logs -f scraper

# Métricas de sistema
curl ${API_BASE_URL}/health
curl ${API_BASE_URL}/metrics
```

---

## 📚 Guias de Desenvolvimento

### Contribuindo para o Projeto

#### 1. Estrutura de Commits

```
tipo(escopo): descrição

Tipos permitidos:
- feat: nova funcionalidade
- fix: correção de bug
- docs: documentação
- style: formatação
- refactor: refatoração
- test: testes
- chore: manutenção

Exemplo:
feat(api): adicionar endpoint de busca avançada
fix(scraper): corrigir extração de valores monetários
docs(readme): atualizar guia de instalação
```

#### 2. Padrões de Código

**TypeScript/JavaScript:**

```typescript
// Usar interfaces para tipos
interface Publication {
  id: string
  processNumber: string
  status: PublicationStatus
}

// Usar enums para constantes
enum PublicationStatus {
  NOVA = 'NOVA',
  LIDA = 'LIDA',
  ENVIADA_PARA_ADV = 'ENVIADA_PARA_ADV',
  CONCLUIDA = 'CONCLUIDA'
}

// Funções async/await
async function getPublications(filters: SearchFilters): Promise<Publication[]> {
  try {
    const result = await prisma.publication.findMany({
      where: buildWhereClause(filters)
    })
    return result
  } catch (error) {
    logger.error('Error fetching publications', error)
    throw error
  }
}
```

**Python:**

```python
# Type hints obrigatórios
from typing import List, Optional, Dict, Any

# Classes com dataclasses
@dataclass
class Publication:
    id: str
    process_number: str
    content: str
    status: PublicationStatus
    created_at: datetime

# Async/await para I/O
async def extract_publications(criteria: ScrapingCriteria) -> List[Publication]:
    """Extrai publicações baseado nos critérios fornecidos."""
    try:
        publications = await scraper.extract(criteria)
        return [Publication.from_raw(pub) for pub in publications]
    except Exception as e:
        logger.error(f"Error extracting publications: {e}")
        raise
```

#### 3. Testing Strategy

**Backend Tests:**

```typescript
// Unit tests
describe('PublicationService', () => {
  it('should create publication with valid data', async () => {
    const publicationData = createValidPublicationData()
    const result = await publicationService.create(publicationData)
    
    expect(result).toBeDefined()
    expect(result.status).toBe(PublicationStatus.NOVA)
  })
})

// Integration tests
describe('Publication API', () => {
  it('should return paginated publications', async () => {
    const response = await request(app)
      .get('/api/publications')
      .set('Authorization', `Bearer ${validToken}`)
      .expect(200)
    
    expect(response.body.success).toBe(true)
    expect(response.body.data).toBeArray()
  })
})
```

### Troubleshooting Comum

#### 1. Problemas de Database

```bash
# Resetar database
pnpm prisma migrate reset

# Regenerar cliente
pnpm prisma generate

# Verificar conexão
pnpm prisma db pull
```

#### 2. Problemas do Scraper

```bash
# Testar scraper
python -m src.main --test-scraping

# Verificar browsers
python -m playwright install chromium

# Debug mode
SCRAPING_HEADLESS=false python -m src.main
```

#### 3. Problemas de Performance

```bash
# Analisar queries lentas
EXPLAIN ANALYZE SELECT * FROM publications WHERE ...

# Verificar índices
\d+ publications

# Monitorar conexões
SELECT count(*) FROM pg_stat_activity;
```

---

**Fim da Documentação Técnica Completa**

---

### 📄 Informações da Documentação

**Versão**: 1.0  
**Data**: Junho 2025
**Autore**: Junior Martins

**Contato Técnico**:

- Email: <amjr.box@gmail.com>
- GitHub: <https://github.com/juniromartinxo>

---

*Esta documentação técnica fornece todos os detalhes necessários para desenvolvimento, manutenção e deploy do sistema JusCash.*
