#!/usr/bin/env bash
# Despliegue en el VPS: trae lo último de GitHub, reconstruye los contenedores y verifica la API.
# Uso (en el VPS):  cd /opt/bi-leads && ./scripts/desplegar.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Código"
git pull --ff-only

echo "==> Contenedores"
docker compose up -d --build

echo "==> Esperando a la API"
for _ in $(seq 1 40); do
  if docker compose exec -T web wget -qO- http://api:8080/api/salud >/dev/null 2>&1; then break; fi
  sleep 3
done
docker compose exec -T web wget -qO- http://api:8080/api/salud
echo
docker compose ps
