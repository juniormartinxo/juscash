# Redis Setup - JusCash Project

## 🚀 Configuração Automática

Este projeto inclui um script de configuração automática que garante que o Redis funcione em qualquer ambiente.

### ⚡ Setup Rápido

Na raiz do projeto execute:

```bash
# Tornar o script executável e executar
chmod +x ./scripts/setup-redis.sh
./setup-redis.sh
```

O script irá:
- ✅ Verificar dependências (Docker, Docker Compose)
- ✅ Criar diretórios necessários
- ✅ Configurar permissões automaticamente
- ✅ Gerar arquivo `.env` se não existir
- ✅ Criar Dockerfile se necessário
- ✅ Limpar configurações antigas
- ✅ Testar a configuração completa

## 🔧 Configuração Manual (se necessário)

### Pré-requisitos
- Docker e Docker Compose instalados
- Arquivo `.env` configurado

### Passos manuais

1. **Criar diretórios:**
   ```bash
   mkdir -p database/redis/{redis-data,logs}
   ```

2. **Configurar permissões:**
   ```bash
   sudo chown -R 1001:1001 database/redis/redis-data
   sudo chown -R 1001:1001 database/redis/logs
   chmod -R 755 database/redis/redis-data database/redis/logs
   ```

3. **Iniciar Redis:**
   ```bash
   docker-compose up -d redis
   ```

4. **Testar:**
   ```bash
   docker exec juscash-redis redis-cli -a $REDIS_PASSWORD ping
   ```

## 📊 Configuração do Redis

### Performance
- **Memória máxima:** 2GB
- **Política de evição:** allkeys-lru
- **Conexões simultâneas:** 10.000
- **TCP keepalive:** 60s

### Persistência
- **RDB snapshots:** A cada 60s se houver mudanças
- **Diretório de dados:** `/var/lib/redis/data`
- **Arquivo de backup:** `dump.rdb`

### Segurança
- **Autenticação:** Senha via variável de ambiente
- **Usuário:** Non-root (1001)
- **Bind:** 0.0.0.0 (apenas dentro da rede Docker)

### Monitoramento
- **Logs:** `/var/log/redis/redis.log`
- **Healthcheck:** Ping a cada 30s
- **Restart:** Automático em falhas

## 🔍 Troubleshooting

### Problema: Redis não inicia

```bash
# Ver logs detalhados
docker-compose logs redis

# Verificar permissões
ls -la database/redis/redis-data/

# Executar script de setup novamente
./scripts/setup-redis.sh
```

### Problema: Erro de permissões
```bash
# Corrigir permissões manualmente
sudo chown -R 1001:1001 database/redis/redis-data
sudo chmod -R 755 database/redis/redis-data
```

### Problema: Container não para de reiniciar
```bash
# Ver logs específicos do erro
docker-compose logs --timestamps redis | tail -20

# Remover e recriar
docker-compose down
docker rm -f juscash-redis
./scripts/setup-redis.sh
```

## 🌐 Uso na Aplicação

### Node.js
```javascript
const redis = require('redis');

const client = redis.createClient({
  url: process.env.REDIS_URL,
  password: process.env.REDIS_PASSWORD
});

await client.connect();

// Cache
await client.setex('user:123', 3600, JSON.stringify(userData));
const cached = await client.get('user:123');

// Filas
await client.lpush('email_queue', JSON.stringify(emailJob));
```

### Python
```python
import redis
import os

r = redis.Redis(
    host='localhost',
    port=6383,
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

# Teste
r.ping()
```

## 📝 Variáveis de Ambiente

Configurar no arquivo `.env`:

```env
REDIS_PORT=6379
REDIS_HOST_PORT=6383
REDIS_CONTAINER_NAME=juscash-redis
REDIS_PASSWORD=sua_senha_super_segura
REDIS_URL=redis://${REDIS_CONTAINER_NAME}:${REDIS_PORT}
```

## 🚀 Comandos Úteis

```bash
# Iniciar apenas o Redis
docker-compose up -d redis

# Ver logs em tempo real
docker-compose logs -f redis

# Conectar via CLI
docker exec -it juscash-redis redis-cli -a $REDIS_PASSWORD

# Ver estatísticas
docker exec juscash-redis redis-cli -a $REDIS_PASSWORD info memory

# Backup manual
docker exec juscash-redis redis-cli -a $REDIS_PASSWORD bgsave

# Monitorar operações
docker exec juscash-redis redis-cli -a $REDIS_PASSWORD monitor
```

## ⚠️ Importante para Produção

1. **Altere as senhas** no arquivo `.env`
2. **Configure backup automático** dos arquivos RDB
3. **Monitore uso de memória** regularmente
4. **Use HTTPS/TLS** para conexões externas
5. **Configure firewall** adequadamente

## 📞 Suporte

Se encontrar problemas:
1. Execute `./scripts/setup-redis.sh` novamente
2. Verifique os logs: `docker-compose logs redis`
3. Consulte a seção de troubleshooting acima