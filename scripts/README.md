# Scripts do JusCash

Esta pasta contém scripts utilitários para configuração e manutenção do projeto JusCash.

## 📋 Scripts Disponíveis

### 🚀 Instalação e Configuração

#### `install.sh` (raiz do projeto)

Script principal de instalação que executa todos os scripts de configuração necessários.

```bash
./install.sh
```

**O que faz:**

- Executa `check-env.sh` para verificar variáveis de ambiente
- Executa `check-ports.sh` para verificar conflitos de portas
- Executa `setup-redis.sh` para configurar Redis
- Executa `setup-database.sh` para configurar banco de dados com Prisma
- Valida arquivos de configuração

#### `check-env.sh`

Configura o arquivo `.env` com todas as variáveis de ambiente necessárias.

```bash
./scripts/check-env.sh
```

**Configurações incluídas:**

- API Backend (Node.js/Express)
- Frontend (React/Vite)
- PostgreSQL
- Redis
- Configurações de e-mail
- Configurações do scraper

#### `setup-redis.sh`

Configura automaticamente o Redis para funcionar em qualquer ambiente.

```bash
./scripts/setup-redis.sh
```

**O que faz:**

- Verifica dependências (Docker, Docker Compose)
- Cria diretórios necessários
- Configura permissões automaticamente
- Gera Dockerfile se necessário
- Testa a configuração completa

#### `setup-database.sh` ⭐ **NOVO**
Configura o banco de dados PostgreSQL executando comandos do Prisma no container da API.

```bash
./scripts/setup-database.sh
```

**O que faz:**
- Verifica se containers API e PostgreSQL estão rodando
- Inicia containers se necessário
- Aguarda containers ficarem saudáveis
- Executa `npx prisma generate` no container da API
- Executa `npx prisma migrate dev` no container da API
- Executa `npx prisma db seed` no container da API

**Comandos executados:**
1. `npx prisma generate` - Gera cliente Prisma
2. `npx prisma migrate dev` - Executa migrações do banco
3. `npx prisma db seed` - Executa seed inicial (opcional)

### 🔍 Verificação e Diagnóstico

#### `check-ports.sh` ⭐ **NOVO**

Verifica se as portas configuradas no arquivo `.env` estão ocupadas e emite alertas quando necessário.

```bash
./scripts/check-ports.sh
```

**Portas verificadas:**

- **8000**: API Backend
- **3001**: Frontend Vite
- **5433**: PostgreSQL Database
- **6388**: Redis Cache

**Funcionalidades:**

- ✅ Detecta portas em uso
- 💻 Mostra informações do processo que está usando a porta
- 💡 Sugere soluções para resolver conflitos
- 🎯 Oferece alternativas de configuração
- 🚀 Código de saída baseado no resultado (0 = sucesso, >0 = portas em uso)

**Exemplo de uso em scripts:**

```bash
if ./scripts/check-ports.sh; then
    echo "Todas as portas estão livres!"
    docker-compose up --build
else
    echo "Resolva os conflitos de porta primeiro"
fi
```

## 🔧 Comandos Úteis

### Verificação rápida de portas

```bash
# Verificar apenas as portas
./scripts/check-ports.sh

# Parar containers que podem estar usando as portas
docker-compose down
docker stop $(docker ps -aq) 2>/dev/null || true
```

### Resolução de conflitos de portas

#### Opção 1: Parar processos

```bash
# Encontrar e parar processo específico
lsof -ti:PORTA | xargs kill -9

# Parar todos os containers Docker
docker-compose down
```

#### Opção 2: Alterar portas no .env

```bash
# Editar arquivo .env
nano .env

# Alterar as variáveis de porta:
# API_HOST_PORT=8001
# VITE_HOST_PORT=3002
# POSTGRES_HOST_PORT=5434
# REDIS_HOST_PORT=6389
```

#### Opção 3: Usar portas alternativas temporariamente

```bash
export API_BACKEND_HOST_PORT=9000
export FRONTEND_VITE_HOST_PORT=4001
export POSTGRESQL_DATABASE_HOST_PORT=6433
export REDIS_CACHE_HOST_PORT=7388
```

## 🛠️ Desenvolvimento

### Tornando scripts executáveis

```bash
chmod +x scripts/*.sh
```

### Executando scripts individuais

```bash
# Verificar apenas ambiente
./scripts/check-env.sh

# Verificar apenas portas
./scripts/check-ports.sh

# Configurar apenas Redis
./scripts/setup-redis.sh

# Configurar apenas banco de dados
./scripts/setup-database.sh
```

### Comandos úteis do banco de dados

```bash
# Visualizar banco no navegador (Prisma Studio)
docker-compose exec api npx prisma studio

# Acessar PostgreSQL diretamente
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Executar migrações manualmente
docker-compose exec api npx prisma migrate dev

# Resetar banco de dados
docker-compose exec api npx prisma migrate reset

# Ver status das migrações
docker-compose exec api npx prisma migrate status
```

## 📊 Códigos de Saída

| Script | Código 0 | Código >0 |
|--------|----------|-----------|
| `check-env.sh` | Sucesso | Erro na configuração |
| `setup-redis.sh` | Redis configurado | Falha na configuração |
| `setup-database.sh` | Banco configurado | Falha na configuração |
| `check-ports.sh` | Todas portas livres | Número de portas ocupadas |

## 🔍 Troubleshooting

### Problema: Script não executa

```bash
# Tornar executável
chmod +x scripts/nome-do-script.sh

# Verificar permissões
ls -la scripts/
```

### Problema: Erro no arquivo .env

```bash
# Recriar arquivo .env
./scripts/check-env.sh

# Verificar sintaxe
cat .env | grep -E '^[A-Z_]+='
```

### Problema: Portas sempre em conflito

```bash
# Parar todos os containers
docker-compose down
docker system prune -f

# Verificar novamente
./scripts/check-ports.sh
```

### Problema: Falha na configuração do banco de dados

```bash
# Verificar se containers estão rodando
docker-compose ps

# Ver logs dos containers
docker-compose logs api
docker-compose logs postgres

# Reiniciar containers
docker-compose restart api postgres

# Executar configuração novamente
./scripts/setup-database.sh
```

### Problema: Erro nas migrações do Prisma

```bash
# Resetar banco e recomeçar
docker-compose exec api npx prisma migrate reset

# Verificar schema do Prisma
docker-compose exec api cat prisma/schema.prisma

# Executar comandos manualmente
docker-compose exec api npx prisma generate
docker-compose exec api npx prisma migrate dev
```

## 📝 Logs e Debug

Todos os scripts incluem logs coloridos e informativos:

- 🔵 **INFO**: Informações gerais
- 🟢 **SUCCESS**: Operações bem-sucedidas
- 🟡 **WARNING**: Avisos importantes
- 🔴 **ERROR**: Erros que impedem execução

Para debug adicional, você pode executar com `bash -x`:

```bash
bash -x scripts/check-ports.sh
```
