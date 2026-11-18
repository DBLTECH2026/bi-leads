"""Arma el video final con la voz de Luis.

Uso:  python video/armar.py [--solo 5] [--rapido]
Entradas: video/voz/NN.wav + escenas.json (alinear.py), video/subtitulos.json, video/crudo/* (grabaciones reales).
Salida:   video/salida/luis-lopez-bi.mp4 (1920x1080, 30 fps)
"""
import argparse
import html
import json
import math
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CRUDO = AQUI / "crudo"
TOMAS = CRUDO / "tomas"
SALIDA = AQUI / "salida"
W, H, FPS = 1920, 1080, 30
PAUSA = 0.45          # silencio después de cada escena
VERDE, VERDE_NEON, NEGRO = (22, 163, 74), (74, 222, 128), (10, 10, 10)
FUENTES = Path("C:/Windows/Fonts")
NAV = CRUDO / "navegador"
VIVO, LOCAL, GH = "https://bi.dbltech.tech", "http://localhost:8081", "https://github.com/DBLTECH2026/bi-leads"


def fuente(nombre, tam):
    return ImageFont.truetype(str(FUENTES / nombre), tam)


# ---------------------------------------------------------------- guion visual (qué se ve en cada escena)
def toma(tipo, peso=1.0, **k):
    return {"tipo": tipo, "peso": peso, **k}


ESCENAS_VIDEO = {
    1: [toma("imagen", 1.3, src=NAV / "vivo-01-resumen.png", url=VIVO),
        toma("imagen", 1, src=NAV / "vivo-04-mejor-mes.png", url=VIVO + "/?meses=2026-08"),
        toma("imagen", 1, src=NAV / "vivo-07-capi.png", url=VIVO + "/?meses=2026-10#capi"),
        toma("imagen", 1, src=NAV / "vivo-07-hallazgos.png", url=VIVO + "/?meses=2026-10#hallazgos")],
    2: [toma("lamina", 1, nombre="preguntas")],
    3: [toma("lamina", 2, nombre="arquitectura"),
        toma("imagen", 1, src=NAV / "gh-03-paquetes.png", url=GH + "/tree/main/api/src/main/java/pe/luislopez/bi")],
    4: [toma("lamina", 1.1, nombre="etl"), toma("terminal", 1, cast="04-etl")],
    5: [toma("video", 1, src=CRUDO / "compass" / "05-compass-local.mp4",
             tramos=[(4, 9.5), (11, 14), (21, 28), (47, 57), (70, 77), (84, 93.4)])],
    6: [toma("codigo", 1, archivo="api/src/main/java/pe/luislopez/bi/model/Lead.java", desde="@Data", lineas=24),
        toma("codigo", 0.7, archivo="api/src/main/java/pe/luislopez/bi/repository/LeadRepository.java",
             desde="public interface", lineas=12),
        toma("codigo", 1, archivo="api/src/main/java/pe/luislopez/bi/service/Pipelines.java",
             desde="    public static final String VENTAS_POR_DIA", lineas=10),
        toma("codigo", 1, archivo="api/src/main/java/pe/luislopez/bi/service/Filtros.java",
             desde="    /** $match para la colección leads", lineas=30),
        toma("codigo", 0.8, archivo="api/src/main/java/pe/luislopez/bi/controller/BiController.java",
             desde="@RestController", lineas=26),
        toma("terminal", 0.8, cast="06-pruebas")],
    7: [toma("codigo", 1.1, archivo="web/app.js", desde="  // ---------- Filtros: estado, URL y API", lineas=30),
        toma("imagen", 1, src=NAV / "local-01-resumen.png", url=LOCAL),
        toma("imagen", 0.9, src=NAV / "local-03-filtros-rapidos.png", url=LOCAL)],
    8: [toma("imagen", 1.6, src=NAV / "gh-01-repo-completo.png", url=GH, mov="bajar"),
        toma("imagen", 0.7, src=NAV / "gh-02-gitignore.png", url=GH + "/blob/main/.gitignore")],
    9: [toma("imagen", 0.8, src=CRUDO / "09-dns" / "1-zona-dns.jpg", url="https://hpanel.hostinger.com/domain/dbltech.tech/dns"),
        toma("imagen", 0.8, src=CRUDO / "09-dns" / "2-registro-a.jpg", url="https://hpanel.hostinger.com/domain/dbltech.tech/dns"),
        toma("imagen", 0.8, src=CRUDO / "09-dns" / "3-registro-aaaa.jpg", url="https://hpanel.hostinger.com/domain/dbltech.tech/dns"),
        toma("imagen", 0.8, src=CRUDO / "09-dns" / "4-registros-creados.jpg", url="https://hpanel.hostinger.com/domain/dbltech.tech/dns"),
        toma("terminal", 1, cast="09-dns")],
    10: [toma("terminal", 1, cast="10-despliegue")],
    11: [toma("terminal", 1, cast="11-carga")],
    12: [toma("terminal", 2, cast="12-contenedores"), toma("terminal", 1, cast="12b-caddy")],
    13: [toma("video", 1, src=CRUDO / "compass" / "13-compass-vps.mp4",
              tramos=[(7, 11), (15, 21), (31, 36), (43, 53)])],
    14: [toma("imagen", 0.8, src=NAV / "vivo-02-menu-meses.png", url=VIVO),
         toma("imagen", 0.8, src=NAV / "vivo-03-filtros-rapidos.png", url=VIVO),
         toma("imagen", 1, src=NAV / "vivo-04-mejor-mes.png", url=VIVO + "/?meses=2026-08"),
         toma("imagen", 1.7, src=NAV / "vivo-05-octubre-completo.png", url=VIVO + "/?meses=2026-10", mov="bajar"),
         toma("imagen", 0.8, src=NAV / "vivo-06-combinados.png", url=VIVO + "/?rubros=SALÓN&dias=6,7&compro=true"),
         toma("imagen", 1.1, src=NAV / "vivo-07-capi.png", url=VIVO + "/?meses=2026-10#capi"),
         toma("imagen", 0.6, src=NAV / "vivo-07-clientes.png", url=VIVO + "/?meses=2026-10#clientes"),
         toma("imagen", 0.9, src=NAV / "vivo-07-hallazgos.png", url=VIVO + "/?meses=2026-10#hallazgos")],
    15: [toma("lamina", 1, nombre="cierre")],
}


