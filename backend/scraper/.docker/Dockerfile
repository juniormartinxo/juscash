# =========================================================================
# BUILDER STAGE
# Esta fase instala dependências de compilação e as dependências Python.
# =========================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instala apenas as dependências de compilação necessárias aqui
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Cria um ambiente virtual para isolar as dependências
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia e instala as dependências Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================================================================
# PRODUCTION STAGE
# Esta é a imagem final, otimizada e segura para produção.
# =========================================================================
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Define o caminho dos browsers do Playwright para um local compartilhado
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    # Aponta para o ambiente virtual criado na fase anterior
    PATH="/opt/venv/bin:$PATH"

# Instala apenas as dependências de sistema para o Playwright rodar
# O comando `playwright install-deps` faz isso de forma otimizada
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -sSL https://raw.githubusercontent.com/microsoft/playwright-python/main/utils/docker/install-deps.sh | bash -s -- chromium && \
    rm -rf /var/lib/apt/lists/*

# Cria o usuário não-root
RUN useradd --create-home --shell /bin/bash scraper

WORKDIR /app

# Instala os browsers do Playwright (agora em /opt/playwright, acessível a todos)
# Não precisa de `--with-deps` pois já instalamos na etapa anterior
RUN python -m playwright install chromium

# Copia o ambiente virtual com as dependências Python da fase 'builder'
COPY --from=builder /opt/venv /opt/venv

# Copia o código da aplicação e define o dono
# Copie apenas o que é necessário para produção
COPY --chown=scraper:scraper src/ ./src/
COPY --chown=scraper:scraper *.py ./
COPY --chown=scraper:scraper entrypoint.sh .
RUN chmod +x entrypoint.sh

USER scraper

# Usa um entrypoint para iniciar múltiplos processos
ENTRYPOINT ["./entrypoint.sh"]

# =========================================================================
# DEVELOPMENT STAGE
# Esta fase é para desenvolvimento, com o código montado como um volume.
# =========================================================================
FROM production AS development

# No modo de desenvolvimento, você provavelmente montará o código-fonte
# como um volume. Este CMD mantém o container rodando para que você
# possa usar `docker exec` e ter live-reloading.
CMD ["tail", "-f", "/dev/null"]