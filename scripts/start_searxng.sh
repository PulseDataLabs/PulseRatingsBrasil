#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Parando container antigo..."
docker rm -f searxng 2>/dev/null || true

echo "Subindo SearXNG..."
docker run -d --name searxng -p 8888:8080 \
  -v "$DIR/searxng-settings.yml:/etc/searxng/settings.yml:ro" \
  searxng/searxng

echo "Aguardando 3s..."
sleep 3

echo "Testando JSON..."
curl -s "http://localhost:8888/search?q=teste&format=json" | python3 -m json.tool

echo ""
echo "OK — SearXNG pronto em http://localhost:8888"
