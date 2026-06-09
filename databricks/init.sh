#!/bin/bash
# Init script para cluster Databricks
# Instala dependências que exigem compilação (curl-cffi)
# Configurar como init script no cluster: Cluster > Advanced > Init Scripts

set -e

echo "[init.sh] Instalando curl-cffi e dependências do Pulse Ratings Brasil"

# curl-cffi requer libcurl mais recente que a disponível no Databricks padrão
# Instala via pip forçando o build com a libcurl bundled
pip install --upgrade pip
pip install curl-cffi --no-binary curl-cffi

# Demais dependências (instalação padrão via requirements.txt)
pip install -r /Workspace/Users/pulse_ratings/requirements.txt 2>/dev/null || \
  pip install pandas requests python-dotenv lxml beautifulsoup4

echo "[init.sh] Concluído"
