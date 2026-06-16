#!/bin/bash
set -e

cd /app

echo "[entrypoint] Iniciando HTTP server na porta 80..."
python -m http.server 80 --bind 0.0.0.0 &

echo "[entrypoint] Configurando cron jobs..."
{
  echo "${CRON_RUN_ALL:-0 6,12,21 * * 1-5} cd /app && python run_all.py >> /var/log/cron.log 2>&1 && python scripts/gerar_consulta_json.py >> /var/log/cron.log 2>&1"
  echo "${CRON_CNPJ:-0 1 * * 1-5} cd /app && python -m scripts.consolidar_emissores >> /var/log/cron.log 2>&1 && python -m scripts.preencher_cnpj_cvm >> /var/log/cron.log 2>&1 && python -m scripts.preencher_cnpj_api >> /var/log/cron.log 2>&1"
} > /etc/cron.d/pulse-ratings-cron \
  && chmod 0644 /etc/cron.d/pulse-ratings-cron \
  && crontab /etc/cron.d/pulse-ratings-cron

echo "[entrypoint] Iniciando cron daemon..."
cron

echo "[entrypoint] Container pronto. Schedules ativos:"
echo "  run_all: ${CRON_RUN_ALL:-0 6,12,21 * * 1-5} BRT"
echo "  cnpj:    ${CRON_CNPJ:-0 1 * * 1-5} BRT"
echo "---"

touch /var/log/cron.log
tail -f /var/log/cron.log
