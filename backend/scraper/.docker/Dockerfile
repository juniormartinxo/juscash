# =========================================================================
# BUILDER STAGE
# =========================================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instala dependências de compilação
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Cria ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================================================================
# PRODUCTION STAGE
# =========================================================================
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    PATH="/opt/venv/bin:$PATH"

# Instala dependências do sistema + supervisor
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        supervisor \
        procps \
        wget \
        curl \
        ca-certificates \
        fonts-liberation \
        fonts-noto-color-emoji \
        fonts-dejavu-core \
        libasound2 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libdrm2 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcb-dri3-0 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        libgbm1 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgconf-2-4 \
        libxss1 \
        libxtst6 && \
    rm -rf /var/lib/apt/lists/*

# Cria usuário não-root e diretórios necessários
RUN useradd --create-home --shell /bin/bash scraper && \
    mkdir -p /opt/playwright && \
    mkdir -p /var/log/supervisor && \
    mkdir -p /var/run/supervisor && \
    mkdir -p /app/reports/json && \
    mkdir -p /app/reports/log && \
    mkdir -p /app/reports/pdf && \
    mkdir -p /app/logs && \
    chown -R scraper:scraper /opt/playwright /var/log/supervisor /var/run/supervisor /app/reports /app/logs

WORKDIR /app

# Copia ambiente virtual e código
COPY --from=builder /opt/venv /opt/venv
COPY --chown=scraper:scraper src/ ./src/
COPY --chown=scraper:scraper *.py ./
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY .docker/entrypoint.sh /entrypoint.sh

# Torna entrypoint executável
RUN chmod +x /entrypoint.sh

# Muda para usuário scraper temporariamente para instalar browsers
USER scraper
RUN python -m playwright install chromium

# Volta para root para configurar supervisor e depois muda permanentemente
USER root
RUN chown -R scraper:scraper /app

# Define usuário final
USER scraper

# Comando principal usando entrypoint
CMD ["/entrypoint.sh"]

# =========================================================================
# DEVELOPMENT STAGE
# =========================================================================
FROM production AS development
CMD ["tail", "-f", "/dev/null"]