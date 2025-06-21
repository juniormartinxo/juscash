#!/bin/bash

# Função que sempre gera hex (0-9, a-f)
generate_secure_hash() {
    local length=${1:-32}
    
    # Detecta o sistema operacional
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash, WSL, Cygwin)
        if command -v openssl >/dev/null 2>&1; then
            openssl rand -hex $((length/2))
        elif command -v powershell >/dev/null 2>&1; then
            # Chama PowerShell do Git Bash
            powershell -Command "-join ((65..90) + (97..122) + (48..57) | Get-Random -Count $length | ForEach-Object {[char]\$_})"
        else
            # Fallback para Windows
            local result=""
            local chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$@&%!@#$%&*_+"
            for i in $(seq 1 $length); do
                local rand=$((RANDOM % 62))
                result="${result}${chars:$rand:1}"
            done
            echo "$result"
        fi
    else
        # Linux/macOS
        if [ -r /dev/urandom ]; then
            cat /dev/urandom | tr -dc 'a-zA-Z0-9#$@&%!@#$%&*_+' | fold -w $length | head -n 1
        elif command -v openssl >/dev/null 2>&1; then
            openssl rand -hex $((length/2))
        else
            # Último recurso
            echo "$(date +%s%N)$$RANDOM" | sha256sum | cut -c 1-$length
        fi
    fi
}

# Testa a função
echo "Testando geração de hash:"
echo "Hash gerado: $(generate_secure_hash 64)"

# Gera as variáveis
SCRAPER_API_KEY="scraper-dje-$(generate_secure_hash 64)"
REDIS_PASSWORD=$(generate_secure_hash 32)
POSTGRES_PASSWORD=$(generate_secure_hash 32)
JWT_ACCESS_SECRET=$(generate_secure_hash 32)
JWT_REFRESH_SECRET=$(generate_secure_hash 48)

# Exibe os resultados
echo -e "\nVariáveis geradas:"
echo "SCRAPER_API_KEY=$SCRAPER_API_KEY"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "JWT_ACCESS_SECRET=$JWT_ACCESS_SECRET"
echo "JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET"