"""Foto fija jul-oct 2026: CRM (leads) + ERP (ventas y rubros) -> datos/leads.json y datos/ventas.json.

Uso:  python -m etl.extraer
Sin montos, sin teléfonos, sin DNI. Asesoras con seudónimo. Si algo falla, no escribe nada.
"""
import secrets
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util

from etl import transformar as t
from etl.fuentes import LOCAL, crm, erp, paginar
from etl.guardas import revisar

DESDE_UTC, HASTA_UTC = "2026-07-01 05:00:00", "2026-11-01 05:00:00"  # 1-jul a 31-oct, hora Lima
DESDE_ERP, HASTA_ERP = "2026-07-01 00:00:00", "2026-11-01 00:00:00"  # el ERP guarda hora Lima
SALIDA = Path(__file__).resolve().parent.parent / "datos"
ETAPAS_CALIFICADAS = {"LISTO_PARA_COMPRAR", "VENTA_GANADA"}


def _en(lista, n=150):  # la maestra del ERP devuelve como máximo 200 filas
    for i in range(0, len(lista), n):
        yield lista[i:i + n]


def extraer_crm():
    chats = paginar(crm, f"""SELECT id, nombre, clienteNombre, creadoEn, etapa, anuncioId, anuncioTitulo,
        anuncioApp, (anuncioCtwaClid IS NOT NULL) AS clid, (capiLeadEn IS NOT NULL) AS capiLead,
        (listoDesde IS NOT NULL) AS listo, asesoraId
        FROM chatvendedor WHERE esGrupo = 0 AND creadoEn >= '{DESDE_UTC}' AND creadoEn < '{HASTA_UTC}'""",
                    tam=500)
    espejo = paginar(crm, f"""SELECT id, erpVentaId, chatId, fecha, (capiEnviadoEn IS NOT NULL) AS capi
        FROM ventacrm WHERE estado <> 'anulada' AND fecha >= '{DESDE_UTC}'""", tam=500)
    return chats, espejo


def extraer_erp():
    ventas = paginar(erp, f"""SELECT id, fecha_venta, tipo_comprobante, cliente_nombre, razon_social
        FROM ventas WHERE estado <> 'anulada' AND fecha_venta >= '{DESDE_ERP}' AND fecha_venta < '{HASTA_ERP}'""")
    ids = [v["id"] for v in ventas]
    detalles = paginar(erp, f"""SELECT id, venta_id, producto_id, producto_nombre, cantidad, cantidad_anulada
        FROM venta_detalles WHERE es_componente = 0 AND venta_id BETWEEN {min(ids)} AND {max(ids)}""")
    detalles = [d for d in detalles if d["venta_id"] in set(ids)]
    categorias = paginar(erp, "SELECT id, parent_id, nombre_categoria FROM categorias WHERE 1=1")
    prods = sorted({d["producto_id"] for d in detalles if d["producto_id"]})
    principal, extra = {}, defaultdict(set)
    for bloque in _en(prods):
        lista = ",".join(map(str, bloque))
        for r in erp(f"SELECT id, categoria_id FROM inventario WHERE id IN ({lista}) LIMIT 500"):
            principal[r["id"]] = r["categoria_id"]
        for r in paginar(erp, f"""SELECT id, inventario_id, categoria_id, es_principal
                FROM categoria_producto WHERE inventario_id IN ({lista})"""):
            extra[r["inventario_id"]].add(r["categoria_id"])
            if r["es_principal"]:
                principal[r["inventario_id"]] = r["categoria_id"]
    return ventas, detalles, categorias, principal, extra