# ---------------------------------------------------------------- utilidades de codificación
def codificador(destino: Path):
    return subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(destino)],
        stdin=subprocess.PIPE)


def escribir(destino: Path, cuadros):
    p = codificador(destino)
    for img in cuadros:
        p.stdin.write(img.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit(f"ffmpeg falló en {destino}")


def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def fondo():
    """Fondo negro con un halo verde muy sutil (marca Luis López · BI)."""
    base = Image.new("RGB", (W, H), NEGRO)
    halo = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(halo)
    for r in range(900, 0, -30):
        d.ellipse((W - r, -r // 2, W + r, r), fill=int(26 * (1 - r / 900)))
    verde = Image.new("RGB", (W, H), (12, 60, 30))
    return Image.composite(verde, base, halo)


FONDO = None


# ---------------------------------------------------------------- tomas: imagen con ventana de navegador
def ventana_navegador(captura: Image.Image, url: str, alto_visible=None):
    """Compone la captura dentro de una ventana de navegador con su barra de dirección."""
    ancho = 1760
    esc = ancho / captura.width
    cont = captura.resize((ancho, round(captura.height * esc)), Image.LANCZOS)
    barra = 46
    visible = alto_visible or cont.height
    alto = barra + visible
    x0, y0 = (W - ancho) // 2, max(16, (H - alto) // 2)
    lienzo = FONDO.copy()
    sombra = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sombra).rounded_rectangle((x0 + 6, y0 + 10, x0 + ancho + 6, y0 + alto + 10), 16, fill=110)
    lienzo.paste((0, 0, 0), (0, 0, W, H), sombra)
    d = ImageDraw.Draw(lienzo)
    d.rounded_rectangle((x0, y0, x0 + ancho, y0 + alto), 14, fill=(241, 241, 243))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((x0 + 18 + i * 22, y0 + 17, x0 + 30 + i * 22, y0 + 29), fill=c)
    d.rounded_rectangle((x0 + 110, y0 + 9, x0 + ancho - 110, y0 + 37), 14, fill=(255, 255, 255))
    if url.startswith("https"):  # candado dibujado
        d.rounded_rectangle((x0 + 132, y0 + 22, x0 + 146, y0 + 33), 2, fill=(90, 90, 96))
        d.arc((x0 + 134, y0 + 14, x0 + 144, y0 + 28), 180, 360, fill=(90, 90, 96), width=2)
    else:
        d.ellipse((x0 + 132, y0 + 16, x0 + 146, y0 + 30), outline=(90, 90, 96), width=2)
    d.text((x0 + 158, y0 + 11), url, font=fuente("segoeui.ttf", 19), fill=(40, 40, 46))
    return lienzo, cont, (x0, y0 + barra, ancho, visible)


def toma_imagen(t, dur, destino):
    cap = Image.open(t["src"]).convert("RGB")
    n = max(1, round(dur * FPS))
    if t.get("mov") == "bajar":
        lienzo, cont, (x, y, ancho, visible) = ventana_navegador(cap, t["url"], alto_visible=990)
        recorrido = max(0, cont.height - visible)

        def cuadros():
            for f in range(n):
                p = suave((f / max(1, n - 1) - 0.12) / 0.76)
                off = round(recorrido * p)
                img = lienzo.copy()
                img.paste(cont.crop((0, off, ancho, off + visible)), (x, y))
                ImageDraw.Draw(img).rectangle((x, y + visible - 1, x + ancho, y + visible), fill=(220, 220, 225))
                yield img
        escribir(destino, cuadros())
        return
    if t.get("url"):
        lienzo, cont, (x, y, ancho, visible) = ventana_navegador(cap, t["url"])
        lienzo.paste(cont, (x, y))
        base = lienzo
    else:
        base = cap.resize((W, H), Image.LANCZOS)
    cx, cy = t.get("foco", (W / 2, H / 2))

    def cuadros():
        for f in range(n):
            z = 1 + 0.055 * suave(f / max(1, n - 1))
            cw, ch = W / z, H / z
            x0 = min(max(0, cx - cw / 2), W - cw)
            y0 = min(max(0, cy - ch / 2), H - ch)
            yield base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    escribir(destino, cuadros())


# ---------------------------------------------------------------- tomas: láminas y código (HTML → PNG)
CSS_BASE = """
@font-face { font-family: Inter; src: url('{fuentes}/inter.woff2'); font-weight: 100 900; }
@font-face { font-family: Jakarta; src: url('{fuentes}/jakarta.woff2'); font-weight: 200 800; }
* { box-sizing: border-box; margin: 0; }
body { width: 1920px; height: 1080px; overflow: hidden; font-family: Inter, sans-serif; color: #f4f4f5;
  background: radial-gradient(1100px 700px at 100% 0%, #0f3d22 0%, #0a0a0a 60%); }
h1, h2, .num { font-family: Jakarta, sans-serif; }
.marca { position: absolute; top: 56px; left: 80px; display: flex; align-items: center; gap: 12px; font-family: Jakarta; font-weight: 800; font-size: 26px; }
.logo { width: 46px; height: 46px; border-radius: 12px; background: #16a34a; color: #0a0a0a; display: grid; place-items: center; }
.logo svg { width: 26px; height: 26px; }
.chip { background: #16a34a; color: #0a0a0a; font-size: 15px; font-weight: 800; padding: 3px 9px; border-radius: 7px; }
.pie { position: absolute; bottom: 150px; left: 80px; right: 80px; color: #a1a1aa; font-size: 22px; display: flex; justify-content: space-between; }
svg { stroke-width: 2; }
"""

MARCA = '<div class="marca"><span class="logo"><i data-lucide="chart-no-axes-combined"></i></span>Luis López <span class="chip">BI</span></div>'

LAMINAS = {
    "preguntas": f"""{MARCA}
<style>
.cont {{ position: absolute; top: 190px; left: 80px; right: 80px; }}
h1 {{ font-size: 72px; font-weight: 800; letter-spacing: -1.5px; }}
h1 b {{ color: #4ade80; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 60px; }}
.p {{ background: #111113; border: 1px solid #27272a; border-radius: 22px; padding: 36px 40px; display: flex; gap: 26px; align-items: center; }}
.ic {{ width: 84px; height: 84px; flex: none; border-radius: 20px; background: #16a34a; color: #0a0a0a; display: grid; place-items: center; }}
.ic svg {{ width: 44px; height: 44px; }}
.p span {{ font-size: 36px; font-weight: 600; line-height: 1.25; }}
.p small {{ display: block; color: #4ade80; font-size: 20px; font-weight: 700; letter-spacing: 2px; margin-bottom: 6px; }}
</style>
<div class="cont"><h1>Cuatro preguntas <b>de negocio</b></h1>
<div class="grid">
 <div class="p"><div class="ic"><i data-lucide="users"></i></div><span><small>01</small>¿Cuántos escribieron y cuántos compraron?</span></div>
 <div class="p"><div class="ic"><i data-lucide="armchair"></i></div><span><small>02</small>¿Qué compraron: barbería, salón o spa?</span></div>
 <div class="p"><div class="ic"><i data-lucide="calendar-days"></i></div><span><small>03</small>¿Qué mes, qué día y a qué hora compran más?</span></div>
 <div class="p"><div class="ic"><i data-lucide="trending-up"></i></div><span><small>04</small>¿Con Meta CAPI llegan mejores clientes?</span></div>
</div></div>
<div class="pie"><span>Datos reales anonimizados · julio a octubre 2026 · sin montos</span><span>bi.dbltech.tech</span></div>""",

    "arquitectura": f"""{MARCA}
<style>
h1 {{ position: absolute; top: 170px; left: 80px; font-size: 64px; font-weight: 800; letter-spacing: -1.2px; }}
h1 b {{ color: #4ade80; }}
.sub {{ position: absolute; top: 262px; left: 80px; font-size: 28px; color: #a1a1aa; }}
.fila {{ position: absolute; top: 380px; left: 80px; right: 80px; display: grid; grid-template-columns: 1fr 120px 1.25fr 120px 1fr; align-items: stretch; }}
.caja {{ background: #111113; border: 1px solid #27272a; border-radius: 24px; padding: 38px 36px; }}
.caja.centro {{ border-color: #16a34a; box-shadow: 0 0 0 1px #16a34a inset; }}
.cab {{ display: flex; align-items: center; gap: 18px; }}
.ic {{ width: 72px; height: 72px; border-radius: 18px; background: #16a34a; color: #0a0a0a; display: grid; place-items: center; }}
.ic svg {{ width: 38px; height: 38px; }}
h2 {{ font-size: 38px; font-weight: 800; }}
.tag {{ color: #4ade80; font-size: 22px; font-weight: 700; margin-top: 4px; }}
ul {{ margin-top: 28px; padding-left: 0; list-style: none; display: grid; gap: 14px; }}
li {{ font-size: 25px; color: #e4e4e7; display: flex; gap: 12px; align-items: center; }}
li::before {{ content: ""; width: 8px; height: 8px; border-radius: 50%; background: #4ade80; flex: none; }}
code {{ font-family: 'Cascadia Mono', Consolas, monospace; color: #4ade80; font-size: 23px; }}
.flecha {{ display: grid; place-items: center; color: #4ade80; }}
.flecha svg {{ width: 70px; height: 70px; }}
.flecha span {{ font-size: 20px; color: #a1a1aa; margin-top: -30px; }}
</style>
<h1>Arquitectura <b>cliente-servidor</b></h1>
<div class="sub">La misma del ejemplo de la PokeAPI del curso, pero con nuestra propia base de datos</div>
<div class="fila">
 <div class="caja"><div class="cab"><div class="ic"><i data-lucide="monitor"></i></div><div><h2>Cliente</h2><div class="tag">web/ · puerto 8081</div></div></div>
  <ul><li>HTML + JavaScript</li><li>Chart.js para los gráficos</li><li>pide los datos con <code>fetch</code></li><li>filtros en la URL</li></ul></div>
 <div class="flecha"><i data-lucide="arrow-right-left"></i><span>JSON</span></div>
 <div class="caja centro"><div class="cab"><div class="ic"><i data-lucide="server"></i></div><div><h2>API Spring Boot</h2><div class="tag">api/ · Java 21 · puerto 8080</div></div></div>
  <ul><li><code>controller</code> · endpoints REST</li><li><code>service</code> · aggregation pipelines</li><li><code>repository</code> · Spring Data</li><li><code>model</code> · <code>dto</code></li></ul></div>
 <div class="flecha"><i data-lucide="arrow-right-left"></i><span>driver</span></div>
 <div class="caja"><div class="cab"><div class="ic"><i data-lucide="database"></i></div><div><h2>MongoDB 8</h2><div class="tag">base bi_leads</div></div></div>
  <ul><li>colección <code>leads</code></li><li>colección <code>ventas</code></li><li>documentos JSON</li><li><code>$match</code> · <code>$group</code> · <code>$lookup</code></li></ul></div>
</div>
<div class="pie"><span>Luis López Lapa · Inteligencia de Negocios 2026</span><span>github.com/DBLTECH2026/bi-leads</span></div>""",

    "etl": f"""{MARCA}
<style>
h1 {{ position: absolute; top: 170px; left: 80px; font-size: 64px; font-weight: 800; letter-spacing: -1.2px; }}
h1 b {{ color: #4ade80; }}
.flujo {{ position: absolute; top: 330px; left: 80px; right: 80px; display: grid; grid-template-columns: 1fr 90px 1.5fr 90px 1fr; align-items: center; }}
.col {{ display: grid; gap: 22px; }}
.caja {{ background: #111113; border: 1px solid #27272a; border-radius: 22px; padding: 28px 30px; display: flex; gap: 18px; align-items: center; }}
.ic {{ width: 64px; height: 64px; flex: none; border-radius: 16px; background: #16a34a; color: #0a0a0a; display: grid; place-items: center; }}
.ic svg {{ width: 34px; height: 34px; }}
h2 {{ font-size: 32px; font-weight: 800; }}
.caja small {{ display: block; color: #a1a1aa; font-size: 21px; margin-top: 4px; }}
.etl {{ border-color: #16a34a; flex-direction: column; align-items: flex-start; }}
.reglas {{ display: grid; gap: 12px; margin-top: 8px; }}
.regla {{ display: flex; gap: 12px; align-items: center; font-size: 24px; }}
.regla svg {{ width: 26px; height: 26px; color: #4ade80; flex: none; }}
.flecha {{ display: grid; place-items: center; color: #4ade80; }}
.flecha svg {{ width: 60px; height: 60px; }}
.control {{ position: absolute; bottom: 215px; left: 80px; right: 80px; display: flex; gap: 22px; }}
.dato {{ background: #16a34a; color: #0a0a0a; border-radius: 18px; padding: 18px 28px; font-size: 26px; font-weight: 700; }}
.dato b {{ font-family: Jakarta; font-size: 40px; font-weight: 800; margin-right: 10px; }}
</style>
<h1>Datos reales, <b>anonimizados</b></h1>
<div class="flujo">
 <div class="col">
  <div class="caja"><div class="ic"><i data-lucide="message-circle"></i></div><div><h2>CRM</h2><small>clientes de WhatsApp</small></div></div>
  <div class="caja"><div class="ic"><i data-lucide="receipt"></i></div><div><h2>ERP</h2><small>boletas y facturas</small></div></div>
 </div>
 <div class="flecha"><i data-lucide="arrow-right"></i></div>
 <div class="caja etl"><div style="display:flex;gap:18px;align-items:center"><div class="ic"><i data-lucide="shield-check"></i></div><div><h2>ETL en Python</h2><small>foto de julio a octubre 2026</small></div></div>
  <div class="reglas">
   <div class="regla"><i data-lucide="circle-off"></i>sin montos</div>
   <div class="regla"><i data-lucide="circle-off"></i>sin teléfonos, DNI ni correos</div>
   <div class="regla"><i data-lucide="circle-off"></i>sin el nombre de la empresa</div>
   <div class="regla"><i data-lucide="user-round"></i>asesoras con seudónimo</div>
  </div></div>
 <div class="flecha"><i data-lucide="arrow-right"></i></div>
 <div class="col">
  <div class="caja"><div class="ic"><i data-lucide="file-json"></i></div><div><h2>leads.json</h2><small>21 587 clientes</small></div></div>
  <div class="caja"><div class="ic"><i data-lucide="file-json"></i></div><div><h2>ventas.json</h2><small>593 comprobantes</small></div></div>
 </div>
</div>
<div class="control"><div class="dato"><b>4 207</b>leads en octubre ✓</div><div class="dato"><b>130</b>ventas en octubre ✓</div></div>
<div class="pie"><span>Si encuentra un dato prohibido o los totales no cuadran, no guarda nada</span><span>etl/</span></div>""",

    "cierre": f"""{MARCA}
<style>
h1 {{ position: absolute; top: 170px; left: 80px; font-size: 72px; font-weight: 800; letter-spacing: -1.5px; }}
h1 b {{ color: #4ade80; }}
.pasos {{ position: absolute; top: 300px; left: 80px; right: 80px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; }}
.paso {{ background: #111113; border: 1px solid #27272a; border-radius: 22px; padding: 32px; }}
.ic {{ width: 70px; height: 70px; border-radius: 18px; background: #16a34a; color: #0a0a0a; display: grid; place-items: center; margin-bottom: 18px; }}
.ic svg {{ width: 38px; height: 38px; }}
.paso h2 {{ font-size: 34px; font-weight: 800; }}
.paso p {{ font-size: 25px; color: #d4d4d8; margin-top: 8px; line-height: 1.35; }}
.datos {{ position: absolute; top: 600px; left: 80px; right: 80px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
.d {{ border: 1px solid #16a34a; border-radius: 18px; padding: 22px 26px; }}
.d b {{ display: block; font-family: Jakarta; font-size: 40px; font-weight: 800; color: #4ade80; }}
.d span {{ font-size: 22px; color: #e4e4e7; }}
.links {{ position: absolute; bottom: 205px; left: 80px; display: flex; gap: 40px; font-size: 30px; font-weight: 700; }}
.links span {{ display: flex; gap: 12px; align-items: center; }}
.links svg {{ width: 32px; height: 32px; color: #4ade80; }}
</style>
<h1>En <b>resumen</b></h1>
<div class="pasos">
 <div class="paso"><div class="ic"><i data-lucide="database"></i></div><h2>MongoDB</h2><p>guarda los clientes y las ventas como documentos</p></div>
 <div class="paso"><div class="ic"><i data-lucide="server"></i></div><h2>Spring Boot</h2><p>los convierte en indicadores con aggregation pipelines</p></div>
 <div class="paso"><div class="ic"><i data-lucide="layout-dashboard"></i></div><h2>Dashboard</h2><p>los muestra con filtros inteligentes a quien decide</p></div>
</div>
<div class="datos">
 <div class="d"><b>Agosto</b><span>mes con más ventas</span></div>
 <div class="d"><b>Jueves</b><span>día con más compras</span></div>
 <div class="d"><b>Salón</b><span>casi la mitad de lo vendido</span></div>
 <div class="d"><b>+18 %</b><span>ventas por 100 leads con CAPI</span></div>
</div>
<div class="links"><span><i data-lucide="globe"></i>bi.dbltech.tech</span><span><i data-lucide="github"></i>github.com/DBLTECH2026/bi-leads</span></div>
<div class="pie"><span>Luis López Lapa · Inteligencia de Negocios 2026</span><span>Siguiente paso: arquitectura hexagonal</span></div>""",
}


def pagina(cuerpo: str) -> str:
    fuentes = (RAIZ / "web" / "vendor" / "fuentes").as_uri()
    lucide = (RAIZ / "web" / "vendor" / "lucide.min.js").as_uri()
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS_BASE.replace('{fuentes}', fuentes)}</style>"
            f"</head><body>{cuerpo}<script src='{lucide}'></script><script>lucide.createIcons()</script></body></html>")


