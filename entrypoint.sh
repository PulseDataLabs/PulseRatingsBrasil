#!/bin/bash
set -e

cd /app

python -m http.server 80 --bind 0.0.0.0 &

{
  echo "${CRON_RUN_ALL:-0 6,12,21 * * 1-5} cd /app && python run_all.py >> /var/log/cron.log 2>&1 && python scripts/gerar_consulta_json.py >> /var/log/cron.log 2>&1"
  echo "${CRON_CNPJ:-0 1 * * 1-5} cd /app && python -m scripts.consolidar_emissores >> /var/log/cron.log 2>&1 && python -m scripts.preencher_cnpj_cvm >> /var/log/cron.log 2>&1 && python -m scripts.preencher_cnpj_api >> /var/log/cron.log 2>&1"
} > /etc/cron.d/pulse-ratings-cron \
  && chmod 0644 /etc/cron.d/pulse-ratings-cron \
  && crontab /etc/cron.d/pulse-ratings-cron \
  && touch /var/log/cron.log

cron && tail -f /var/log/cron.log
