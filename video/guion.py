"""Guion del video de Luis López · BI: una sola fuente para guion.md, guion.json (montaje) y el Word para leer.

Uso:  python video/guion.py [carpeta_del_word]
"""
import json
import sys
from pathlib import Path

ESCENAS = [
    {
        "id": 1, "titulo": "Presentación",
        "pantalla": "El dashboard terminado en https://bi.dbltech.tech: recorrido rápido por las cuatro pestañas y los filtros.",
        "leer": "Hola, soy Luis López Lapa. En este video les presento mi proyecto de inteligencia de negocios, "
                "hecho con MongoDB y una arquitectura cliente-servidor. Trabajé con datos reales de una empresa "
                "peruana que vende muebles para barberías, salones y spas, donde casi todas las ventas empiezan con "
                "un mensaje de WhatsApp. Por privacidad no muestro el nombre de la empresa. Lo que van a ver es un "
                "dashboard publicado en internet que convierte esos mensajes en decisiones de negocio.",
    },
    {
        "id": 2, "titulo": "El problema de negocio",
        "pantalla": "Lámina con las cuatro preguntas del proyecto.",
        "leer": "Partimos de cuatro preguntas. Primera: cuántas personas escribieron en octubre de 2026 y cuántas "
                "compraron. Segunda: qué compraron, si fue para barbería, para salón o para spa. Tercera: qué mes, "
                "qué día y a qué hora compran más. Y cuarta: desde que activamos Meta CAPI, que es la conexión que le avisa a "
                "Facebook qué clientes realmente compran, ¿nos llegan clientes de mejor calidad?",
    },
    {
        "id": 3, "titulo": "Arquitectura cliente-servidor",
        "pantalla": "Diagrama: cliente HTML → API Spring Boot → MongoDB. Al lado, los paquetes controller, dto, model y service del ejemplo del curso.",
        "leer": "La arquitectura es la misma del ejemplo de la PokeAPI que vimos en clase, pero en lugar de consumir "
                "una API externa, el servidor consulta nuestra propia base de datos en MongoDB. El cliente es una "
                "página HTML con JavaScript que pide los datos con fetch. El servidor es una API en Spring Boot con "
                "Java 21, organizada en los paquetes controller, service, repository, model y dto. Y la base de datos "
                "es MongoDB 8, que guarda la información como documentos.",
    },
    {
        "id": 4, "titulo": "Los datos y la privacidad",
        "pantalla": "Lámina del ETL: CRM + ERP → limpieza y guardas → leads.json y ventas.json. Luego la terminal corriendo el ETL con el control 4 207 / 130.",
        "leer": "Los datos vienen de dos sistemas reales de la empresa: el CRM de WhatsApp, de donde salen los clientes, y "
                "el ERP, de donde salen las ventas. Un script en Python saca una foto de julio a octubre y la limpia. "
                "Aquí hay una regla importante: no se exponen montos, ni teléfonos, ni DNI, ni el nombre de la "
                "empresa, y las asesoras aparecen con seudónimo. Si el script encuentra cualquiera de esos datos, se detiene y no guarda nada. Además, "
                "compara sus totales con las bases originales: 4 207 clientes y 130 ventas en octubre, exactos.",
    },
    {
        "id": 5, "titulo": "MongoDB local y Compass",
        "pantalla": "MongoDB Compass conectado a la PC: base bi_leads, colecciones leads y ventas, un documento abierto y la pestaña Aggregations con el pipeline de ventas por día.",
        "leer": "Este es MongoDB Compass conectado a mi computadora. La base se llama bi_leads y tiene dos colecciones: "
                "leads, con un documento por cada cliente que escribió, y ventas, con un documento por cada "
                "comprobante. Fíjense que un documento guarda todo junto: el origen del anuncio, la etapa, la asesora "
                "y si compró. En la pestaña de agregaciones pego un pipeline: primero match para filtrar octubre, "
                "luego group para agrupar por día. El resultado sale al instante: el jueves es el día con más compras.",
    },
    {
        "id": 6, "titulo": "El back en Spring Boot",
        "pantalla": "VS Code: paquetes de la API, Lead.java con @Document, LeadRepository, Pipelines.java, MetricasService y BiController. Luego mvn test con 15 pruebas en verde y /api/salud en el navegador.",
        "leer": "Ahora el servidor. En model están las clases Lead y Venta, marcadas con arroba Document para que "
                "Spring las guarde en MongoDB. En repository usamos Spring Data: con solo escribir el nombre del "
                "método, como count by mes, Spring arma la consulta. Los cálculos pesados están en "
                "Pipelines, y son exactamente los mismos pipelines que acabamos de probar en Compass. El controller "
                "expone los endpoints con GetMapping, y todos reciben los mismos filtros por la URL: Spring los arma "
                "en un objeto Filtro, que se convierte en un match de MongoDB. Y antes de publicar, quince pruebas "
                "automáticas confirman que los números cuadran.",
    },
    {
        "id": 7, "titulo": "El front",
        "pantalla": "VS Code con app.js (fetch a la API con los filtros) y el dashboard en localhost:8081 llamando a localhost:8080.",
        "leer": "El cliente es independiente del servidor, igual que en el ejemplo del curso: el HTML corre en el "
                "puerto 8081 y la API en el 8080. El archivo app.js hace las llamadas con fetch, recibe el JSON y "
                "dibuja los gráficos con Chart.js. El dashboard es abierto, sin clave, y los filtros que elijas "
                "quedan en la dirección, así que se puede compartir exactamente la vista que estás mirando.",
    },
    {
        "id": 8, "titulo": "GitHub",
        "pantalla": "El repositorio público DBLTECH2026/bi-leads: carpetas, README y el .gitignore que deja fuera los datos reales.",
        "leer": "Todo el código está en un repositorio público de GitHub. Tiene un README que explica cómo correrlo "
                "y cómo desplegarlo. Los datos reales no se suben: el gitignore los deja fuera y, en su lugar, el "
                "repositorio trae datos de ejemplo inventados, para que cualquiera lo pueda probar.",
    },
    {
        "id": 9, "titulo": "Configurar el DNS",
        "pantalla": "hPanel de Hostinger → dbltech.tech → DNS: se crean los registros A y AAAA de bi. Luego nslookup en la terminal.",
        "leer": "Para publicarlo en internet necesitamos un dominio. En el panel de Hostinger, en la zona DNS de "
                "dbltech punto tech, creo un registro A con el nombre bi que apunta a la IP del servidor, y "
                "un registro AAAA con su dirección IPv6. Con nslookup comprobamos que el nombre ya responde con la "
                "IP correcta.",
    },
    {
        "id": 10, "titulo": "Despliegue en el VPS",
        "pantalla": "Terminal por SSH en el VPS: git clone, creación del .env, docker compose up -d --build y docker compose ps.",
        "leer": "Ahora entro al servidor por SSH. Es un VPS con Ubuntu y Docker. Clono el repositorio, creo el "
                "archivo de variables con las claves, y levanto todo con un solo comando: docker compose up. Docker "
                "construye la imagen de la API con Maven, descarga MongoDB y nginx, y deja los tres contenedores "
                "corriendo.",
    },
    {
        "id": 11, "titulo": "Carga de datos",
        "pantalla": "scp de los JSON al VPS y scripts/cargar-datos.sh con mongoimport: «leads: 21 587 · ventas: 593».",
        "leer": "Los contenedores ya están arriba, pero la base del servidor empieza vacía. Copio los dos archivos JSON y corro el script de carga, que usa "
                "mongoimport dentro del contenedor y crea los índices. Al final cuenta los documentos: 21 587 "
                "clientes y 593 ventas, de julio a octubre.",
    },
    {
        "id": 12, "titulo": "Cada contenedor",
        "pantalla": "docker compose ps; mongosh en el contenedor mongo; logs de la API con «Started»; wget a /api/salud desde web; el bloque de Caddy y el reload.",
        "leer": "Veamos cada contenedor. El primero es mongo: entro con mongosh, listo las colecciones y cuento los documentos. El segundo es la API de "
                "Spring Boot: en sus registros dice started, y el endpoint de salud responde con la versión de "
                "MongoDB. El tercero es web, un nginx que sirve el HTML y reenvía todo lo que empieza con barra api "
                "al contenedor de Spring. Por último, el proxy Caddy del servidor recibe el dominio y saca solo el "
                "certificado SSL.",
    },
    {
        "id": 13, "titulo": "Compass por túnel SSH",
        "pantalla": "Compass: nueva conexión con Proxy/SSH hacia el VPS y destino 127.0.0.1:27018. Se ven las mismas colecciones del servidor.",
        "leer": "Un detalle de seguridad: MongoDB no está abierto a internet. Entonces, ¿cómo lo vemos desde "
                "Compass? Con un túnel SSH. En la conexión elijo la opción de SSH, pongo el servidor y mi llave, y "
                "Compass entra por ese túnel. Aquí están las mismas colecciones, pero ahora en el servidor de "
                "producción.",
    },
    {
        "id": 14, "titulo": "El dashboard y los hallazgos",
        "pantalla": "https://bi.dbltech.tech: barra de filtros, filtros rápidos, destacados (clic en «Mes con más ventas»), filtro octubre, rubros, CAPI antes y después, clientes y hallazgos.",
        "leer": "Y este es el resultado en internet. Arriba está la barra de filtros: puedo combinar meses, rubro, "
                "origen, asesora, día y si compró o no. Los destacados son filtros inteligentes: el mes con más "
                "ventas fue agosto, y si lo toco, todo el dashboard se filtra a agosto. Si elijo octubre, veo que "
                "escribieron 4 207 personas, el 87 por ciento por anuncios, y compraron 93. El jueves es el día con "
                "más ventas y el domingo no se vende. Lo que más se vendió fue mobiliario de salón, casi la mitad, "
                "seguido de barbería. Y la respuesta sobre CAPI: desde que se activó llegan 29 por ciento menos "
                "leads, pero las ventas por cada 100 leads subieron de 2,6 a 3, un 18 por ciento más. Es "
                "correlación, no prueba, pero la calidad de los clientes mejoró.",
    },
    {
        "id": 15, "titulo": "Cierre",
        "pantalla": "Lámina final: conclusiones, enlaces al dashboard y a GitHub.",
        "leer": "En resumen: con MongoDB guardamos los datos como documentos, con Spring Boot los convertimos en "
                "indicadores, y con un cliente web los mostramos a quien toma decisiones. Un hallazgo extra: en "
                "octubre, quien escribe directo, sin anuncio, compró cuatro veces más que quien llegó por Facebook. El siguiente "
                "paso es llevar este mismo proyecto a arquitectura hexagonal. Gracias por su atención.",
    },
]

