"""Datos INVENTADOS para probar el proyecto sin acceso a los datos reales (van al repo público).

Uso:  python -m etl.generar_ejemplo
Fija a propósito: el sábado es el día con más compras y 10 de los 30 leads compran (pruebas de la API).
"""
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bson import json_util

from etl import transformar as t

NOMBRES = ["Ana Torres", "Bruno Díaz", "Carla Ríos", "Diego Paz", "Elena Soto", "Fabio Luna", "Gina Vega",
           "Hugo Lara", "Irene Mora", "Jorge Cano", "Karen Gil", "Luis Ponce", "Marta Ruiz", "Nico Salas",
           "Olga Reyes"]
ANUNCIOS = ["Mobiliario para tu barbería", "Lavacabezas para salón", "Sillones con envío a todo el Perú"]
PRODUCTOS = [("Sillón barbero clásico", "BARBERÍA"), ("Lavacabezas cerámico", "SALÓN"),
             ("Tocador con espejo", "SALÓN"), ("Camilla de spa", "SPA"), ("Secadora profesional", "HERRAMIENTAS")]


def generar():
    r = random.Random(2026)
    leads, ventas = [], []
    meses = [(2026, 7), (2026, 8), (2026, 9), (2026, 10)]
    for i in range(30):
        y, m = meses[i % 4] if i < 16 else (2026, 10)
        llegada = datetime(y, m, 1 + r.randrange(27), 9 + r.randrange(10), tzinfo=t.LIMA)
        compro = i % 3 == 0  # 10 de 30
        anuncio = r.random() < 0.8
        lead = {
            "_id": f"L-ejemplo{i:03d}",
            "nombre": NOMBRES[i % len(NOMBRES)],
            "llegada": llegada.astimezone(timezone.utc),
            **t.campos_fecha(llegada),
            "origen": {"tipo": "anuncio" if anuncio else "directo",
                       "plataforma": r.choice(["facebook", "instagram"]) if anuncio else None,
                       "anuncio": r.choice(ANUNCIOS) if anuncio else None, "clickId": anuncio},
            "capi": {"periodo": t.periodo_capi(llegada), "leadEnviado": compro or r.random() < 0.1},
            "etapa": "VENTA_GANADA" if compro else r.choice(["INTERESADO", "INACTIVO", "LISTO_PARA_COMPRAR"]),
            "calificado": compro or r.random() < 0.2,
            "asesora": f"Asesora {'ABC'[i % 3]}",
            "compro": compro, "primeraCompra": None, "diasHastaCompra": None,
        }
        if compro:
            fecha = llegada + timedelta(days=1 + r.randrange(5))
            # empuja la compra al sábado siguiente para 6 de las 10 ventas
            if len(ventas) < 6:
                fecha += timedelta(days=(5 - fecha.weekday()) % 7)
            lead["primeraCompra"] = fecha.astimezone(timezone.utc)
            lead["diasHastaCompra"] = t.dias_entre(llegada, fecha)
            prod, cat = r.choice(PRODUCTOS)
            ventas.append({
                "_id": f"V-ejemplo{len(ventas):03d}", "fecha": fecha.astimezone(timezone.utc),
                **t.campos_fecha(fecha), "tipo": "boleta", "cliente": lead["nombre"], "canal": "whatsapp",
                "leadId": lead["_id"], "categorias": [cat],
                "items": [{"producto": prod, "categoria": cat, "cantidad": 1 + r.randrange(2)}],
                "capiEnviado": lead["capi"]["periodo"] == "despues"})
        leads.append(lead)
    for j in range(2):  # ventas en tienda, sin chat
        fecha = datetime(2026, 10, 10 + j * 7, 11, tzinfo=t.LIMA)  # 10 y 17 de octubre: sábados
        ventas.append({"_id": f"V-ejemplo{len(ventas):03d}", "fecha": fecha.astimezone(timezone.utc),
                       **t.campos_fecha(fecha), "tipo": "factura", "cliente": "Cliente de tienda", "canal": "otro",
                       "leadId": None, "categorias": ["BARBERÍA"],
                       "items": [{"producto": "Sillón barbero clásico", "categoria": "BARBERÍA", "cantidad": 1}],
                       "capiEnviado": False})
    return leads, ventas


if __name__ == "__main__":
    carpeta = Path(__file__).resolve().parent.parent / "datos" / "ejemplo"
    carpeta.mkdir(parents=True, exist_ok=True)
    leads, ventas = generar()
    for nombre, docs in (("leads", leads), ("ventas", ventas)):
        (carpeta / f"{nombre}.json").write_text(
            json_util.dumps(docs, json_options=json_util.RELAXED_JSON_OPTIONS, ensure_ascii=False, indent=1),
            encoding="utf-8")
    print(f"{len(leads)} leads y {len(ventas)} ventas de ejemplo en {carpeta}")
