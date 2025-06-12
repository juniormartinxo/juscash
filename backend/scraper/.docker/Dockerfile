FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário antes de instalar dependências
RUN useradd --create-home --shell /bin/bash scraper

WORKDIR /app

# Instalar dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Instalar browsers do Playwright como root, mas configurar para todos os usuários
RUN python -m playwright install chromium --with-deps

# Dar permissões para o usuário scraper acessar os browsers
RUN chmod -R 755 /root/.cache/ms-playwright || true
RUN mkdir -p /home/scraper/.cache && \
    cp -r /root/.cache/ms-playwright /home/scraper/.cache/ || true && \
    chown -R scraper:scraper /home/scraper/.cache || true

# Stage de desenvolvimento
FROM base AS development
COPY . .
RUN chown -R scraper:scraper /app
USER scraper
CMD ["python", "-m", "src.main"]

# Stage de produção
FROM base AS production
COPY src/ ./src/
COPY *.py ./
RUN chown -R scraper:scraper /app
USER scraper
CMD ["python", "-m", "src.main"]