"""Capturas reales del navegador para el video (Chrome sin ventana, 1920x1080).

Uso:  BI_CLAVE=... python video/capturar.py [vivo] [local] [github] [api]
Guarda en video/crudo/navegador/. Las imágenes de página completa sirven para animar el desplazamiento.
"""
import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

SALIDA = Path(__file__).resolve().parent / "crudo" / "navegador"
VIVO = "https://bi.dbltech.tech"
LOCAL = "http://localhost:8081"
REPO = "https://github.com/DBLTECH2026/bi-leads"


async def dashboard(ctx, base, prefijo, clave):
    pg = await ctx.new_page()
    await pg.goto(base + "/")
    await pg.wait_for_selector("#clave")
    await pg.screenshot(path=SALIDA / f"{prefijo}-00-ingreso.png")
    await pg.fill("#clave", clave)
    await pg.screenshot(path=SALIDA / f"{prefijo}-01-clave.png")
    await pg.click("button[type=submit]")
    await pg.wait_for_timeout(4500)
    await pg.screenshot(path=SALIDA / f"{prefijo}-02-resumen.png")
    await pg.screenshot(path=SALIDA / f"{prefijo}-02-resumen-completo.png", full_page=True)
    for tab in ["capi", "clientes", "hallazgos"]:
        await pg.click(f"button[data-tab={tab}]")
        await pg.wait_for_timeout(3500)
        await pg.screenshot(path=SALIDA / f"{prefijo}-03-{tab}.png")
    await pg.click("button[data-tab=clientes]")
    await pg.click("#f-compro button[data-v=true]")
    await pg.wait_for_timeout(2500)
    await pg.screenshot(path=SALIDA / f"{prefijo}-04-clientes-compraron.png")
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
            await dashboard(ctx, VIVO, "vivo", os.environ["BI_CLAVE"])
        if "local" in partes:
            await dashboard(ctx, LOCAL, "local", "bi2026")  # clave de desarrollo (application.properties)
        if "github" in partes:
            await github(ctx)
        if "api" in partes:
            await api_json(ctx)
        await b.close()
    print("\n".join(sorted(f.name for f in SALIDA.iterdir())))


asyncio.run(main())
