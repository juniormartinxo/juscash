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
      test: ["CMD", "curl", "-f", "http://localhost:3001/api/health"]
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
echo "   API Docs: http://localhost:3001/api-docs"
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
curl http://localhost:3001/api/health
curl http://localhost:3001/api/metrics
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
**Data**: Janeiro 2024  
**Autores**: Equipe de Desenvolvimento JusCash  
**Revisão**: Quinzenal  

**Contato Técnico**:
- Email: dev@juscash.com  
- Slack: #juscash-dev  
- GitHub: https://github.com/seu-usuario/juscash  

---

*Esta documentação técnica fornece todos os detalhes necessários para desenvolvimento, manutenção e deploy do sistema JusCash.*