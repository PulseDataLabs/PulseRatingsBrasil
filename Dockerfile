FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gerenciamento rápido de dependências
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT ["./entrypoint.sh"]
