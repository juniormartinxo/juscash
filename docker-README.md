# Docker Setup - JusCash

Este documento explica como usar Docker para executar o projeto JusCash.

## Pré-requisitos

- Docker
- Docker Compose

## Estrutura dos Serviços

O projeto é composto por 5 serviços:

1. **Frontend** - React com Vite (porta 3000)
2. **API** - Node.js/Express (porta 8000)
3. **Scraper** - Python (sem porta exposta)
4. **PostgreSQL** - Banco de dados (porta 5432)
5. **Redis** - Cache e filas (porta 6379)

## Como Executar

### Desenvolvimento

```bash
# Construir e executar todos os serviços
docker-compose up --build

# Executar em background
docker-compose up -d --build

# Executar apenas alguns serviços
docker-compose up frontend api postgres redis
```

### Produção

```bash
# Usar targets de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

## Comandos Úteis

```bash
# Ver logs de um serviço específico
docker-compose logs -f frontend

# Executar comandos dentro de um container
docker-compose exec api pnpm install
docker-compose exec scraper pip install -r requirements.txt

# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reconstruir um serviço específico
docker-compose build --no-cache frontend
```

## Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example`:

```bash
cp .env.example .env
```

Principais variáveis:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Configuração do banco
- `REDIS_HOST`, `REDIS_PORT` - Configuração do Redis
- `NODE_ENV` - Ambiente da aplicação
- `VITE_API_URL` - URL da API para o frontend

## Volumes

- `postgres_data` - Dados do PostgreSQL
- `redis_data` - Dados do Redis
- Volumes de desenvolvimento para hot-reload

## Rede

Todos os serviços estão na rede `juscash-network` e podem se comunicar usando os nomes dos serviços.

## Troubleshooting

### Problemas Comuns

1. **Porta já em uso**: Altere as portas no docker-compose.yml
2. **Permissões**: Execute com `sudo` se necessário
3. **Cache**: Use `--no-cache` para reconstruir sem cache

### Logs

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs api
```
