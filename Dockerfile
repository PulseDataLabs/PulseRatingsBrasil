FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ── Cron: roda run_all.py todo dia à meia-noite ─────────────────
# Para alterar o horário, edite a expressão cron abaixo:
#   formato: minuto hora dia mês dia-da-semana
#   Exemplo: 0 0 * * *   = meia-noite todos os dias
#            0 6 * * 1-5 = 06:00 BRST de segunda a sexta
#            30 9 * * 1  = 09:30 BRST toda segunda-feira
RUN echo "0 0 * * * cd /app && python run_all.py >> /var/log/cron.log 2>&1" \
    > /etc/cron.d/pulse-ratings-cron \
    && chmod 0644 /etc/cron.d/pulse-ratings-cron \
    && crontab /etc/cron.d/pulse-ratings-cron \
    && touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log
