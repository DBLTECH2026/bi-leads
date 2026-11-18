"""Guardas de privacidad: si algo de esto aparece, el ETL se detiene y no escribe nada."""
import re

from etl.transformar import tiene_marca

CAMPOS_PROHIBIDOS = ("total", "monto", "precio", "subtotal", "igv", "costo",
                     "telefono", "celular", "dni", "ruc")
CAMPOS_ID = {"_id", "leadId"}  # hashes hex: pueden traer dígitos seguidos por azar
TELEFONO = re.compile(r"(?<!\d)9\d{8}(?!\d)")
DNI = re.compile(r"(?<!\d)\d{8}(?!\d)")
CORREO = re.compile(r"\S@\S")


class DatoProhibido(Exception):
    pass


def _revisar(valor, ruta):
    if isinstance(valor, dict):
        for k, v in valor.items():
            if any(p in k.lower() for p in CAMPOS_PROHIBIDOS):
                raise DatoProhibido(f"campo prohibido: {ruta}{k}")
            if k not in CAMPOS_ID:
                _revisar(v, f"{ruta}{k}.")
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            _revisar(v, f"{ruta}{i}.")
    elif isinstance(valor, str) and (TELEFONO.search(valor) or DNI.search(valor) or CORREO.search(valor) or tiene_marca(valor)):
        raise DatoProhibido(f"valor con forma de teléfono, DNI, correo o marca en {ruta.rstrip('.')}: {valor!r}")


def revisar(documentos):
    for d in documentos:
        _revisar(d, "")
