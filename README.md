# 📋 JusCash - Sistema de Gerenciamento DJE

> Sistema moderno e automatizado para gerenciamento de publicações do Diário da Justiça Eletrônico de São Paulo (DJE-SP), desenvolvido para advogados e escritórios jurídicos.

## 🌟 Visão Geral do Projeto

O **JusCash** é uma solução completa que automatiza a coleta, organização e acompanhamento de publicações jurídicas do DJE-SP. O sistema oferece uma interface visual intuitiva baseada em Kanban para gerenciar o fluxo de trabalho das publicações, desde a coleta automática até a conclusão dos processos.

### 🏗️ Arquitetura do Sistema

```mermaid
graph TB
    A[DJE-SP] --> B[Sistema de Scraping]
    B --> C[PostgreSQL Database]
    C --> D[API RESTful]
    D --> E[Interface Kanban]
    E --> F[Usuário Final]
    
    G[Redis Cache] --> D
    H[Sistema de Filas] --> B
    I[Monitoramento] --> B
```

### 🎯 Componentes Principais

- **🤖 Scraper Automático**: Coleta diária de publicações do DJE-SP com filtragem inteligente
- **⚡ API RESTful**: Backend robusto com autenticação JWT e arquitetura limpa
- **🎨 Interface Kanban**: Frontend moderno em React com sistema de drag-and-drop
- **📊 Sistema de Filas**: Processamento assíncrono com Redis
- **🔍 Busca Avançada**: Filtros inteligentes por processo, data, valor e status

## 📋 Requisitos para Execução Local

### 🔧 Pré-requisitos

- **Docker** 20.10+ e **Docker Compose** 3.8+
- **Git** para clonagem do repositório
- **4GB RAM** mínimo (recomendado 8GB)
- **Portas disponíveis**: 5173, 8000, 5433, 6379, 8000

### 🛠️ Dependências dos Serviços

| Serviço | Tecnologia | Versão | Porta |
|---------|------------|--------|-------|
| Frontend | React + Vite | 18+ | 5173 |
| API | Node.js + TypeScript | 20+ | 3001 |
| Scraper | Python + FastAPI | 3.11+ | 8000 |
| Database | PostgreSQL | 16+ | 5433 |
| Cache | Redis | 7+ | 6379 |

## 🚀 Instruções de Instalação e Execução

### 📦 Instalação Automática (Recomendada)

```bash
# 1. Clonar o repositório
git clone https://github.com/juniormartinxo/juscash.git
cd juscash

# 2. Executar instalação automática completa (7 etapas)
./install.sh

# 3. Iniciar todos os serviços
./start.sh
```

#### 🤖 Scripts de Gerenciamento Disponíveis

| Script | Função | Descrição |
|--------|--------|-----------|
| `./install.sh` | 🚀 **Instalação Completa** | Configura todo o ambiente automaticamente |
| `./start.sh` | ▶️ **Iniciar Sistema** | Inicia todos os containers |
| `./restart.sh` | 🔄 **Reiniciar Sistema** | Reconstrói e reinicia todos os serviços |

**📋 [Ver todos os scripts disponíveis](./scripts/README.md)**

### 🐳 Instalação Manual com Docker

```bash
# 1. Clonar e configurar ambiente
git clone https://github.com/juniormartinxo/juscash.git
cd juscash

# 2. Criar arquivo de ambiente
cp .env.example .env

# 3. Configurar variáveis no .env (edite conforme necessário)
nano .env

# 4. Construir e iniciar containers
docker-compose up -d --build

# 5. Verificar status dos serviços
docker-compose ps
```

### 🔧 Comandos Úteis

```bash
# Parar todos os serviços
docker-compose down

# Ver logs em tempo real
docker-compose logs -f

# Reiniciar um serviço específico
docker-compose restart api

# Acessar shell do container da API
docker-compose exec api bash

# Backup do banco de dados
./scripts/backup.sh

# Limpar workspace (cuidado - remove todos os dados!)
./scripts/clean-workspace.sh
```

## 🌐 Acesso aos Serviços

Após a instalação, os serviços estarão disponíveis em:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | <http://localhost:5173> | Interface principal do usuário |
| **API** | <http://localhost:8000> | Documentação da API |
| **API Docs** | <http://localhost:8000/api/docs> | Swagger UI |
| **Scraper API** | <http://localhost:5000> | API do sistema de scraping |
| **Scraper Docs** | <http://localhost:5000/docs> | Documentação do scraper |