def codigo_html(t) -> str:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_for_filename
    ruta = RAIZ / t["archivo"]
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    i = next(n for n, l in enumerate(lineas) if l.startswith(t["desde"]))
    trozo = "\n".join(lineas[i:i + t["lineas"]])
    fmt = HtmlFormatter(style="github-dark", noclasses=True, nowrap=True)
    cuerpo = highlight(trozo, get_lexer_for_filename(ruta.name), fmt)
    numeros = "\n".join(str(n) for n in range(i + 1, i + 1 + t["lineas"]))
    camino = " › ".join(Path(t["archivo"]).parts)
    tam = 26 if t["lineas"] <= 24 else 23
    return f"""
<style>
.editor {{ position: absolute; inset: 70px 110px; background: #0d1117; border: 1px solid #30363d; border-radius: 16px; overflow: hidden; box-shadow: 0 30px 80px rgba(0,0,0,.5); }}
.tabs {{ height: 54px; background: #010409; display: flex; align-items: flex-end; padding-left: 18px; border-bottom: 1px solid #30363d; }}
.tab {{ background: #0d1117; color: #e6edf3; padding: 12px 22px; font-size: 20px; border: 1px solid #30363d; border-bottom: 0; border-top: 2px solid #16a34a; border-radius: 8px 8px 0 0; }}
.ruta {{ color: #8b949e; font-size: 18px; padding: 10px 24px; border-bottom: 1px solid #21262d; }}
.cod {{ display: flex; gap: 24px; padding: 18px 24px; font-family: 'Cascadia Mono', Consolas, monospace; font-size: {tam}px; line-height: 1.5; }}
.num {{ color: #6e7681; text-align: right; white-space: pre; font-family: inherit; }}
pre {{ margin: 0; white-space: pre; color: #e6edf3; font-family: inherit; }}
</style>
<div class="editor"><div class="tabs"><div class="tab">{html.escape(ruta.name)}</div></div>
<div class="ruta">{html.escape(camino)}</div>
<div class="cod"><div class="num">{numeros}</div><pre>{cuerpo}</pre></div></div>"""


