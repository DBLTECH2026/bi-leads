"""Capturas reales del navegador para el video (Chrome sin ventana, 1920x1080).

Uso:  python video/capturar.py [vivo] [local] [github] [api]
Guarda en video/crudo/navegador/. Las imágenes de página completa sirven para animar el desplazamiento.
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

SALIDA = Path(__file__).resolve().parent / "crudo" / "navegador"
VIVO = "https://bi.dbltech.tech"
LOCAL = "http://localhost:8081"
REPO = "https://github.com/DBLTECH2026/bi-leads"


async def dashboard(ctx, base, prefijo):
    pg = await ctx.new_page()
    await pg.goto(base + "/")
    await pg.wait_for_timeout(4500)
    await pg.screenshot(path=SALIDA / f"{prefijo}-01-resumen.png")
    await pg.screenshot(path=SALIDA / f"{prefijo}-01-resumen-completo.png", full_page=True)
    # Filtros: menú de meses abierto
    await pg.click(".filtro[data-filtro=meses] .filtro-boton")
    await pg.wait_for_timeout(600)
    await pg.screenshot(path=SALIDA / f"{prefijo}-02-menu-meses.png")
    await pg.click(".filtro[data-filtro=meses] .filtro-boton")
    # Filtros rápidos abiertos y luego «Mes con más ventas»
    await pg.click(".filtro[data-filtro=rapidos] .filtro-boton")
    await pg.wait_for_timeout(600)
    await pg.screenshot(path=SALIDA / f"{prefijo}-03-filtros-rapidos.png")
    await pg.click("[data-rapido=mejor-mes]")
    await pg.wait_for_timeout(3500)
    await pg.screenshot(path=SALIDA / f"{prefijo}-04-mejor-mes.png")
    # Octubre (la vista del guion)
    await pg.goto(base + "/?meses=2026-10#mes")
    await pg.wait_for_timeout(4000)
    await pg.screenshot(path=SALIDA / f"{prefijo}-05-octubre.png")
    await pg.screenshot(path=SALIDA / f"{prefijo}-05-octubre-completo.png", full_page=True)
    # Filtros combinados: salón + fin de semana
    await pg.goto(base + "/?rubros=SAL%C3%93N&dias=6,7&compro=true#mes")
    await pg.wait_for_timeout(4000)
    await pg.screenshot(path=SALIDA / f"{prefijo}-06-combinados.png")
    for tab in ["capi", "clientes", "hallazgos"]:
        await pg.goto(base + f"/?meses=2026-10#{tab}")
        await pg.wait_for_timeout(3500)
        await pg.screenshot(path=SALIDA / f"{prefijo}-07-{tab}.png")
    await pg.close()


async def github(ctx):
    pg = await ctx.new_page()
    await pg.goto(REPO)
    await pg.wait_for_timeout(3000)
    await pg.screenshot(path=SALIDA / "gh-01-repo.png")
    await pg.screenshot(path=SALIDA / "gh-01-repo-completo.png", full_page=True)
    await pg.goto(REPO + "/blob/main/.gitignore")
    await pg.wait_for_timeout(3000)
    await pg.screenshot(path=SALIDA / "gh-02-gitignore.png")
    await pg.goto(REPO + "/tree/main/api/src/main/java/pe/luislopez/bi")
    await pg.wait_for_timeout(3000)
    await pg.screenshot(path=SALIDA / "gh-03-paquetes.png")
    await pg.close()


async def api_json(ctx):
    pg = await ctx.new_page()
    await pg.goto("http://localhost:8080/api/salud")
    await pg.wait_for_timeout(1000)
    await pg.screenshot(path=SALIDA / "api-01-salud-local.png")
    await pg.goto(VIVO + "/api/salud")
    await pg.wait_for_timeout(1500)
    await pg.screenshot(path=SALIDA / "api-02-salud-vivo.png")
    await pg.close()


async def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1, locale="es-PE")
        partes = set(sys.argv[1:]) or {"vivo", "local", "github", "api"}
        if "vivo" in partes:
            await dashboard(ctx, VIVO, "vivo")
        if "local" in partes:
            await dashboard(ctx, LOCAL, "local")
        if "github" in partes:
            await github(ctx)
        if "api" in partes:
            await api_json(ctx)
        await b.close()
    print("\n".join(sorted(f.name for f in SALIDA.iterdir())))


asyncio.run(main())
