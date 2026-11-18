// Luis López · BI — cliente. Consume la API Spring Boot con fetch y dibuja el dashboard.
(() => {
  "use strict";

  const API = window.BI_CONFIG.API_BASE;
  const $ = (s) => document.querySelector(s);
  const NUM = new Intl.NumberFormat("es-PE");
  const DEC = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 1 });
  const FECHA = new Intl.DateTimeFormat("es-PE", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "America/Lima",
  });
  const MESES = { "2026-07": "julio", "2026-08": "agosto", "2026-09": "setiembre", "2026-10": "octubre" };
  const MES_CORTO = { "2026-07": "jul", "2026-08": "ago", "2026-09": "sep", "2026-10": "oct" };
  const DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];
  const DIAS_LARGOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
  const HORAS = Array.from({ length: 14 }, (_, i) => 8 + i); // 8:00 a 21:00
  const COLOR = { verde: "#16a34a", antes: "#66c28a", despues: "#15803d", grilla: "#eef0f3", texto: "#5a5a60" };
  const ETAPAS = {
    INACTIVO: ["Inactivo", ""], INTERESADO: ["Interesado", "marca"], LISTO_PARA_COMPRAR: ["Listo", "marca"],
    VENTA_GANADA: ["Ganada", "ok"], VENTA_PERDIDA: ["Perdida", ""], EN_SEGUIMIENTO: ["Seguimiento", "marca"],
    EN_CALIFICACION: ["Calificando", ""],
  };
  const ORIGENES = {
    facebook: ["Anuncio Facebook", "megaphone"], instagram: ["Anuncio Instagram", "camera"],
    whatsapp: ["Anuncio WhatsApp", "message-circle"], directo: ["Escribió directo", "user-round"],
    "otro anuncio": ["Otro anuncio", "globe"], anuncio: ["Anuncio", "megaphone"],
  };

  const estado = { token: sessionStorage.getItem("bi_leads_token"), mes: "2026-10", pestana: "mes",
    clientes: { pagina: 1, compro: "", q: "" }, capiCargado: false };
  const graficos = {};

  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const iconos = () => lucide.createIcons();

  // ---------- API ----------
  async function api(ruta) {
    const r = await fetch(API + ruta, { headers: { Authorization: "Bearer " + estado.token } });
    if (r.status === 401) { salir(); throw new Error("sin acceso"); }
    if (!r.ok) throw new Error(ruta + " -> " + r.status);
    return r.json();
  }

  async function ingresar(ev) {
    ev.preventDefault();
    const r = await fetch(API + "/api/ingresar", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clave: $("#clave").value }),
    });
    if (!r.ok) { $("#ingreso-error").hidden = false; return; }
    estado.token = (await r.json()).token;
    sessionStorage.setItem("bi_leads_token", estado.token);
    iniciar();
  }

  function salir() {
    sessionStorage.removeItem("bi_leads_token");
    estado.token = null;
    $("#app").hidden = true;
    $("#ingreso").hidden = false;
  }

  // ---------- Gráficos (Chart.js) ----------
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = COLOR.texto;
  Chart.defaults.plugins.legend.display = false;
  Object.assign(Chart.defaults.plugins.tooltip, {
    backgroundColor: "#0a0a0a", padding: 10, cornerRadius: 8, displayColors: false,
    titleFont: { weight: "600" },
  });

  function grafico(id, config) {
    graficos[id]?.destroy();
    graficos[id] = new Chart(document.getElementById(id), config);
  }

  const ejes = (horizontal) => ({
    [horizontal ? "y" : "x"]: { grid: { display: false }, border: { display: false } },
    [horizontal ? "x" : "y"]: {
      beginAtZero: true, grid: { color: COLOR.grilla }, border: { display: false },
      ticks: { precision: 0, callback: (v) => NUM.format(v) },
    },
  });

  // Etiqueta solo en la barra indicada (rótulos selectivos, no un número en cada barra)
  const rotulo = (indices, texto) => ({
    id: "rotulo",
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.getDatasetMeta(0).data.forEach((barra, i) => {
        if (!indices.includes(i)) return;
        ctx.save();
        ctx.font = "600 12px Inter";
        ctx.fillStyle = "#0a0a0a";
        ctx.textAlign = "center";
        ctx.fillText(texto(i), barra.x, barra.y - 8);
        ctx.restore();
      });
    },
  });

  // Línea vertical "CAPI" entre agosto y setiembre
  const lineaCapi = {
    id: "lineaCapi",
    afterDatasetsDraw(chart) {
      const meta = chart.getDatasetMeta(0).data;
      if (meta.length < 3) return;
      const x = (meta[1].x + meta[2].x) / 2;
      const { top, bottom } = chart.chartArea;
      const { ctx } = chart;
      ctx.save();
      ctx.strokeStyle = "#0a0a0a";
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
      ctx.setLineDash([]);
      ctx.font = "600 11px Inter"; ctx.fillStyle = "#0a0a0a"; ctx.textAlign = "left";
      ctx.fillText("CAPI", x + 5, top + 10);
      ctx.restore();
    },
  };

  // ---------- Resumen del mes ----------
  async function cargarMes() {
    const m = estado.mes;
    const q = "?mes=" + m;
    $("#titulo-mes").textContent = "Resumen de " + MESES[m];
    const [res, emb, dias, calor, cats, anu, ases] = await Promise.all([
      api("/api/resumen" + q), api("/api/embudo" + q), api("/api/compras/dias" + q), api("/api/compras/calor" + q),
      api("/api/compras/categorias" + q), api("/api/anuncios/top" + q), api("/api/asesoras" + q),
    ]);
    pintarKpis(res);
    pintarEmbudo(emb);
    pintarCategorias(cats);
    pintarDias(dias);
    pintarCalor(calor);
    pintarOrigen(anu.plataformas);
    pintarAnuncios(anu.anuncios);
    pintarAsesoras(ases);
    iconos();
  }

  function pintarKpis(r) {
    const k = [
      ["Leads", NUM.format(r.leads), "escribieron por WhatsApp", "users"],
      ["De anuncios", DEC.format(r.pctAnuncio) + " %", NUM.format(r.deAnuncio) + " por Meta Ads", "megaphone"],
      ["Listos para comprar", NUM.format(r.calificados), DEC.format(r.calificados * 100 / (r.leads || 1)) + " % de los leads", "target"],
      ["Compraron", NUM.format(r.compraron), DEC.format(r.conversion) + " % de conversión", "shopping-bag"],
      ["Ventas por 100 leads", DEC.format(r.ventasPor100), NUM.format(r.ventas) + " comprobantes · " + NUM.format(r.unidades) + " unid.", "receipt"],
    ];
    $("#kpis").innerHTML = k.map(([e, v, p, i]) => `
      <div class="kpi"><div class="kpi-etiqueta">${e}</div><div class="kpi-valor">${v}</div>
      <div class="kpi-pie">${p}</div><span class="kpi-icono"><i data-lucide="${i}"></i></span></div>`).join("");
  }

  function pintarEmbudo(etapas) {
    const max = etapas[0]?.cantidad || 1;
    $("#embudo").innerHTML = etapas.map((e) => `
      <div class="etapa-fila" data-tip="${esc(e.nombre)}: ${NUM.format(e.cantidad)} (${DEC.format(e.pctDelTotal)} % de los leads)">
        <span class="etapa-nombre">${esc(e.nombre)}</span>
        <div class="etapa-pista"><div class="etapa-barra" style="width:${(e.cantidad / max) * 100}%"></div></div>
        <span class="etapa-valor">${NUM.format(e.cantidad)}<small>${DEC.format(e.pctDelTotal)} %</small></span>
      </div>`).join("") + (etapas[3] ? `<p class="lectura">De cada 100 personas que escriben, <b>${DEC.format(etapas[3].pctDelTotal)}</b> compran
      y <b>${DEC.format(etapas[2].pctDelTotal)}</b> llegan a estar listas para comprar.</p>` : "");
  }

  function pintarCategorias(cats) {
    grafico("g-categorias", {
      type: "bar",
      data: {
        labels: cats.map((c) => c.categoria),
        datasets: [{ data: cats.map((c) => c.unidades), backgroundColor: COLOR.verde,
          borderRadius: { topRight: 4, bottomRight: 4 }, borderSkipped: false, maxBarThickness: 22 }],
      },
      options: {
        indexAxis: "y", maintainAspectRatio: false, scales: ejes(true),
        plugins: { tooltip: { callbacks: {
          label: (c) => `${NUM.format(cats[c.dataIndex].unidades)} unidades · ${DEC.format(cats[c.dataIndex].pctUnidades)} %`,
          afterLabel: (c) => `en ${NUM.format(cats[c.dataIndex].ventas)} comprobantes`,
        } } },
      },
    });
  }

  function pintarDias(d) {
    const ganador = d.ganador ? d.ganador.diaNum - 1 : -1;
    grafico("g-dias", {
      type: "bar",
      data: {
        labels: d.dias.map((x) => DIAS[x.diaNum - 1]),
        datasets: [{ data: d.dias.map((x) => x.ventas), backgroundColor: COLOR.verde,
          borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: false, maxBarThickness: 34 }],
      },
      options: {
        maintainAspectRatio: false, scales: ejes(false), layout: { padding: { top: 18 } },
        plugins: { tooltip: { callbacks: {
          title: (c) => DIAS_LARGOS[c[0].dataIndex],
          label: (c) => `${NUM.format(d.dias[c.dataIndex].ventas)} comprobantes · ${NUM.format(d.dias[c.dataIndex].unidades)} unidades`,
        } } },
      },
      plugins: ganador >= 0 ? [rotulo([ganador], () => "Más compras")] : [],
    });
  }

  function pintarCalor(celdas) {
    const mapa = new Map(celdas.map((c) => [c.diaNum + "-" + c.hora, c.ventas]));
    const max = Math.max(1, ...celdas.map((c) => c.ventas));
    let html = '<span></span>' + HORAS.map((h) => `<span class="eje">${h}</span>`).join("");
    for (let d = 1; d <= 7; d++) {
      html += `<span class="eje eje-dia">${DIAS[d - 1]}</span>`;
      for (const h of HORAS) {
        const n = mapa.get(d + "-" + h) || 0;
        const fondo = n ? escalaVerde(n / max) : "";
        html += `<span class="celda" style="${fondo ? "background:" + fondo : ""}"
          data-tip="${DIAS_LARGOS[d - 1]} ${h}:00–${h + 1}:00 · ${n} ${n === 1 ? "venta" : "ventas"}"></span>`;
      }
    }
    $("#calor").innerHTML = html;
  }

  // Secuencial de un solo tono (verde): claro (pocas ventas) -> oscuro (muchas)
  const PASOS = [[220, 252, 231], [134, 239, 172], [22, 163, 74], [20, 83, 45]];
  function escalaVerde(t) {
    const x = Math.min(1, Math.max(0, t)) * (PASOS.length - 1);
    const i = Math.min(PASOS.length - 2, Math.floor(x));
    const f = x - i;
    return `rgb(${PASOS[i].map((v, k) => Math.round(v + (PASOS[i + 1][k] - v) * f)).join(",")})`;
  }

  function pintarOrigen(plat) {
    const max = Math.max(1, ...plat.map((p) => p.leads));
    $("#t-origen").innerHTML = `<tr><td></td><td class="num apoyo">leads</td><td class="num apoyo">compra</td></tr>` +
      plat.map((p) => {
        const [nombre, icono] = ORIGENES[p.nombre] || [p.nombre, "globe"];
        return `<tr><td><span class="con-icono"><i data-lucide="${icono}"></i>${esc(nombre)}</span>
          <div class="pista"><i style="width:${(p.leads / max) * 100}%"></i></div></td>
          <td class="num">${NUM.format(p.leads)}</td><td class="num">${DEC.format(p.conversion)} %</td></tr>`;
      }).join("");
  }

  function pintarAnuncios(anuncios) {
    $("#t-anuncios").innerHTML = `<tr><td></td><td class="num apoyo">compraron</td></tr>` +
      anuncios.map((a) => `<tr><td class="texto-largo" title="${esc(a.nombre)}">${esc(a.nombre)}</td>
        <td class="num">${NUM.format(a.compraron)} <span class="apoyo">/ ${NUM.format(a.leads)}</span></td></tr>`).join("");
  }

  function pintarAsesoras(lista) {
    $("#t-asesoras").innerHTML = `<tr><td></td><td class="num apoyo">leads</td><td class="num apoyo">compraron</td><td class="num apoyo">%</td></tr>` +
      lista.map((a) => `<tr><td><span class="con-icono"><i data-lucide="user-round"></i>${esc(a.asesora)}</span></td>
        <td class="num">${NUM.format(a.leads)}</td><td class="num">${NUM.format(a.compraron)}</td>
        <td class="num">${DEC.format(a.conversion)}</td></tr>`).join("");
  }

  // ---------- CAPI ----------
  async function cargarCapi() {
    const c = await api("/api/capi/comparativo");
    const signo = c.variacionPct >= 0 ? "+" : "";
    $("#capi-variacion").textContent = signo + DEC.format(c.variacionPct) + " %";
    $("#capi-nota").textContent = c.nota;
    $("#capi-periodos").innerHTML = [["Antes de CAPI · jul–ago", c.antes, "antes"], ["Con CAPI · sep–oct", c.despues, "despues"]]
      .map(([t, p, cl]) => `<div class="periodo"><div class="periodo-titulo"><i class="cuadro ${cl}"></i>${t}</div>
        <div class="periodo-datos"><div><b>${NUM.format(p.leads)}</b><span>leads</span></div>
        <div><b>${DEC.format(p.ventasPor100)}</b><span>ventas por 100 leads</span></div>
        <div><b>${DEC.format(p.pctCalificados)} %</b><span>listos para comprar</span></div></div></div>`).join("");

    const etiquetas = c.meses.map((m) => MES_CORTO[m.mes] || m.mes);
    const colores = c.meses.map((m) => (m.periodo === "antes" ? COLOR.antes : COLOR.despues));
    const barras = (id, valores, formato) => grafico(id, {
      type: "bar",
      data: { labels: etiquetas, datasets: [{ data: valores, backgroundColor: colores,
        borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: false, maxBarThickness: 40 }] },
      options: {
        maintainAspectRatio: false, scales: ejes(false), layout: { padding: { top: 18 } },
        plugins: { tooltip: { callbacks: {
          title: (x) => MESES[c.meses[x[0].dataIndex].mes] + (c.meses[x[0].dataIndex].periodo === "antes" ? " · antes de CAPI" : " · con CAPI"),
          label: (x) => formato(valores[x.dataIndex]),
        } } },
      },
      plugins: [lineaCapi, rotulo([0, valores.length - 1], (i) => formato(valores[i]))],
    });
    barras("g-capi-leads", c.meses.map((m) => m.leads), (v) => NUM.format(v));
    barras("g-capi-por100", c.meses.map((m) => m.ventasPor100), (v) => DEC.format(v));
    barras("g-capi-calif", c.meses.map((m) => m.pctCalificados), (v) => DEC.format(v) + " %");

    $("#t-capi").innerHTML = `<tr><th>Mes</th><th>Periodo</th><th class="der">Leads</th><th class="der">Listos</th>
      <th class="der">% listos</th><th class="der">Compraron</th><th class="der">Ventas</th><th class="der">Ventas / 100 leads</th>
      <th class="der">Mediana días a compra</th><th class="der">Leads enviados a CAPI</th></tr>` +
      c.meses.map((m) => `<tr><td>${MESES[m.mes] || m.mes}</td>
        <td><span class="pildora ${m.periodo === "antes" ? "" : "marca"}">${m.periodo === "antes" ? "Antes" : "Con CAPI"}</span></td>
        <td class="der">${NUM.format(m.leads)}</td><td class="der">${NUM.format(m.calificados)}</td>
        <td class="der">${DEC.format(m.pctCalificados)} %</td><td class="der">${NUM.format(m.compraron)}</td>
        <td class="der">${NUM.format(m.ventas)}</td><td class="der">${DEC.format(m.ventasPor100)}</td>
        <td class="der">${m.medianaDias == null ? "—" : DEC.format(m.medianaDias)}</td>
        <td class="der">${NUM.format(m.leadsCapi)}</td></tr>`).join("");
    estado.capiCargado = true;
    iconos();
  }

  // ---------- Clientes ----------
  async function cargarClientes() {
    const f = estado.clientes;
    const p = new URLSearchParams({ mes: estado.mes, pagina: f.pagina });
    if (f.compro) p.set("compro", f.compro);
    if (f.q) p.set("q", f.q);
    const r = await api("/api/clientes?" + p);
    const paginas = Math.max(1, Math.ceil(r.total / r.porPagina));
    $("#total-clientes").textContent = NUM.format(r.total) + " clientes";
    $("#pag-num").textContent = `${r.pagina} de ${NUM.format(paginas)}`;
    $("#pag-ant").disabled = r.pagina <= 1;
    $("#pag-sig").disabled = r.pagina >= paginas;
    $("#clientes-vacio").hidden = r.filas.length > 0;
    $("#t-clientes").hidden = r.filas.length === 0;
    $("#t-clientes").innerHTML = `<tr><th>Cliente</th><th>Llegó</th><th>Origen</th><th>Anuncio</th><th>Etapa</th>
      <th>Asesora</th><th>Compró</th><th class="der">Días a compra</th></tr>` +
      r.filas.map((c) => {
        const [etapa, clase] = ETAPAS[c.etapa] || [c.etapa, ""];
        const [origen, icono] = ORIGENES[c.origen] || [c.origen, "globe"];
        const compro = c.compro
          ? `<span class="pildora ok">Sí</span> ${(c.categoriasCompradas || []).map((x) => `<span class="etiqueta-rubro">${esc(x)}</span>`).join("")}`
          : `<span class="pildora">No</span>`;
        return `<tr><td><b>${esc(c.nombre)}</b></td><td>${FECHA.format(new Date(c.llegada))}</td>
          <td><span class="con-icono"><i data-lucide="${icono}"></i>${esc(origen)}</span></td>
          <td class="texto-largo" style="max-width:220px" title="${esc(c.anuncio || "")}">${esc(c.anuncio || "—")}</td>
          <td><span class="pildora ${clase}">${esc(etapa)}</span></td><td>${esc(c.asesora)}</td>
          <td>${compro}</td><td class="der">${c.diasHastaCompra ?? "—"}</td></tr>`;
      }).join("");
    iconos();
  }

  // ---------- Hallazgos ----------
  async function cargarHallazgos() {
    const h = await api("/api/hallazgos?mes=" + estado.mes);
    $("#hallazgos-mes").textContent = "Frases armadas por la API con los números de " + MESES[estado.mes];
    $("#hallazgos").innerHTML = h.map((x) => `<div class="hallazgo">
      <span class="hallazgo-icono"><i data-lucide="${esc(x.icono)}"></i></span><p>${esc(x.texto)}</p></div>`).join("");
    iconos();
  }

  // ---------- Navegación ----------
  function cargarPestana() {
    const t = estado.pestana;
    if (t === "mes") return cargarMes();
    if (t === "capi") return estado.capiCargado ? null : cargarCapi();
    if (t === "clientes") return cargarClientes();
    return cargarHallazgos();
  }

  function cambiarPestana(t) {
    estado.pestana = t;
    document.querySelectorAll(".pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.tab === t));
    document.querySelectorAll("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== t; });
    history.replaceState(null, "", "#" + t);
    cargarPestana();
  }

  async function iniciar() {
    $("#ingreso").hidden = true;
    $("#app").hidden = false;
    fetch(API + "/api/salud").then((r) => r.json()).then((s) => {
      $("#chip-mongo span").textContent = `MongoDB ${s.mongo} · ${NUM.format(s.leads + s.ventas)} documentos`;
    }).catch(() => {});
    const inicial = location.hash.slice(1);
    cambiarPestana(["mes", "capi", "clientes", "hallazgos"].includes(inicial) ? inicial : "mes");
    iconos();
  }

  // Tooltip propio para el embudo y el mapa de calor
  document.addEventListener("mousemove", (e) => {
    const el = e.target.closest("[data-tip]");
    const tip = $("#tip");
    if (!el) { tip.hidden = true; return; }
    tip.textContent = el.dataset.tip;
    tip.hidden = false;
    tip.style.left = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8) + "px";
    tip.style.top = e.clientY + 16 + "px";
  });

  $("#form-ingreso").addEventListener("submit", ingresar);
  $("#salir").addEventListener("click", salir);
  document.querySelectorAll(".pestanas button").forEach((b) => b.addEventListener("click", () => cambiarPestana(b.dataset.tab)));
  $("#mes").addEventListener("change", (e) => {
    estado.mes = e.target.value;
    estado.clientes.pagina = 1;
    if (estado.pestana !== "capi") cargarPestana();
  });
  let espera;
  $("#buscar").addEventListener("input", (e) => {
    clearTimeout(espera);
    espera = setTimeout(() => { estado.clientes.q = e.target.value.trim(); estado.clientes.pagina = 1; cargarClientes(); }, 300);
  });
  document.querySelectorAll("#f-compro button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#f-compro button").forEach((x) => x.classList.toggle("activa", x === b));
    estado.clientes.compro = b.dataset.v;
    estado.clientes.pagina = 1;
    cargarClientes();
  }));
  $("#pag-ant").addEventListener("click", () => { estado.clientes.pagina--; cargarClientes(); });
  $("#pag-sig").addEventListener("click", () => { estado.clientes.pagina++; cargarClientes(); });

  iconos();
  if (estado.token) iniciar(); else $("#ingreso").hidden = false;
})();
