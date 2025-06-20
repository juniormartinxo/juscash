# 🐳 Docker - Containerização JusCash

> Guia completo para containerização e deploy do sistema JusCash

## 🎯 Visão Geral

O JusCash utiliza Docker para containerização completa, facilitando o desenvolvimento, deploy e manutenção. Todos os serviços são orquestrados via Docker Compose.

## 📋 Arquitetura de Containers

```mermaid
graph TB
    subgraph "Docker Network"
        A[Frontend Container<br/>React + Nginx] 
        B[API Container<br/>Node.js + Express]
        C[Scraper Container<br/>Python + FastAPI]
        D[PostgreSQL Container<br/>Database]
        E[Redis Container<br/>Cache & Queue]
    end
    
    A --> B
    B --> D
    B --> E
    C --> B
    C --> D
```

### Containers do Sistema

| Container | Imagem Base | Porta | Função |
|-----------|-------------|-------|--------|
| **frontend** | node:20-alpine | 5173 | Interface React |
| **api** | node:20-alpine | 8000 | Backend API |
| **scraper** | python:3.11-slim | 5000 | Sistema de scraping |
| **postgres** | postgres:16-alpine | 5433 | Banco de dados |
| **redis** | redis:7-alpine | 6379 | Cache e filas |

## 📁 Estrutura Docker

```
juscash/
├── docker-compose.yml           # Orquestração principal
├── docker-compose.prod.yml      # Configuração de produção
├── docker-compose.dev.yml       # Configuração de desenvolvimento
├── .dockerignore               # Arquivos ignorados
├── frontend/
│   └── Dockerfile              # Container React
├── backend/api/
│   └── Dockerfile              # Container API
├── backend/scraper/
│   └── Dockerfile              # Container Scraper
└── nginx/
    ├── Dockerfile              # Proxy reverso
    └── nginx.conf              # Configuração Nginx
```

## 🛠️ Docker Compose - Desenvolvimento

### docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api
    networks:
      - juscash-network

  api:
    build:
      context: ./backend/api
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend/api:/app
      - /app/node_modules
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - juscash-network
    restart: unless-stopped

  scraper:
    build:
      context: ./backend/scraper
      dockerfile: Dockerfile
      target: development
    ports:
      - "5000:5000"
    volumes:
      - ./backend/scraper:/app
      - ./backend/scraper/reports:/app/reports
    env_file:
      - .env
    depends_on:
      - api
      - postgres
    networks:
      - juscash-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: ${DATABASE_NAME:-juscash_db}
      POSTGRES_USER: ${DATABASE_USER:-juscash_user}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-juscash_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER:-juscash_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - juscash-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD:-juscash_redis_password}
    volumes:
      - redis_data:/data
      - ./database/redis/redis.conf:/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - juscash-network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  juscash-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🏭 Docker Compose - Produção

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/var/www/html
    depends_on:
      - frontend
      - api
    networks:
      - juscash-network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    volumes:
      - frontend_dist:/app/dist
    environment:
      - VITE_API_URL=https://api.juscash.com
    networks:
      - juscash-network

  api:
    build:
      context: ./backend/api
      dockerfile: Dockerfile
      target: production
    expose:
      - "8000"
    env_file:
      - .env.production
    environment:
      - NODE_ENV=production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - juscash-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  scraper:
    build:
      context: ./backend/scraper
      dockerfile: Dockerfile
      target: production
    expose:
      - "5000"
    env_file:
      - .env.production
    environment:
      - ENVIRONMENT=production
    volumes:
      - scraper_reports:/app/reports
      - scraper_logs:/app/logs
    depends_on:
      - api
    networks:
      - juscash-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    expose:
      - "5432"
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - juscash-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    expose:
      - "6379"
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - juscash-network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  frontend_dist:
    driver: local
  scraper_reports:
    driver: local
  scraper_logs:
    driver: local
  postgres_backups:
    driver: local

networks:
  juscash-network:
    driver: bridge
