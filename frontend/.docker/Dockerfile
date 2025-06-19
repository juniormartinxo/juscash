# Multi-stage build para otimização
FROM node:22.15.0-alpine AS base

# Instalar pnpm globalmente
RUN npm install -g pnpm

# Definir diretório de trabalho
WORKDIR /app

RUN apk add --no-cache tzdata bash wget curl

# Copiar arquivos de configuração do pnpm
COPY .npmrc pnpm-lock.yaml package.json ./

# Instalar dependências
RUN pnpm install --frozen-lockfile

# Copiar código fonte
COPY . .

# Stage de desenvolvimento
FROM base AS development
EXPOSE ${VITE_PORT}
CMD ["sh", "-c", "pnpm dev --host 0.0.0.0 --port ${VITE_PORT}"]

# Stage de build para produção
FROM base AS build
RUN pnpm build

# Stage de produção com nginx
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY .docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Por padrão, usar o stage de desenvolvimento
FROM development