PALABRAS_POR_SEGUNDO = 2.4  # lectura tranquila en español


def duracion(texto: str) -> int:
    return round(len(texto.split()) / PALABRAS_POR_SEGUNDO)


def escribir_md(ruta: Path):
    total = sum(duracion(e["leer"]) for e in ESCENAS)
    lineas = [
        "# Guion del video · Luis López · BI",
        "",
        f"Duración estimada de la voz: **{total // 60} min {total % 60:02d} s** (más las pausas del video).",
        "",
        "## Cómo grabar",
        "",
        "- Un audio por escena: `01.m4a`, `02.m4a` … `15.m4a` (sirve m4a, mp3, wav u ogg, incluso notas de voz de WhatsApp).",
        "- Lugar en silencio, el celular a un palmo de la boca, sin música de fondo.",
        "- Deja 1 segundo de silencio al empezar y al terminar cada audio.",
        "- Si te equivocas, vuelve a grabar la escena completa: es más fácil que cortar.",
        "- Lee tranquilo y con tus palabras; si cambias algo del texto no pasa nada.",
        r"- Guárdalos en `Desktop\Inteligencia de negocios\voz\`.",
        "",
    ]
    for e in ESCENAS:
        lineas += [
            f"## {e['id']:02d} · {e['titulo']}  (~{duracion(e['leer'])} s)",
            "",
            f"**En pantalla:** {e['pantalla']}",
            "",
            f"**Leer:** {e['leer']}",
            "",
        ]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_docx(ruta: Path):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    doc = Document()
    for lang in doc.styles.element.iter(qn("w:lang")):
        for atributo in ("w:val", "w:eastAsia"):
            if lang.get(qn(atributo)) is not None:
                lang.set(qn(atributo), "es-PE")
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(13)
    rpr = normal.element.get_or_add_rPr()
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "es-PE")
    rpr.append(lang)

    doc.add_heading("Guion del video · Luis López · BI", level=0)
    total = sum(duracion(e["leer"]) for e in ESCENAS)
    doc.add_paragraph(f"Duración estimada de la voz: {total // 60} min {total % 60:02d} s. "
                      "Graba un audio por escena (01, 02 … 15), con 1 segundo de silencio al inicio y al final. "
                      r"Guárdalos en Desktop\Inteligencia de negocios\voz.")
    for e in ESCENAS:
        doc.add_heading(f"{e['id']:02d} · {e['titulo']}  (~{duracion(e['leer'])} s)", level=1)
        p = doc.add_paragraph()
        r = p.add_run("En pantalla: " + e["pantalla"])
        r.italic = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0x5A, 0x5A, 0x60)
        doc.add_paragraph(e["leer"])
    doc.save(ruta)


if __name__ == "__main__":
    aqui = Path(__file__).resolve().parent
    escribir_md(aqui / "guion.md")
    (aqui / "guion.json").write_text(json.dumps(ESCENAS, ensure_ascii=False, indent=1), encoding="utf-8")
    if len(sys.argv) > 1:
        escribir_docx(Path(sys.argv[1]) / "GUION - Luis Lopez BI.docx")
    total = sum(duracion(e["leer"]) for e in ESCENAS)
    print(f"{len(ESCENAS)} escenas · voz ~{total // 60} min {total % 60:02d} s")
