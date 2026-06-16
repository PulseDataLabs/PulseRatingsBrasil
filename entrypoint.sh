#!/bin/bash

cd /app

python -m http.server 80 --bind 0.0.0.0 &

echo "0 0 * * * cd /app && python run_all.py >> /var/log/cron.log 2>&1" \
    > /etc/cron.d/pulse-ratings-cron \
    && chmod 0644 /etc/cron.d/pulse-ratings-cron \
    && crontab /etc/cron.d/pulse-ratings-cron \
    && touch /var/log/cron.log

cron && tail -f /var/log/cron.log
