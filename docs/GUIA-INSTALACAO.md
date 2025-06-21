# 🚀 Guia de Instalação - JusCash

> Instruções completas para instalação e configuração do sistema JusCash

## 📋 Requisitos do Sistema

### 🔧 Pré-requisitos Obrigatórios

- **Docker** 20.10+ e **Docker Compose** 3.8+
- **Git** para clonagem do repositório
- **4GB RAM** mínimo (recomendado 8GB)
- **10GB** de espaço em disco

### 🌐 Portas Necessárias

Certifique-se de que as seguintes portas estão disponíveis:

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Frontend | 5173 | Interface React |
| API | 8000 | Backend Node.js |
| Scraper API | 5000 | API Python do scraper |
| PostgreSQL | 5433 | Banco de dados |
| Redis | 6379 | Cache e filas |

## 🚀 Instalação Automática (Recomendada)

### Método 1: Instalação Completa com Script Automatizado

```bash
# 1. Clonar o repositório
git clone https://github.com/juniormartinxo/juscash.git
cd juscash

# 2. Executar instalação automática completa
./install.sh

# 3. Iniciar os serviços
./start.sh
```

#### 🔍 O que o script `./install.sh` faz

O script de instalação executa automaticamente **7 etapas** de configuração:

1. **🔍 Verificação de Variáveis de Ambiente** - Valida arquivo `.env`
2. **🌐 Verificação de Conflitos de Portas** - Testa se portas estão livres
3. **💾 Configuração do Redis** - Cache e sistema de filas
4. **⚡ Configuração da API** - Backend Node.js com dependências
5. **🗄️ Configuração do Banco de Dados** - PostgreSQL com Prisma
6. **🎨 Configuração do Frontend** - Vite React com dependências
7. **🕷️ Configuração do Scraper** - Python com Playwright

**⚠️ Importante**: O script:

- **Solicita confirmação** antes de executar
- **Para containers existentes** automaticamente
- **Limpa o workspace** antes de instalar
- **Exibe logs coloridos** para acompanhar o progresso
- **Para a execução** se alguma etapa falhar

#### 🚀 O que o script `./start.sh` faz

- **Verifica dependências** (Docker, Docker Compose)
- **Valida arquivos necessários** (.env, docker-compose.yml)
- **Inicia todos os containers** em background
- **Mostra status e logs** dos serviços

### Método 2: Scripts Individuais

Se quiser executar etapas específicas ou verificar componentes individuais:

#### 🔍 Scripts de Verificação

```bash
# Verificar se portas estão livres
./scripts/check-ports.sh

# Verificar configuração do ambiente (.env)
./scripts/check-env.sh

# Verificar conexão com Redis
./scripts/check-redis.sh
```

#### ⚙️ Scripts de Configuração

```bash
# Configurar banco de dados PostgreSQL
./scripts/setup-database.sh

# Configurar Redis (cache e filas)
./scripts/setup-redis.sh

# Configurar API Node.js
./scripts/setup-api.sh

# Configurar frontend Vite/React
./scripts/setup-vite.sh

# Configurar scraper Python
./scripts/setup-scraper.sh
```

#### 🛠️ Scripts de Manutenção

```bash
# Limpar workspace (remove containers, volumes, etc.)
./scripts/clean-workspace.sh

# Corrigir permissões do scraper
./scripts/fix-scraper-permissions.sh

# Testar scraper individualmente
./scripts/test-scraper.sh

# Executar scraper em modo local
./scripts/run-scraper-local.sh
```

#### 📚 Documentação dos Scripts

```bash
# Ver documentação completa dos scripts
cat ./scripts/README.md
```

## 🐳 Instalação Manual com Docker

### 1. Preparação do Ambiente

```bash
# Clonar repositório
git clone https://github.com/juniormartinxo/juscash.git
cd juscash

# Verificar dependências
docker --version
docker-compose --version
```

### 2. Configuração de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar variáveis de ambiente
nano .env
```

#### Principais Variáveis a Configurar

```bash
# Database
DATABASE_URL="postgresql://juscash_user:juscash_password@postgres:5432/juscash_db"

# JWT Secrets (OBRIGATÓRIO ALTERAR!)
JWT_ACCESS_SECRET="seu-jwt-access-secret-de-pelo-menos-32-caracteres"
JWT_REFRESH_SECRET="seu-jwt-refresh-secret-de-pelo-menos-32-caracteres"

# API Configuration
API_PORT=8000
NODE_ENV=development
CORS_ORIGIN="http://localhost:3000"

# Redis
REDIS_URL="redis://redis:6379"
REDIS_PASSWORD="juscash_redis_password"