def construir(chats, espejo, ventas, detalles, categorias, principal, extra):
    h = t.Hasheador(secrets.token_hex(16))
    padres = {c["id"]: c["parent_id"] for c in categorias}
    nombres = {c["id"]: c["nombre_categoria"] for c in categorias}
    alias = t.seudonimos(c["asesoraId"] for c in chats)

    def rubro(prod_id):
        cats = {principal.get(prod_id)} | extra.get(prod_id, set())
        raices = [t.raiz(c, padres) for c in cats if c]
        return t.elegir_rubro(raices, t.raiz(principal.get(prod_id), padres), nombres)

    # Compras por chat (cualquier fecha posterior a su llegada, hasta hoy)
    compras_por_chat = defaultdict(list)
    chat_de_venta, capi_de_venta = {}, {}
    for e in espejo:
        capi_de_venta[e["erpVentaId"]] = bool(e["capi"])
        if e["chatId"]:
            chat_de_venta[e["erpVentaId"]] = e["chatId"]
            compras_por_chat[e["chatId"]].append(t.a_lima(e["fecha"]))

    leads = []
    for c in chats:
        llegada = t.a_lima(c["creadoEn"])
        compras = sorted(f for f in compras_por_chat.get(c["id"], []) if f >= llegada)
        compro = bool(compras)
        leads.append({
            "_id": h("L", c["id"]),
            "nombre": t.nombre_limpio(c["clienteNombre"], c["nombre"]),
            "llegada": llegada.astimezone(timezone.utc),
            **t.campos_fecha(llegada),
            "origen": {
                "tipo": "anuncio" if c["anuncioId"] else "directo",
                "plataforma": c["anuncioApp"],
                "anuncio": t.sin_marca(c["anuncioTitulo"]),
                "clickId": bool(c["clid"]),
            },
            "capi": {"periodo": t.periodo_capi(llegada), "leadEnviado": bool(c["capiLead"])},
            "etapa": c["etapa"],
            "calificado": bool(c["listo"]) or c["etapa"] in ETAPAS_CALIFICADAS or compro,
            "asesora": alias.get(c["asesoraId"], "Asistente IA (sin asignar)"),
            "compro": compro,
            "primeraCompra": compras[0].astimezone(timezone.utc) if compro else None,
            "diasHastaCompra": t.dias_entre(llegada, compras[0]) if compro else None,
        })

    lead_de_chat = {c["id"]: h("L", c["id"]) for c in chats}
    items_por_venta = defaultdict(list)
    for d in detalles:
        cant = (d["cantidad"] or 0) - (d["cantidad_anulada"] or 0)
        if cant > 0:
            items_por_venta[d["venta_id"]].append({
                "producto": t.sin_marca(t.nombre_limpio(None, d["producto_nombre"])) or "Producto",
                "categoria": rubro(d["producto_id"]),
                "cantidad": int(cant),
            })

    docs_ventas = []
    for v in ventas:
        fecha = t.erp_a_lima(v["fecha_venta"])
        items = items_por_venta.get(v["id"], [])
        chat = chat_de_venta.get(v["id"])
        docs_ventas.append({
            "_id": h("V", v["id"]),
            "fecha": fecha.astimezone(timezone.utc),
            **t.campos_fecha(fecha),
            "tipo": v["tipo_comprobante"],
            "cliente": t.nombre_limpio(v["cliente_nombre"] or v["razon_social"], None),
            "canal": "whatsapp" if chat else "otro",
            "leadId": lead_de_chat.get(chat),
            "categorias": sorted({i["categoria"] for i in items}),
            "items": items,
            "capiEnviado": capi_de_venta.get(v["id"], False),
        })
    return leads, docs_ventas


def controlar(leads, ventas):
    """Los conteos de octubre deben cuadrar con conteos hechos directo en las bases."""
    oct_leads = crm("""SELECT COUNT(*) n FROM chatvendedor WHERE esGrupo = 0
        AND creadoEn >= '2026-10-01 05:00:00' AND creadoEn < '2026-11-01 05:00:00'""")[0]["n"]
    oct_ventas = erp("""SELECT COUNT(*) n FROM ventas WHERE estado <> 'anulada'
        AND fecha_venta >= '2026-10-01' AND fecha_venta < '2026-11-01'""")[0]["n"]
    mios_l = sum(1 for x in leads if x["mes"] == "2026-10")
    mios_v = sum(1 for x in ventas if x["mes"] == "2026-10")
    print(f"Control octubre: leads {mios_l}/{oct_leads} · ventas {mios_v}/{oct_ventas}")
    if (mios_l, mios_v) != (int(oct_leads), int(oct_ventas)):
        raise SystemExit("Los conteos no cuadran: no se escribe nada.")


def main():
    t.configurar_marcas(LOCAL.get("MARCAS", "").split(","))
    print("Leyendo CRM…")
    chats, espejo = extraer_crm()
    print(f"  {len(chats)} chats, {len(espejo)} ventas espejo")
    print("Leyendo ERP…")
    ventas, detalles, categorias, principal, extra = extraer_erp()
    print(f"  {len(ventas)} ventas, {len(detalles)} líneas, {len(categorias)} categorías")
    leads, docs_ventas = construir(chats, espejo, ventas, detalles, categorias, principal, extra)
    revisar(leads)
    revisar(docs_ventas)
    controlar(leads, docs_ventas)
    SALIDA.mkdir(exist_ok=True)
    for nombre, docs in (("leads", leads), ("ventas", docs_ventas)):
        (SALIDA / f"{nombre}.json").write_text(
            json_util.dumps(docs, json_options=json_util.RELAXED_JSON_OPTIONS, ensure_ascii=False, indent=0),
            encoding="utf-8")
    print(f"OK {datetime.now():%d-%m %H:%M}: {len(leads)} leads y {len(docs_ventas)} ventas en {SALIDA}")


if __name__ == "__main__":
    main()
