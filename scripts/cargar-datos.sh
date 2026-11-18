#!/usr/bin/env bash
# Carga datos/leads.json y datos/ventas.json en el MongoDB del contenedor (reemplaza lo anterior).
# Los .json NO están en GitHub: se copian al VPS con scp desde la PC donde se corrió el ETL.
# Uso (en el VPS):  cd /opt/bi-leads && ./scripts/cargar-datos.sh
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
URI="mongodb://${MONGO_USUARIO}:${MONGO_CLAVE}@localhost:27017/bi_leads?authSource=admin"

for coleccion in leads ventas; do
  echo "==> $coleccion"
  docker compose cp "datos/${coleccion}.json" "mongo:/tmp/${coleccion}.json"
  docker compose exec -T mongo mongoimport --quiet --uri "$URI" --collection "$coleccion" \
    --drop --jsonArray --file "/tmp/${coleccion}.json"
  docker compose exec -T mongo rm -f "/tmp/${coleccion}.json"
done

docker compose exec -T mongo mongosh --quiet "$URI" --eval '
  db.leads.createIndex({ mes: 1 });
  db.leads.createIndex({ compro: 1, mes: 1 });
  db.leads.createIndex({ nombre: 1 });
  db.ventas.createIndex({ mes: 1 });
  db.ventas.createIndex({ leadId: 1 });
  print("leads: " + db.leads.countDocuments() + " · ventas: " + db.ventas.countDocuments());
'