```

## 📄 Dockerfiles

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS base

WORKDIR /app

# Instalar dependências
COPY package*.json pnpm-lock.yaml* ./
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copiar código fonte
COPY . .

# Desenvolvimento
FROM base AS development
EXPOSE 5173
CMD ["pnpm", "dev", "--host"]

# Build de produção
FROM base AS build
RUN pnpm build

# Produção com Nginx
FROM nginx:alpine AS production
COPY --from=build /app/dist /var/www/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### API Dockerfile

```dockerfile
# backend/api/Dockerfile
FROM node:20-alpine AS base

# Instalar dependências do sistema
RUN apk add --no-cache dumb-init

WORKDIR /app

# Criar usuário não-root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Instalar dependências
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copiar código
COPY --chown=nodejs:nodejs . .

# Desenvolvimento
FROM base AS development
RUN npm ci
USER nodejs
EXPOSE 8000
CMD ["npm", "run", "dev"]

# Produção
FROM base AS production
RUN npm run build
USER nodejs
EXPOSE 8000
CMD ["dumb-init", "node", "dist/app.js"]
```

### Scraper Dockerfile

```dockerfile
# backend/scraper/Dockerfile
FROM python:3.11-slim AS base

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright
RUN playwright install chromium --with-deps

# Copiar código
COPY . .

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Desenvolvimento
FROM base AS development
EXPOSE 5000
CMD ["python", "main.py"]

# Produção
FROM base AS production
EXPOSE 5000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

## 🚀 Comandos Docker

### Desenvolvimento

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Reconstruir containers
docker-compose up -d --build

# Parar serviços
docker-compose down

# Remover volumes (CUIDADO!)
docker-compose down -v
```

### Produção

```bash
# Deploy de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Atualizar apenas API
docker-compose -f docker-compose.prod.yml up -d --no-deps api

# Scaling da API
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

### Manutenção

```bash
# Entrar no container
docker-compose exec api bash
docker-compose exec postgres psql -U juscash_user -d juscash_db

# Ver uso de recursos
docker stats

# Limpar containers e imagens não utilizados
docker system prune -a

# Backup do banco
docker-compose exec postgres pg_dump -U juscash_user juscash_db > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U juscash_user juscash_db < backup.sql
```

## 🔧 Configurações Avançadas

### Health Checks

```yaml
# Exemplo de health check personalizado
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Resource Limits

```yaml
# Limites de recursos
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Secrets Management

```yaml
# Usando Docker secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt
  
services:
  api:
    secrets:
      - db_password
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

## 📊 Monitoramento

### Container Monitoring

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

### Logs Centralizados

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 Segurança

### Dockerfile Security

```dockerfile
# Usar imagens oficiais
FROM node:20-alpine

# Não rodar como root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# Escanear vulnerabilidades
RUN npm audit fix

# Multi-stage builds
FROM node:20-alpine AS build
# ... build steps ...

FROM node:20-alpine AS production
COPY --from=build /app/dist ./dist
```

### Network Security

```yaml
networks:
  juscash-network:
    driver: bridge
    internal: true  # Rede interna apenas
  
  public-network:
    driver: bridge
    # Rede pública para nginx
```

## 🧪 Testing

### Test Containers

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-api:
    build:
      context: ./backend/api
      target: development
    command: npm test
    depends_on:
      - test-postgres
    environment:
      - NODE_ENV=test
      - DATABASE_URL=postgresql://test_user:test_pass@test-postgres:5432/test_db

  test-postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    tmpfs:
      - /var/lib/postgresql/data
```

## 📚 Troubleshooting

### Problemas Comuns

1. **Porta em uso**
   ```bash
   # Verificar portas
   sudo lsof -i :5173
   
   # Matar processo
   sudo kill -9 PID
   ```

2. **Problema de permissão**
   ```bash
   # Corrigir permissões
   sudo chown -R $USER:$USER .
   ```

3. **Espaço em disco**
   ```bash
   # Limpar Docker
   docker system prune -a --volumes
   ```

4. **Container não inicia**
   ```bash
   # Ver logs detalhados
   docker-compose logs container_name
   
   # Debug interativo
   docker-compose run --rm api bash
   ```

## 📖 Recursos Adicionais

- **[Backup Guide](./BACKUP.md)** - Estratégias de backup
- **[Production Guide](./PRODUCTION.md)** - Deploy em produção
- **[Monitoring Guide](./MONITORING.md)** - Monitoramento de containers

---

**Docker: Containerização que facilita desenvolvimento e deployment** 🐳 