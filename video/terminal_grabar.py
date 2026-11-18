"""Graba una sesión de terminal REAL: ejecuta cada paso (en el VPS por SSH o en la PC) y guarda
lo que se escribió y lo que respondió, con sus tiempos. Luego video/armar.py lo anima.

Uso:  python video/terminal_grabar.py video/sesiones/despliegue.json
Cada paso: {"ver": "comando que se muestra", "correr": "comando real (si difiere)", "host": "vps"|"pc",
            "cwd": "/opt/bi-leads", "prompt": "...", "solo_ver": false, "puede_fallar": false}
"""
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SSH = ["ssh", "-i", str(Path.home() / ".ssh" / "sirac_vps"), "-o", "BatchMode=yes", "root@2.25.216.93"]
PROMPT_VPS = "root@srv2164565:{cwd}#"
PROMPT_PC = "luis@PC:~/bi-leads$"


def ejecutar(sesion_path: Path):
    sesion = json.loads(sesion_path.read_text(encoding="utf-8"))
    eventos, t0 = [], time.time()
    ahora = lambda: round(time.time() - t0, 3)  # noqa: E731
    for paso in sesion["pasos"]:
        host = paso.get("host", "vps")
        cwd = paso.get("cwd", "/opt/bi-leads")
        prompt = paso.get("prompt") or (PROMPT_VPS.format(cwd=cwd.replace("/root", "~")) if host == "vps" else PROMPT_PC)
        eventos.append([ahora(), "cmd", paso["ver"], prompt])
        print(f"{prompt} {paso['ver']}", flush=True)
        if paso.get("solo_ver"):
            continue
        real = paso.get("correr", paso["ver"])
        if host == "vps":
            args = SSH + ["bash -lc " + shlex.quote(f"cd {cwd} && {real}")]
        else:
            args = ["bash", "-lc", f"cd {shlex.quote(str(RAIZ))} && {real}"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for linea in iter(p.stdout.readline, b""):
            texto = linea.decode("utf-8", "replace").rstrip("\r\n")
            eventos.append([ahora(), "out", texto])
            print("   " + texto, flush=True)
        p.wait()
        eventos.append([ahora(), "fin", p.returncode])
        if p.returncode != 0 and not paso.get("puede_fallar"):
            guardar(sesion, eventos, sesion_path)
            raise SystemExit(f"Falló (código {p.returncode}): {paso['ver']}")
    guardar(sesion, eventos, sesion_path)


def guardar(sesion, eventos, sesion_path: Path):
    destino = RAIZ / "video" / "crudo" / (sesion_path.stem + ".cast.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({"titulo": sesion.get("titulo", ""), "eventos": eventos}, ensure_ascii=False,
                                  indent=0), encoding="utf-8")
    print(f"\nGrabado en {destino}")


if __name__ == "__main__":
    ejecutar(Path(sys.argv[1]))
