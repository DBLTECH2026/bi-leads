"""Funciones puras del ETL: fechas en hora de Lima, rubros, seudónimos y anonimización."""
import hashlib
import re
from datetime import datetime, timedelta, timezone

LIMA = timezone(timedelta(hours=-5), "America/Lima")  # Perú no tiene horario de verano
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# CAPI se activó el 30-ago-2026. Para comparar meses completos: jul-ago = antes, sep-oct = después.
PRIMER_MES_CON_CAPI = (2026, 9)

# Raíces del árbol de categorías del ERP que sí son rubro, en orden de prioridad.
RUBROS = {
    "BARBERÍA": "BARBERÍA",
    "SALÓN": "SALÓN",
    "SPA": "SPA",
    "Calzado": "CALZADO",
    "HERRAMIENTAS Y EQUIPOS": "HERRAMIENTAS",
    "Sillones Temáticos Infantil": "INFANTIL",
    "REPUESTOS": "REPUESTOS",
}
PRIORIDAD = list(RUBROS)


def a_lima(iso_utc: str) -> datetime:
    """'2026-10-01T14:21:55.000Z' (UTC, como lo guarda el CRM) -> datetime en hora de Lima."""
    f = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    if f.tzinfo is None:
        f = f.replace(tzinfo=timezone.utc)
    return f.astimezone(LIMA)


def erp_a_lima(local: str) -> datetime:
    """'2026-10-01 09:21:55' (el ERP guarda hora de Lima sin zona) -> datetime en Lima."""
    return datetime.fromisoformat(local).replace(tzinfo=LIMA)


def campos_fecha(f: datetime) -> dict:
    return {"mes": f.strftime("%Y-%m"), "dia": DIAS[f.weekday()], "diaNum": f.isoweekday(), "hora": f.hour}


def periodo_capi(f: datetime) -> str:
    return "despues" if (f.year, f.month) >= PRIMER_MES_CON_CAPI else "antes"


def raiz(cat_id, padres: dict):
    """Sube por parent_id hasta la raíz. None si la categoría no existe."""
    vistos = set()
    while cat_id in padres and cat_id not in vistos:
        vistos.add(cat_id)
        padre = padres[cat_id]
        if not padre:
            return cat_id
        cat_id = padre
    return None


def elegir_rubro(raices: list, principal, nombres: dict) -> str:
    """Rubro de un producto: el de su categoría principal si es rubro; si no, el de mayor prioridad."""
    if principal in raices and nombres.get(principal) in RUBROS:
        return RUBROS[nombres[principal]]
    candidatos = [nombres.get(r) for r in raices if nombres.get(r) in RUBROS]
    if not candidatos:
        return "OTROS"
    return RUBROS[min(candidatos, key=PRIORIDAD.index)]


def seudonimos(ids) -> dict:
    unicos = sorted({i for i in ids if i is not None})
    return {i: f"Asesora {chr(65 + n)}" for n, i in enumerate(unicos)}


_DIGITOS_LARGOS = re.compile(r"\+?\d[\d\s-]{6,}\d")
_CORREO = re.compile(r"\S*@\S*")


def nombre_limpio(nombre_cliente, nombre_whatsapp) -> str:
    """Nombre visible del cliente. Nunca deja pasar un teléfono o DNI escondido en el nombre."""
    base = (nombre_cliente or "").strip() or (nombre_whatsapp or "").strip()
    if tiene_marca(base):
        return "Sin nombre"
    base = _CORREO.sub(" ", base)
    base = _DIGITOS_LARGOS.sub(" ", base)
    base = re.sub(r"\s+", " ", base).strip(" -.,")
    return base if re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", base) else "Sin nombre"


_MARCA = None


def configurar_marcas(nombres):
    """Nombres de la empresa a ocultar. Llegan de etl/.env.local (MARCAS=...); nunca se escriben en el código."""
    global _MARCA
    alternativas = "|".join(re.escape(n.strip()) for n in nombres if n.strip())
    # (?<![a-z]) evita tocar palabras que solo contienen el nombre, p. ej. «Ultracme»
    _MARCA = re.compile(rf"(?i)(?<![a-z])(?:{alternativas})(?:[\s_-]*(?:group|style|pro))?")


configurar_marcas(["acme"])  # marca de ejemplo por defecto


def sin_marca(texto):
    """Quita el nombre de la empresa de títulos y productos. None si no queda nada útil."""
    if not texto:
        return None
    limpio = re.sub(r"\s+", " ", _MARCA.sub(" ", texto)).strip(" -·|,.:")
    limpio = re.sub(r"(?i)\b(con|de|en|por)$", "", limpio).strip()
    return limpio if re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3}", limpio) else None


def tiene_marca(texto) -> bool:
    return bool(texto and _MARCA.search(texto))


class Hasheador:
    """Ids no reversibles: sha256 con una sal aleatoria de cada corrida."""

    def __init__(self, sal: str):
        self.sal = sal

    def __call__(self, prefijo: str, valor) -> str:
        h = hashlib.sha256(f"{self.sal}|{prefijo}|{valor}".encode()).hexdigest()[:12]
        return f"{prefijo}-{h}"


def dias_entre(desde: datetime, hasta: datetime) -> int:
    return int((hasta - desde).total_seconds() // 86400)
