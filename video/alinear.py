"""Alinea la transcripción (voz/palabras.json) con el guion y corta la voz en un audio por escena.

Uso:  python video/alinear.py video/voz/voz-completa.mp3
Salida: video/voz/01.wav … 15.wav y video/voz/escenas.json (inicio, fin y palabras con tiempo de cada escena).
"""
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ESCENAS = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
NUMEROS = {"4 207": "4207", "21 587": "21587"}


def normal(palabra: str) -> str:
    p = unicodedata.normalize("NFKD", palabra.lower())
    p = "".join(c for c in p if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", p)


def tokens(texto: str) -> list[str]:
    for a, b in NUMEROS.items():
        texto = texto.replace(a, b)
    return [t for t in (normal(x) for x in texto.split()) if t]


def main(audio: Path):
    dichas = json.loads((audio.parent / "palabras.json").read_text(encoding="utf-8"))
    oidas = [normal(w["p"]) for w in dichas]

    guion, escena_de = [], []
    for e in ESCENAS:
        for t in tokens(e["leer"]):
            guion.append(t)
            escena_de.append(e["id"])

    # Cada palabra del guion apunta a la palabra que Whisper oyó (si coinciden)
    pareja = {}
    for bloque in difflib.SequenceMatcher(None, guion, oidas, autojunk=False).get_matching_blocks():
        for k in range(bloque.size):
            pareja[bloque.a + k] = bloque.b + k

    inicios = {}
    for e in ESCENAS:
        indices = [i for i, s in enumerate(escena_de) if s == e["id"]]
        primeras = [pareja[i] for i in indices[:12] if i in pareja]
        if not primeras:
            raise SystemExit(f"No se encontró el inicio de la escena {e['id']}")
        # el primer acierto, corregido por cuántas palabras del guion lo preceden en la escena
        i_guion = next(i for i in indices if i in pareja)
        j = max(0, pareja[i_guion] - (i_guion - indices[0]))
        # Luis a veces improvisa una frase de entrada («Bueno, ahora voy a…»): se retrocede hasta el inicio
        # de la oración (palabra tras un punto), como máximo 12 palabras y sin pisar la escena anterior.
        tope = max(inicios.values()) + 1 if inicios else 0
        k = j
        while k > tope and j - k < 12 and not dichas[k - 1]["p"].endswith((".", "?", "!")):
            k -= 1
        inicios[e["id"]] = k if k > tope and dichas[k - 1]["p"].endswith((".", "?", "!")) else j

    duracion = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(audio)], capture_output=True, text=True).stdout)
    resultado = []
    ids = [e["id"] for e in ESCENAS]
    for n, eid in enumerate(ids):
        j0 = inicios[eid]
        j1 = inicios[ids[n + 1]] if n + 1 < len(ids) else len(dichas)
        t0 = max(0.0, dichas[j0]["t0"] - 0.25)
        t1 = (dichas[j1 - 1]["t1"] + 0.35) if j1 > j0 else t0 + 1
        if n + 1 < len(ids):
            t1 = min(t1, dichas[j1]["t0"] - 0.05)
        t1 = min(t1, duracion)
        palabras = [{"t0": round(w["t0"] - t0, 2), "t1": round(w["t1"] - t0, 2), "p": w["p"]} for w in dichas[j0:j1]]
        destino = audio.parent / f"{eid:02d}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-to", f"{t1:.2f}", "-i", str(audio),
                        "-ac", "1", "-ar", "48000", str(destino)], check=True)
        resultado.append({"id": eid, "inicio": round(t0, 2), "fin": round(t1, 2), "duracion": round(t1 - t0, 2),
                          "palabras": palabras})
        print(f"{eid:02d}  {t0:7.2f} → {t1:7.2f}  ({t1 - t0:5.1f} s)  «{' '.join(w['p'] for w in dichas[j0:j0 + 7])}…»")
    (audio.parent / "escenas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