## 📡 Exemplos de Requisições à API

### 🔐 Autenticação

#### Cadastro de Usuário

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@exemplo.com",
    "password": "MinhaSenh@123"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@exemplo.com",
    "password": "MinhaSenh@123"
  }'
```

### 📄 Gestão de Publicações

#### Listar Publicações

```bash
curl -X GET "http://localhost:8000/api/publications?page=1&limit=10&status=NOVA" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

#### Criar Nova Publicação

```bash
curl -X POST http://localhost:8000/api/publications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "process_number": "1234567-89.2024.8.26.0100",
    "publication_date": "2024-03-15T00:00:00.000Z",
    "availability_date": "2024-03-17T00:00:00.000Z",
    "authors": ["João Silva Santos", "Maria Oliveira"],
    "defendant": "Instituto Nacional do Seguro Social - INSS",
    "lawyers": [
      {
        "name": "Dr. Carlos Advogado",
        "oab": "123456"
      }
    ],
    "gross_value": 150000,
    "net_value": 135000,
    "content": "Conteúdo completo da publicação...",
    "status": "NOVA"
  }'
```

#### Atualizar Status de Publicação

```bash
curl -X PATCH http://localhost:8000/api/publications/PUBLICATION_ID/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{
    "status": "LIDA"
  }'
```

#### Buscar Publicações com Filtros

```bash
curl -X GET "http://localhost:8000/api/publications/search?search=aposentadoria&startDate=2024-01-01&endDate=2024-12-31" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 🤖 API do Scraper

#### Executar Scraping de Data Específica

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "command": "scraper",
    "args": {
      "date": "2024-12-17"
    }
  }'
```

#### Verificar Status do Scraper

```bash
curl -X GET http://localhost:8000/status
```

## 🎯 Fluxo de Trabalho do Kanban

O sistema utiliza um board Kanban visual com 4 colunas que representam o ciclo de vida das publicações:

### 📋 Estrutura do Kanban

```mermaid
flowchart LR
    A[📋 Nova Publicação] --> B[👀 Publicação Lida]
    B --> C[📤 Enviar para Advogado]
    C --> D[✅ Concluído]
    C --> B
    
    style A fill:#f9f9f9
    style B fill:#e3f2fd
    style C fill:#fff3e0
    style D fill:#e8f5e8
```

### 🔄 Detalhamento dos Status

#### 1. 📋 **Nova Publicação**

- **Descrição**: Publicações recém-coletadas pelo sistema de scraping
- **Ações Disponíveis**:
  - Visualizar detalhes completos
  - Mover para "Publicação Lida"
- **Regras**: Status inicial de todas as publicações
- **Indicadores**: Badge com quantidade total

#### 2. 👀 **Publicação Lida**

- **Descrição**: Publicações visualizadas e analisadas pelo usuário
- **Ações Disponíveis**:
  - Mover para "Enviar para Advogado"
  - Retornar para "Nova Publicação" se necessário
- **Regras**: Indica que o conteúdo foi revisado
- **Workflow**: Ponto de decisão sobre encaminhamento

#### 3. 📤 **Enviar para Advogado Responsável**

- **Descrição**: Publicações que requerem ação específica do advogado
- **Ações Disponíveis**:
  - Mover para "Concluído"
  - Retornar para "Publicação Lida" se necessário
- **Regras**: Controle de workflow interno do escritório
- **Notificações**: Pode gerar alertas para o advogado responsável

#### 4. ✅ **Concluído**

- **Descrição**: Publicações totalmente processadas
- **Ações Disponíveis**: Apenas visualização (somente leitura)
- **Regras**: Status final - não permite movimentação
- **Arquivo**: Mantido para histórico e auditoria

### 🎮 Funcionalidades do Kanban

#### **Drag & Drop Inteligente**

- Arraste e solte publicações entre colunas
- Validação automática de movimentos permitidos
- Feedback visual durante a movimentação
- Reversão automática em caso de erro

#### **Carregamento Otimizado**

- Paginação automática (30 itens por vez)
- Lazy loading ao fazer scroll
- Preload inteligente para melhor performance
- Cache local para reduzir requisições

#### **Filtros Avançados**

```bash
# Exemplos de filtros disponíveis:
- Por data (publicação/disponibilidade)
- Por texto (busca no conteúdo)
- Por número de processo
- Por valor (faixas configuráveis)
- Por advogado/autor
- Por status específico
```