def render_html(trabajos):
    """trabajos: lista de (html_cuerpo, destino_png). Usa Chrome sin ventana."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H})
        for cuerpo, destino in trabajos:
            tmp = destino.with_suffix(".html")
            tmp.write_text(pagina(cuerpo), encoding="utf-8")
            pg.goto(tmp.as_uri())
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(destino))
        b.close()


# ---------------------------------------------------------------- tomas: terminal animada desde la grabación real
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def toma_terminal(t, dur, destino):
    cast = json.loads((CRUDO / f"{t['cast']}.cast.json").read_text(encoding="utf-8"))
    eventos = cast["eventos"]
    # Línea de tiempo «mostrable»: tecleo humano y pausas cortas entre salidas
    linea_t, lineas = [], []          # lineas: [prompt, texto, t_inicio, t_fin_tecleo] o [None, texto, t, t]
    t_disp, previo = 0.5, None
    for ev in eventos:
        if ev[1] == "cmd":
            texto, prompt = ev[2], ev[3]
            teclear = min(2.6, max(0.6, len(texto) / 30))
            lineas.append([prompt, texto, t_disp, t_disp + teclear])
            t_disp += teclear + 0.3
            previo = ev[0]
        elif ev[1] == "out":
            gap = 0.0 if previo is None else ev[0] - previo
            t_disp += min(0.45, max(0.012, gap))
            limpio = ANSI.sub("", ev[2]).replace("\t", "    ")
            lineas.append([None, limpio, t_disp, t_disp])
            previo = ev[0]
        elif ev[1] == "fin":
            t_disp += 0.5
    natural = t_disp + 0.8
    factor = min(1.0, (dur - 0.3) / natural)          # si sobra tiempo, se queda quieta al final
    for l in lineas:
        l[2] *= factor
        l[3] *= factor

    mono = fuente("consola.ttf", 23)
    monob = fuente("consolab.ttf", 23)
    alto_linea, x_txt, y_txt = 31, 96, 118
    visibles = (H - 60 - y_txt) // alto_linea
    base = FONDO.copy()
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((60, 40, W - 60, H - 40), 16, fill=(12, 15, 14), outline=(38, 46, 42))
    d.rounded_rectangle((60, 40, W - 60, 88), 16, fill=(22, 27, 25))
    d.rectangle((60, 70, W - 60, 88), fill=(22, 27, 25))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((84 + i * 24, 58, 98 + i * 24, 72), fill=c)
    titulo = cast.get("titulo", "") or "terminal"
    tw = d.textlength(titulo, font=fuente("segoeuib.ttf", 19))
    d.text(((W - tw) / 2, 52), titulo, font=fuente("segoeuib.ttf", 19), fill=(160, 170, 165))
    max_chars = 128

    def cuadros():
        n = max(1, round(dur * FPS))
        for f in range(n):
            tt = f / FPS
            img = base.copy()
            dd = ImageDraw.Draw(img)
            mostrar = []
            for prompt, texto, t0, t1 in lineas:
                if t0 > tt:
                    break
                if prompt is not None:
                    k = len(texto) if tt >= t1 else int(len(texto) * (tt - t0) / max(0.01, t1 - t0))
                    mostrar.append((prompt, texto[:k], tt < t1))
                else:
                    mostrar.append((None, texto, False))
            # cursor parpadeando en una línea de prompt vacía al final (esperando comando)
            for fila, (prompt, texto, tecleando) in enumerate(mostrar[-visibles:]):
                y = y_txt + fila * alto_linea
                if prompt is not None:
                    dd.text((x_txt, y), prompt, font=monob, fill=VERDE_NEON)
                    xx = x_txt + dd.textlength(prompt + " ", font=monob)
                    corto = texto if len(prompt) + len(texto) < max_chars else texto[:max_chars - len(prompt) - 1] + "…"
                    dd.text((xx, y), corto, font=mono, fill=(244, 244, 245))
                    if tecleando and (f // 8) % 2 == 0:
                        cx = xx + dd.textlength(corto, font=mono)
                        dd.rectangle((cx + 2, y + 3, cx + 13, y + 26), fill=VERDE_NEON)
                else:
                    corto = texto if len(texto) < max_chars else texto[:max_chars - 1] + "…"
                    dd.text((x_txt, y), corto, font=mono, fill=(200, 205, 210))
            yield img
    escribir(destino, cuadros())


# ---------------------------------------------------------------- tomas: video de Compass
def toma_video(t, dur, destino):
    partes = "".join(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[p{i}];" for i, (a, b) in enumerate(t["tramos"]))
    total = sum(b - a for a, b in t["tramos"])
    factor = dur / total
    une = "".join(f"[p{i}]" for i in range(len(t["tramos"])))
    filtro = (partes + f"{une}concat=n={len(t['tramos'])}:v=1:a=0[c];"
              f"[c]setpts=PTS*{factor:.4f},crop=1849:1040:0:0,scale={W}:{H}:flags=lanczos,fps={FPS}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(t["src"]), "-filter_complex", filtro, "-map", "[v]",
                    "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    str(destino)], check=True)


# ---------------------------------------------------------------- voz y subtítulos
def normal(p):
    p = unicodedata.normalize("NFKD", p.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in p if not unicodedata.combining(c)))


def preparar_voz(escenas, subs):
    """Recorta tropiezos y deja voz/final/NN.wav. Devuelve {id: (duracion, palabras)}."""
    destino = AQUI / "voz" / "final"
    destino.mkdir(parents=True, exist_ok=True)
    salida = {}
    for e in escenas:
        palabras = e["palabras"]
        ini, fin = 0.0, e["duracion"]
        s = subs[str(e["id"])]
        if "empezar_en" in s:
            objetivo = normal(s["empezar_en"])
            k = next(i for i, w in enumerate(palabras) if normal(w["p"]) == objetivo)
            ini = max(0.0, palabras[k]["t0"] - 0.15)
        if "cortar_desde" in s:
            toks = [normal(x) for x in s["cortar_desde"].split()]
            for i in range(len(palabras) - len(toks) + 1):
                if [normal(w["p"]) for w in palabras[i:i + len(toks)]] == toks:
                    fin = palabras[i]["t0"] - 0.1
                    break
        palabras = [{"t0": w["t0"] - ini, "t1": w["t1"] - ini, "p": w["p"]}
                    for w in palabras if w["t0"] >= ini - 0.01 and w["t1"] <= fin + 0.3]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.2f}", "-to", f"{fin:.2f}",
                        "-i", str(AQUI / "voz" / f"{e['id']:02d}.wav"), str(destino / f"{e['id']:02d}.wav")], check=True)
        salida[e["id"]] = (fin - ini, palabras)
    return salida


def tiempos_subtitulos(texto, palabras, dur):
    """Reparte el texto corregido sobre los tiempos reales de la voz (por proporción de caracteres)."""
    if not palabras:
        return []
    acum, marcas = 0, []
    for w in palabras:
        marcas.append((acum, w["t0"]))
        acum += len(w["p"]) + 1
        marcas.append((acum - 1, w["t1"]))
    total_voz = acum

    def tiempo(frac):
        objetivo = frac * total_voz
        for (c0, t0), (c1, t1) in zip(marcas, marcas[1:]):
            if c0 <= objetivo <= c1:
                return t0 + (t1 - t0) * ((objetivo - c0) / max(1, c1 - c0))
        return marcas[-1][1]

    trozos, linea = [], []
    for p in texto.split():
        linea.append(p)
        largo = len(" ".join(linea))
        if largo >= 44 or (largo >= 22 and re.search(r"[.?!:;]$", p)) or (largo >= 34 and p.endswith(",")):
            trozos.append(" ".join(linea))
            linea = []
    if linea:
        trozos.append(" ".join(linea))
    total, pos, eventos = len(texto), 0, []
    for tr in trozos:
        i = texto.index(tr, pos)
        a, b = tiempo(i / total), tiempo((i + len(tr)) / total)
        eventos.append([a, min(dur, b + 0.3), tr])
        pos = i + len(tr)
    for x, y in zip(eventos, eventos[1:]):
        x[1] = min(x[1], y[0] - 0.02)
    return eventos


def ass_tiempo(s):
    h, r = divmod(max(0.0, s), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def escribir_ass(destino, bloques):
    cab = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Segoe UI,46,&H00FFFFFF,&H00FFFFFF,&H380A0A0A,&H380A0A0A,1,0,0,0,100,100,0,0,3,14,0,2,120,120,46,1
Style: Tag,Segoe UI,30,&H000A0A0A,&H000A0A0A,&H004AA316,&H004AA316,1,0,0,0,100,100,0,0,3,10,0,7,70,70,44,1
Style: Titulo,Segoe UI,84,&H00FFFFFF,&H00FFFFFF,&H140A0A0A,&H140A0A0A,1,0,0,0,100,100,0,0,3,26,0,5,100,100,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    filas = []
    for estilo, a, b, texto in bloques:
        limpio = texto if estilo == "Titulo" else texto.replace("{", "(").replace("}", ")")
        filas.append(f"Dialogue: 0,{ass_tiempo(a)},{ass_tiempo(b)},{estilo},,0,0,0,,{limpio}")
    destino.write_text(cab + "\n".join(filas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- armado
def main():
    global FONDO
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", type=int, help="renderizar solo esta escena (para revisar)")
    a = ap.parse_args()
    FONDO = fondo()
    TOMAS.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(parents=True, exist_ok=True)
    guion = {e["id"]: e for e in json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))}
    escenas = json.loads((AQUI / "voz" / "escenas.json").read_text(encoding="utf-8"))
    subs = json.loads((AQUI / "subtitulos.json").read_text(encoding="utf-8"))
    voz = preparar_voz(escenas, subs)

    # Láminas y código → PNG (una sola sesión de Chrome)
    trabajos = []
    for eid, tomas in ESCENAS_VIDEO.items():
        for k, t in enumerate(tomas):
            if t["tipo"] == "lamina":
                t["png"] = TOMAS / f"lamina-{t['nombre']}.png"
                trabajos.append((LAMINAS[t["nombre"]], t["png"]))
            elif t["tipo"] == "codigo":
                t["png"] = TOMAS / f"codigo-{eid:02d}-{k}.png"
                trabajos.append((codigo_html(t), t["png"]))
    render_html(trabajos)

    ids = [a.solo] if a.solo else sorted(ESCENAS_VIDEO)
    lista = []
    for eid in ids:
        dur_voz, _ = voz[eid]
        dur = dur_voz + PAUSA
        tomas = ESCENAS_VIDEO[eid]
        pesos = sum(t["peso"] for t in tomas)
        clips = []
        for k, t in enumerate(tomas):
            d = dur * t["peso"] / pesos
            destino = TOMAS / f"{eid:02d}-{k}.mp4"
            if t["tipo"] in ("lamina", "codigo"):
                toma_imagen({"src": t["png"]}, d, destino)
            elif t["tipo"] == "imagen":
                toma_imagen(t, d, destino)
            elif t["tipo"] == "terminal":
                toma_terminal(t, d, destino)
            elif t["tipo"] == "video":
                toma_video(t, d, destino)
            clips.append(destino)
        concat = TOMAS / f"{eid:02d}-lista.txt"
        concat.write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
        escena = TOMAS / f"escena-{eid:02d}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                        "-vf", f"fade=in:st=0:d=0.3,fade=out:st={dur - 0.3:.3f}:d=0.3", "-t", f"{dur:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(escena)],
                       check=True)
        lista.append((eid, escena, dur))
        print(f"escena {eid:02d} lista ({dur:.1f} s)", flush=True)

    # Video completo + voz + subtítulos
    (TOMAS / "escenas.txt").write_text("".join(f"file '{e.name}'\n" for _, e, _ in lista), encoding="utf-8")
    mudo = TOMAS / "video-mudo.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(TOMAS / "escenas.txt"),
                    "-c", "copy", str(mudo)], check=True)
    entradas, filtro, bloques, t0 = [], "", [], 0.0
    for n, (eid, _, dur) in enumerate(lista):
        entradas += ["-i", str(AQUI / "voz" / "final" / f"{eid:02d}.wav")]
        filtro += f"[{n}:a]aresample=48000,apad,atrim=0:{dur:.3f},asetpts=PTS-STARTPTS[a{n}];"
        dur_voz, palabras = voz[eid]
        for a_, b_, texto in tiempos_subtitulos(subs[str(eid)]["texto"], palabras, dur_voz):
            bloques.append(("Sub", t0 + a_, t0 + b_, texto))
        if eid == 1:
            bloques.append(("Titulo", 0.3, 4.6, "Luis López · BI\\N{\\fs40}Leads y ventas con MongoDB + Spring Boot"))
        else:
            bloques.append(("Tag", t0 + 0.3, t0 + 4.0, f"{eid:02d} · {guion[eid]['titulo']}"))
        t0 += dur
    filtro += "".join(f"[a{n}]" for n in range(len(lista))) + f"concat=n={len(lista)}:v=0:a=1[voz];"
    filtro += "[voz]highpass=f=80,afftdn=nf=-25,loudnorm=I=-15:TP=-1.5:LRA=11[a]"
    audio = TOMAS / "voz-final.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", filtro, "-map", "[a]",
                    "-ar", "48000", str(audio)], check=True)
    ass = TOMAS / "subtitulos.ass"
    escribir_ass(ass, bloques)
    final = SALIDA / ("luis-lopez-bi.mp4" if not a.solo else f"prueba-escena-{a.solo:02d}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mudo.name, "-i", audio.name,
                    "-vf", "subtitles=subtitulos.ass", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    str(final)], check=True, cwd=TOMAS)
    print(f"LISTO: {final} ({t0:.1f} s)")


if __name__ == "__main__":
    main()
