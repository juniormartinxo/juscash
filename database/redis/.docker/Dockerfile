FROM bitnami/redis:8.0.2

# Criar diretórios necessários e definir permissões
USER root
RUN mkdir -p /var/log/redis /var/lib/redis/data && \
    chown -R 1001:1001 /var/log/redis /var/lib/redis && \
    chmod -R 755 /var/log/redis /var/lib/redis

# Voltar para o usuário redis
USER 1001

EXPOSE ${REDIS_PORT}