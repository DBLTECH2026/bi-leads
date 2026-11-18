"""Clientes de solo lectura para las API de consulta del CRM y del ERP de la empresa.

Direcciones, cabeceras y nombres de las llaves van en etl/.env.local; las llaves, en el archivo que
indica LLAVES_ENV. Nada de eso se guarda en este repo (ver etl/.env.local.ejemplo).
"""
import json
import os
import re
import urllib.error
import urllib.request

from pathlib import Path


def _local() -> dict:
    archivo = Path(__file__).with_name(".env.local")
    if not archivo.exists():
        raise SystemExit("Falta etl/.env.local (copiar etl/.env.local.ejemplo y completarlo)")
    pares = (l.split("=", 1) for l in archivo.read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
    return {k.strip(): v.strip() for k, v in pares}


LOCAL = _local()
RUTA_ENV = LOCAL["LLAVES_ENV"]


def _env(clave: str) -> str:
    texto = open(RUTA_ENV, encoding="utf-8").read()
    m = re.search(rf"^{clave}=\"?(.*?)\"?\s*$", texto, re.M)
    if not m:
        raise SystemExit(f"Falta {clave} en {RUTA_ENV}")
    return m.group(1)


def _post(url: str, cabeceras: dict, sql: str) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps({"sql": sql}).encode(),
        headers={**cabeceras, "content-type": "application/json", "User-Agent": "bi-leads-etl"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{url} -> {e.code}: {e.read().decode()[:500]}")


def _numero(v):
    # La API del CRM serializa los DECIMAL de MySQL como {"s":1,"e":..,"d":[n]}
    return v["d"][0] * v.get("s", 1) if isinstance(v, dict) and "d" in v else v


def crm(sql: str) -> list[dict]:
    d = _post(LOCAL["CRM_URL"], {LOCAL["CRM_CABECERA"]: _env(LOCAL["CRM_LLAVE"])}, sql)
    if "filas" not in d:
        raise SystemExit(f"CRM: {d}")
    return [{k: _numero(v) for k, v in f.items()} for f in d["filas"]]


def erp(sql: str) -> list[dict]:
    d = _post(LOCAL["ERP_URL"], {LOCAL["ERP_CABECERA"]: _env(LOCAL["ERP_LLAVE"])}, sql)
    if "filas" not in d:
        raise SystemExit(f"ERP: {d}")
    return [dict(zip(d["columnas"], f)) for f in d["filas"]]


def paginar(fuente, sql_sin_orden: str, alias_id: str = "id", tam: int = 200) -> list[dict]:
    """Recorre por id ascendente, de `tam` en `tam` (las maestras limitan las filas por consulta).

    `sql_sin_orden` debe tener un WHERE y exponer la columna `alias_id` en el SELECT.
    """
    filas, ultimo = [], 0
    while True:
        lote = fuente(f"{sql_sin_orden} AND {alias_id} > {ultimo} ORDER BY {alias_id} LIMIT {tam}")
        filas += lote
        if len(lote) < tam:
            return filas
        ultimo = lote[-1][alias_id.split(".")[-1]]