#### **Busca Inteligente**

- Busca em tempo real
- Destacamento dos termos encontrados
- Busca em múltiplos campos simultaneamente
- Histórico de buscas recentes

### ⚙️ Configurações do Workflow

#### **Regras de Negócio**

- Movimentos permitidos são pré-definidos
- Validação de permissões por usuário
- Log de auditoria para todas as mudanças
- Possibilidade de reverter ações

#### **Personalização**

- Cores das colunas configuráveis
- Campos exibidos nos cards personalizáveis
- Ordenação flexível (data, valor, prioridade)
- Filtros salvos para reutilização

## 🔧 Configuração Avançada

### 📝 Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
# Database
DATABASE_URL="postgresql://juscash_user:juscash_password@postgres:5432/juscash_db"

# JWT Secrets (OBRIGATÓRIO ALTERAR EM PRODUÇÃO!)
JWT_ACCESS_SECRET="seu-jwt-access-secret-de-pelo-menos-32-caracteres"
JWT_REFRESH_SECRET="seu-jwt-refresh-secret-de-pelo-menos-32-caracteres"

# API Configuration
API_PORT=8000
NODE_ENV=development
CORS_ORIGIN="http://localhost:3000"

# Redis Configuration
REDIS_URL="redis://redis:6379"
REDIS_PASSWORD="juscash_redis_password"

# Scraper Configuration
SCRAPER_API_PORT=8000
PYTHONPATH="/app"

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

### 🧪 Executar Testes

```bash
# Testes da API
cd backend/api
npm test

# Testes do Scraper
cd backend/scraper
python -m pytest

# Testes E2E
npm run test:e2e
```

## 📚 Documentação Completa

A documentação do JusCash foi **unificada e reorganizada** para facilitar a navegação:

### 👤 Para Usuários

- **[📖 Manual do Usuário](./docs/MANUAL-USUARIO.md)** - Guia completo de uso
- **[🚀 Guia de Instalação](./docs/GUIA-INSTALACAO.md)** - Instalação passo-a-passo
- **[🛠️ Troubleshooting](./docs/TROUBLESHOOTING.md)** - Solução de problemas

### 👨‍💻 Para Desenvolvedores

- **[🔌 API Documentation](./docs/api/)** - Documentação técnica e exemplos
- **[🕷️ Scraper Guide](./docs/scraper/)** - Sistema de scraping
- **[⚛️ Frontend Guide](./docs/frontend/)** - Interface React

### 🚀 Para DevOps

- **[🐳 Docker Guide](./docs/deployment/DOCKER.md)** - Containerização
- **[📊 Monitoring](./docs/deployment/MONITORING.md)** - Observabilidade
- **[💾 Backup](./docs/deployment/BACKUP.md)** - Estratégias de backup

**📋 [Índice Completo da Documentação](./docs/README.md)**

## 🆘 Solução de Problemas

### Problemas Comuns

#### Erro de Porta em Uso

```bash
# Verificar portas em uso
./scripts/check-ports.sh

# Parar serviços conflitantes
sudo lsof -ti:3000 | xargs kill -9
```

#### Problemas de Permissão

```bash
# Dar permissões aos scripts
chmod +x *.sh scripts/*.sh

# Verificar propriedade dos arquivos
sudo chown -R $USER:$USER .
```

#### Erro de Conexão com Banco

```bash
# Verificar status do PostgreSQL
docker-compose logs postgres

# Recriar banco de dados
docker-compose down -v
docker-compose up -d postgres
```

#### Cache do Redis

```bash
# Limpar cache do Redis
docker-compose exec redis redis-cli FLUSHALL

# Verificar conexão
./scripts/check-redis.sh
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Suporte

- **Email**: <juniormatinxo@gmail.com>
- **Issues**: [GitHub Issues](https://github.com/juniormartinxo/juscash/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/juniormartinxo/juscash/wiki)

---

## 🚀 Desenvolvido com ❤️ para a JusCash

[![Made with TypeScript](https://img.shields.io/badge/Made%20with-TypeScript-blue)](https://typescript.org/)
[![Made with React](https://img.shields.io/badge/Made%20with-React-61DAFB)](https://reactjs.org/)
[![Made with Node.js](https://img.shields.io/badge/Made%20with-Node.js-339933)](https://nodejs.org/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB)](https://python.org/)
