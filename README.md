# Luis López · BI · Leads y ventas con MongoDB

Proyecto personal de Luis López Lapa para el curso **Inteligencia de Negocios** (UTP, 2026). Es un dashboard que
responde, con datos reales y anonimizados de una empresa peruana de mobiliario para barberías, salones y spas, estas
preguntas:

- ¿Cuántos clientes escribieron por WhatsApp en octubre de 2026 y cuántos compraron?
- ¿Qué compraron: barbería, salón, spa o herramientas?
- ¿Qué día y a qué hora compran más?
- ¿Desde que se activó **Meta CAPI** (30-ago-2026) llegan clientes de mejor calidad?

En vivo: **https://bi.dbltech.tech** (pide una clave).

> Los datos reales **no están en este repositorio**. Aquí solo hay datos de ejemplo inventados en `datos/ejemplo/`.
> El dashboard no muestra montos, teléfonos, DNI ni el nombre de la empresa, y las asesoras aparecen con seudónimo.

## Arquitectura cliente-servidor

```
┌──────────────────────────┐   HTTP/JSON    ┌──────────────────────────┐   driver   ┌───────────────┐
│ Cliente (web/)           │ ─────────────▶ │ Servidor (api/)          │ ─────────▶ │ MongoDB 8     │
│ HTML + JS + Chart.js     │ ◀───────────── │ Spring Boot 4 · Java 21  │ ◀───────── │ leads, ventas │
└──────────────────────────┘                └──────────────────────────┘            └───────────────┘
```

- **Cliente** (`web/`): `index.html`, `app.js` y `estilo.css`. Pide los datos con `fetch` y dibuja los gráficos.
- **Servidor** (`api/`): Spring Boot con los paquetes `controller`, `service`, `repository`, `model`, `dto` y `config`.
  Los cálculos los hace MongoDB con *aggregation pipelines*, como `$match`, `$group`, `$unwind`, `$lookup`, `$facet` y `$median`.
  Están en `service/Pipelines.java` y se pueden pegar tal cual en la pestaña *Aggregations* de MongoDB Compass.
- **ETL** (`etl/`): Python. Saca una foto fija del CRM y del ERP, limpia y anonimiza los datos y los guarda en `datos/*.json`.
  Si encuentra un monto, un teléfono, un DNI, un correo o el nombre de la empresa, se detiene sin escribir nada.

### Colecciones

| Colección | Un documento es… | Campos principales |
|---|---|---|
| `leads` | un cliente que escribió por WhatsApp | `nombre`, `llegada`, `mes`, `dia`, `hora`, `origen{tipo,plataforma,anuncio}`, `capi{periodo}`, `etapa`, `calificado`, `asesora`, `compro`, `diasHastaCompra` |
| `ventas` | un comprobante del ERP | `fecha`, `mes`, `dia`, `hora`, `tipo`, `cliente`, `leadId`, `categorias`, `items[{producto,categoria,cantidad}]` |

### API

| Método | Ruta | Qué devuelve |
|---|---|---|
| POST | `/api/ingresar` | token (clave del dashboard) |
| GET | `/api/salud` | versión de MongoDB y número de documentos (libre) |
| GET | `/api/resumen?mes=2026-10` | leads, de anuncios, listos, compraron, ventas por 100 leads |
| GET | `/api/embudo` | escribieron → interés → listos → compraron |
| GET | `/api/compras/dias` · `/api/compras/calor` · `/api/compras/categorias` | cuándo y qué compran |
| GET | `/api/capi/comparativo` | jul–ago (antes) contra sep–oct (con CAPI) |
| GET | `/api/anuncios/top` · `/api/asesoras` | origen de los leads y desempeño |
| GET | `/api/clientes?compro=true&q=ana&pagina=1` | tabla de clientes (usa `$lookup` con ventas) |
| GET | `/api/hallazgos` | frases automáticas con los números del mes |

## Correrlo en tu PC

Necesitas Java 21+, Maven, Python 3.11+ y MongoDB 8 en `127.0.0.1:27017`.

```bash
# 1. Datos de ejemplo en MongoDB
pip install -r etl/requirements.txt
python -m etl.cargar --db bi_leads --ejemplo

# 2. Servidor (puerto 8080). La clave local por defecto es bi2026.
cd api && mvn spring-boot:run

# 3. Cliente (puerto 8081), en otra terminal
python -m http.server 8081 -d web
```

Abre http://localhost:8081. Las pruebas: `python -m pytest etl` y `cd api && mvn test`.
`mvn test` usa la base `bi_leads_test` y la llena sola con los datos de ejemplo.

## Despliegue en el VPS (Docker)

```bash
git clone https://github.com/DBLTECH2026/bi-leads.git /opt/bi-leads
cd /opt/bi-leads
cp .env.ejemplo .env            # y cambiar las claves
docker compose up -d --build    # mongo + api + web
./scripts/cargar-datos.sh       # mongoimport de datos/*.json (copiados por scp)
cp caddy/bi-leads.caddy /opt/caddy-extra/ && docker exec sirac-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

- DNS: registros **A** y **AAAA** de `bi-leads` hacia el VPS.
- MongoDB no se abre a internet: escucha en `127.0.0.1:27018` del VPS.
  **MongoDB Compass** se conecta por **túnel SSH**: pestaña *Proxy/SSH*, servidor del VPS, llave SSH y destino `mongodb://usuario:clave@127.0.0.1:27018/?authSource=admin`.
- Para actualizar: `./scripts/desplegar.sh`.

## Créditos

Luis López Lapa · Inteligencia de Negocios, UTP 2026.
