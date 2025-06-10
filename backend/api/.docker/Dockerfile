# Multi-stage build para otimização
FROM node:22.15.0-alpine AS base

# Instalar pnpm globalmente
RUN npm install -g pnpm

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de configuração do pnpm
COPY .npmrc pnpm-lock.yaml package.json ./

# Instalar dependências
RUN pnpm install --frozen-lockfile

# Copiar código fonte
COPY . .

# Stage de desenvolvimento
FROM base AS development
EXPOSE 8000
CMD ["pnpm", "dev"]

# Stage de build para produção
FROM base AS build
RUN pnpm build

# Stage de produção
FROM node:22.15.0-alpine AS production
RUN npm install -g pnpm
WORKDIR /app

# Copiar apenas arquivos necessários para produção
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod --frozen-lockfile

# Copiar código compilado
COPY --from=build /app/dist ./dist

# Criar usuário não-root para segurança
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

EXPOSE 8000
CMD ["pnpm", "start"]

# Por padrão, usar o stage de desenvolvimento
FROM development