# Scraper
SCRAPER_API_PORT=5000
PYTHONPATH="/app"
```

### 3. Construção e Inicialização

```bash
# Construir containers
docker-compose build

# Iniciar serviços em background
docker-compose up -d

# Verificar status
docker-compose ps
```

### 4. Verificação da Instalação

```bash
# Health check dos serviços
curl http://localhost:8000/health
curl http://localhost:5000/health

# Verificar logs
docker-compose logs -f
```

## 🔧 Instalação para Desenvolvimento

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
# Acesse http://localhost:5173
```

### Backend API (Node.js)

```bash
cd backend/api
npm install
npm run dev
# API disponível em http://localhost:8000
```

### Scraper (Python)

```bash
cd backend/scraper
pip install -r requirements.txt
python main.py
# API disponível em http://localhost:5000
```

### Banco de Dados

```bash
# PostgreSQL local
docker run -d \
  --name juscash-postgres \
  -e POSTGRES_USER=juscash_user \
  -e POSTGRES_PASSWORD=juscash_password \
  -e POSTGRES_DB=juscash_db \
  -p 5433:5432 \
  postgres:16

# Redis local
docker run -d \
  --name juscash-redis \
  -p 6379:6379 \
  redis:7-alpine
```

## 🌐 Acessando o Sistema

Após a instalação bem-sucedida:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | <http://localhost:5173> | Interface principal |
| **API Docs** | <http://localhost:8000/api/docs> | Documentação Swagger |
| **Scraper Docs** | <http://localhost:5000/docs> | Docs do scraper |
| **Health Check** | <http://localhost:8000/health> | Status da API |

## 🧪 Testando a Instalação

### 1. Teste de Conectividade

```bash
# Testar API
curl -X GET http://localhost:8000/health

# Testar Scraper
curl -X GET http://localhost:5000/health

# Testar frontend (abrir no navegador)
open http://localhost:5173
```

### 2. Teste de Funcionalidades

```bash
# Cadastrar usuário
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste Usuario",
    "email": "teste@exemplo.com",
    "password": "MinhaSenh@123"
  }'

# Fazer login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@exemplo.com",
    "password": "MinhaSenh@123"
  }'
```

## 🛠️ Comandos Úteis

### Scripts de Gerenciamento

```bash
# 🚀 Iniciar sistema (após instalação)
./start.sh

# 🔄 Reiniciar sistema completo
./restart.sh

# 🛑 Parar todos os serviços
docker-compose down
```

#### 🔄 O que o script `./restart.sh` faz

- **Para todos os containers** em execução
- **Reconstrói as imagens** com `--build`
- **Reinicia todos os serviços** automaticamente
- **Mostra status e logs** após reiniciar

### Gerenciamento Manual de Containers

```bash
# Reiniciar um serviço específico
docker-compose restart api

# Ver logs em tempo real
docker-compose logs -f api

# Acessar shell do container
docker-compose exec api bash

# Rebuild completo manual
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Backup e Manutenção

```bash
# Backup do banco
./scripts/backup.sh

# Limpeza completa (CUIDADO!)
./scripts/clean-workspace.sh

# Verificar espaço em disco
df -h
docker system df
```

## 🚨 Solução de Problemas Comuns

### Problema: Porta em Uso

```bash
# Verificar processos usando as portas
sudo lsof -i :5173
sudo lsof -i :8000

# Matar processo se necessário
sudo kill -9 PID_DO_PROCESSO
```

### Problema: Permissões

```bash
# Dar permissões aos scripts
chmod +x *.sh scripts/*.sh

# Corrigir propriedade
sudo chown -R $USER:$USER .
```

### Problema: Erro de Memória

```bash
# Verificar uso de memória
free -h
docker stats

# Aumentar swap se necessário
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problema: Banco de Dados

```bash
# Recriar banco
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d api
```

## 📚 Próximos Passos

Após a instalação:

1. **Leia o [Manual do Usuário](./MANUAL-USUARIO.md)** para entender como usar o sistema
2. **Configure o scraper** seguindo o [Guia do Scraper](./scraper/README.md)
3. **Em caso de problemas**, consulte [Troubleshooting](./TROUBLESHOOTING.md)

## 📞 Suporte

Se encontrar problemas durante a instalação:

- **Verifique os logs** com `docker-compose logs`
- **Execute os scripts de verificação** em `./scripts/`
- **Consulte a documentação** de [Troubleshooting](./TROUBLESHOOTING.md)
- **Abra uma issue** no [GitHub](https://github.com/juniormartinxo/juscash/issues)

---

**Desenvolvido com ❤️ para facilitar o gerenciamento de publicações DJE**
