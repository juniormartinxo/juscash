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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Instalar browsers do Playwright (após instalar as dependências Python)
RUN python -m playwright install chromium --with-deps

# Stage de desenvolvimento
FROM base AS development
COPY . .
RUN useradd --create-home --shell /bin/bash scraper
USER scraper
CMD ["python", "-m", "src.main"]

# Stage de produção
FROM base AS production
COPY src/ ./src/
COPY *.py ./
RUN useradd --create-home --shell /bin/bash scraper
USER scraper
CMD ["python", "-m", "src.main"]