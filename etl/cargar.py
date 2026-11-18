"""Carga datos/*.json (o datos/ejemplo/*.json) en MongoDB, reemplazando lo que hubiera.

Uso:  python -m etl.cargar --uri mongodb://127.0.0.1:27017 --db bi_leads [--ejemplo]
"""
import argparse
from pathlib import Path

from bson import json_util
from pymongo import ASCENDING, MongoClient

INDICES = {
    "leads": [[("mes", ASCENDING)], [("compro", ASCENDING), ("mes", ASCENDING)], [("nombre", ASCENDING)]],
    "ventas": [[("mes", ASCENDING)], [("leadId", ASCENDING)]],
}


def cargar(uri: str, db: str, carpeta: Path):
    base = MongoClient(uri)[db]
    for coleccion, indices in INDICES.items():
        docs = json_util.loads((carpeta / f"{coleccion}.json").read_text(encoding="utf-8"))
        base[coleccion].drop()
        base[coleccion].insert_many(docs)
        for campos in indices:
            base[coleccion].create_index(campos)
        print(f"{db}.{coleccion}: {base[coleccion].count_documents({})} documentos")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--uri", default="mongodb://127.0.0.1:27017")
    p.add_argument("--db", default="bi_leads")
    p.add_argument("--ejemplo", action="store_true", help="usar datos/ejemplo (datos inventados)")
    a = p.parse_args()
    raiz = Path(__file__).resolve().parent.parent / "datos"
    cargar(a.uri, a.db, raiz / "ejemplo" if a.ejemplo else raiz)
