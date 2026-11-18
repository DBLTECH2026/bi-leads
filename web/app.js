// Luis López · BI — cliente. Consume la API Spring Boot con fetch y dibuja el dashboard.
// Los filtros son múltiples, se combinan entre sí y viajan en la URL (?meses=…&rubros=…).
(() => {
  "use strict";

  const API = window.BI_CONFIG.API_BASE;
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
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
    "otro anuncio": ["Otro anuncio", "globe"], "sin chat": ["Sin chat (tienda)", "store"],
  };
  const CLAVES = ["meses", "rubros", "origenes", "asesoras", "dias"];
  const NOMBRE_FILTRO = { meses: "Mes", rubros: "Rubro", origenes: "Origen", asesoras: "Asesora", dias: "Día", compro: "Compró" };

  // Filtros rápidos («inteligentes»): combinaciones listas; el primero se calcula con los datos
  const RAPIDOS = [
    { id: "mejor-mes", etiqueta: "Mes con más ventas", icono: "trophy" },
    { id: "capi", etiqueta: "Con CAPI (sep–oct)", icono: "trending-up", f: { meses: ["2026-09", "2026-10"] } },
    { id: "antes", etiqueta: "Antes de CAPI (jul–ago)", icono: "history", f: { meses: ["2026-07", "2026-08"] } },
    { id: "anuncios", etiqueta: "Solo anuncios", icono: "megaphone", f: { origenes: ["facebook", "instagram", "whatsapp", "otro anuncio"] } },
    { id: "directo", etiqueta: "Escribieron directo", icono: "user-round", f: { origenes: ["directo"] } },
    { id: "salon", etiqueta: "Compraron salón", icono: "armchair", f: { rubros: ["SALÓN"], compro: true } },
    { id: "barberia", etiqueta: "Compraron barbería", icono: "scissors", f: { rubros: ["BARBERÍA"], compro: true } },
    { id: "finde", etiqueta: "Fin de semana", icono: "sun", f: { dias: [6, 7] } },
    { id: "compraron", etiqueta: "Solo los que compraron", icono: "shopping-bag", f: { compro: true } },
  ];

  const vacio = () => ({ meses: [], rubros: [], origenes: [], asesoras: [], dias: [], compro: null });
  const estado = { f: vacio(), pestana: "mes", clientes: { pagina: 1, q: "" }, opciones: null };
  const graficos = {};

  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const iconos = () => lucide.createIcons();

  // ---------- Filtros: estado, URL y API ----------
  function qs(f = estado.f, extra = {}) {
    const p = new URLSearchParams();
    CLAVES.forEach((k) => { if (f[k].length) p.set(k, f[k].join(",")); });
    if (f.compro !== null) p.set("compro", f.compro);
    Object.entries(extra).forEach(([k, v]) => { if (v !== "" && v != null) p.set(k, v); });
    const s = p.toString();
    return s ? "?" + s : "";
  }

  function leerUrl() {
    const p = new URLSearchParams(location.search);
    CLAVES.forEach((k) => {
      const v = p.get(k);
      estado.f[k] = v ? v.split(",").filter(Boolean).map((x) => (k === "dias" ? Number(x) : x)) : [];
    });
    estado.f.compro = p.has("compro") ? p.get("compro") === "true" : null;
  }

  function escribirUrl() {
    history.replaceState(null, "", location.pathname + qs() + "#" + estado.pestana);
  }

  async function api(ruta) {
    const r = await fetch(API + ruta);
    if (!r.ok) throw new Error(ruta + " -> " + r.status);
    return r.json();
  }

  function cantidadFiltros(f = estado.f) {
    return CLAVES.reduce((n, k) => n + f[k].length, 0) + (f.compro !== null ? 1 : 0);
  }

  function etiqueta(clave, valor) {
    if (clave === "meses") return MESES[valor] || valor;
    if (clave === "dias") return DIAS_LARGOS[valor - 1];
    if (clave === "origenes") return (ORIGENES[valor] || [valor])[0];
    if (clave === "compro") return valor ? "Compraron" : "No compraron";
    return valor;
  }

  function textoFiltros(f = estado.f, sinMeses = false) {
    const partes = [];
    CLAVES.forEach((k) => {
      if (sinMeses && k === "meses") return;
      if (f[k].length) partes.push(`${NOMBRE_FILTRO[k]}: ${f[k].map((v) => etiqueta(k, v)).join(", ")}`);
    });
    if (f.compro !== null) partes.push(etiqueta("compro", f.compro));
    return partes.join(" · ");
  }

  /** Cambia los filtros y recarga. `reemplazar` empieza de cero (filtros rápidos). */
  function aplicar(nuevo, reemplazar = false) {
    const base = reemplazar ? vacio() : { ...estado.f };
    Object.entries(nuevo).forEach(([k, v]) => { base[k] = Array.isArray(v) ? [...v] : v; });
    estado.f = base;
    estado.clientes.pagina = 1;
    actualizarBarra();
    escribirUrl();
    cargarPestana();
  }

  function alternar(clave, valor) {
    const lista = estado.f[clave];
    aplicar({ [clave]: lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor] });
  }

  // ---------- Barra de filtros ----------
  function opcionesDe(clave) {
    const o = estado.opciones;
    if (!o) return [];
    if (clave === "dias") return o.dias.map((d) => ({ valor: Number(d.valor), etiqueta: d.etiqueta, cantidad: d.cantidad, unidad: "ventas" }));
    const unidad = clave === "rubros" ? "unid." : "leads";
    return o[clave].map((x) => ({ valor: x.valor, etiqueta: clave === "origenes" ? etiqueta("origenes", x.valor) : x.etiqueta, cantidad: x.cantidad, unidad }));
  }

  function pintarMenu(div) {
    const clave = div.dataset.filtro;
    const menu = div.querySelector(".menu");
    if (clave === "rapidos") {
      menu.innerHTML = RAPIDOS.map((r) => `<button class="opcion-rapida" data-rapido="${r.id}">
        <i data-lucide="${r.icono}"></i>${esc(r.etiqueta)}</button>`).join("");
    } else {
      const sel = estado.f[clave];
      menu.innerHTML = opcionesDe(clave).map((o) => `<label class="opcion">
          <input type="checkbox" value="${esc(o.valor)}" ${sel.includes(o.valor) ? "checked" : ""}>
          <span>${esc(o.etiqueta)}</span><small>${NUM.format(o.cantidad)} ${o.unidad}</small></label>`).join("") +
        `<button class="menu-todos" data-todos="${clave}">Ver todos</button>`;
    }
    iconos();
  }

  function actualizarBarra() {
    $$(".filtro[data-filtro]").forEach((div) => {
      const clave = div.dataset.filtro;
      if (clave === "rapidos") return;
      const n = estado.f[clave].length;
      div.querySelector(".cuenta").textContent = n ? n : "";
      div.classList.toggle("activo", n > 0);
    });
    $$("#f-compro button").forEach((b) => b.classList.toggle("activa", b.dataset.v === (estado.f.compro === null ? "" : String(estado.f.compro))));
    const n = cantidadFiltros();
    $("#limpiar").hidden = n === 0;
    const chips = [];
    CLAVES.forEach((k) => estado.f[k].forEach((v) => chips.push(
      `<button class="chip-filtro" data-quitar="${k}" data-valor="${esc(v)}">${NOMBRE_FILTRO[k]}: <b>${esc(etiqueta(k, v))}</b><i data-lucide="x"></i></button>`)));
    if (estado.f.compro !== null) chips.push(`<button class="chip-filtro" data-quitar="compro"><b>${etiqueta("compro", estado.f.compro)}</b><i data-lucide="x"></i></button>`);
    $("#activos").innerHTML = chips.join("");
    $("#activos").hidden = chips.length === 0;
    iconos();
  }

  async function aplicarRapido(id) {
    const r = RAPIDOS.find((x) => x.id === id);
    if (r.id === "mejor-mes") {
      const d = await api("/api/destacados" + qs({ ...estado.f, meses: [] }));
      const mes = d.find((x) => x.clave === "mes");
      if (mes) aplicar(mes.filtro);
      return;
    }
    aplicar(r.f, true);
  }

  // ---------- Gráficos (Chart.js) ----------
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = COLOR.texto;
  Chart.defaults.plugins.legend.display = false;
  Object.assign(Chart.defaults.plugins.tooltip, {
    backgroundColor: "#0a0a0a", padding: 10, cornerRadius: 8, displayColors: false, titleFont: { weight: "600" },
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

  // Clic en una barra = filtrar por ese valor (y la mano indica que se puede)
  const alClic = (clave, valores) => ({
    onClick: (_, el) => { if (el.length) alternar(clave, valores[el[0].index]); },
    onHover: (e, el) => { e.native.target.style.cursor = el.length ? "pointer" : "default"; },
  });

  // Etiqueta solo en las barras indicadas (rótulos selectivos, no un número en cada barra)
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

  const barrasVerticales = (id, etiquetas, valores, extra = {}) => grafico(id, {
    type: "bar",
    data: { labels: etiquetas, datasets: [{ data: valores, backgroundColor: extra.colores || COLOR.verde,
      borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: false, maxBarThickness: extra.grosor || 34 }] },
    options: { maintainAspectRatio: false, scales: ejes(false), layout: { padding: { top: 18 } },
      plugins: { tooltip: { callbacks: extra.tooltip || {} } }, ...(extra.clic || {}) },
    plugins: extra.plugins || [],
  });

  // ---------- Resumen ----------
  async function cargarMes() {
    const q = qs();
    const [res, dest, meses, emb, dias, calor, cats, anu, ases] = await Promise.all([
      api("/api/resumen" + q), api("/api/destacados" + q), api("/api/compras/meses" + q), api("/api/embudo" + q),
      api("/api/compras/dias" + q), api("/api/compras/calor" + q), api("/api/compras/categorias" + q),
      api("/api/anuncios/top" + q), api("/api/asesoras" + q),
    ]);
    $("#titulo-mes").textContent = "Resumen · " + res.periodo;
    pintarKpis(res);
    pintarDestacados(dest);
    pintarMeses(meses);
    pintarEmbudo(emb);
    pintarCategorias(cats);
    pintarDias(dias);
    pintarCalor(calor);
    pintarOrigen(anu.origenes);
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

  function pintarDestacados(lista) {
    $("#destacados").innerHTML = lista.length ? lista.map((d, i) => {
      const filtra = Object.keys(d.filtro || {}).length > 0;
      return `<button class="destacado${filtra ? "" : " fijo"}" data-destacado="${i}" ${filtra ? "" : "disabled"}>
        <span class="destacado-icono"><i data-lucide="${esc(d.icono)}"></i></span>
        <span class="destacado-titulo">${esc(d.titulo)}</span>
        <span class="destacado-valor">${esc(d.valor)}</span>
        <span class="destacado-detalle">${esc(d.detalle)}</span></button>`;
    }).join("") : `<p class="suave">Sin datos para estos filtros.</p>`;
    estado.destacados = lista;
  }

  function pintarMeses(meses) {
    const valores = meses.map((m) => m.ventas);
    const mejor = valores.indexOf(Math.max(...valores, 0));
    barrasVerticales("g-meses", meses.map((m) => MES_CORTO[m.mes] || m.mes), valores, {
      grosor: 46,
      tooltip: {
        title: (c) => MESES[meses[c[0].dataIndex].mes],
        label: (c) => `${NUM.format(meses[c.dataIndex].ventas)} comprobantes · ${DEC.format(meses[c.dataIndex].ventasPor100)} por 100 leads`,
      },
      clic: alClic("meses", meses.map((m) => m.mes)),
      plugins: mejor >= 0 && valores[mejor] > 0 ? [rotulo([mejor], () => "Más ventas")] : [],
    });
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
        indexAxis: "y", maintainAspectRatio: false, scales: ejes(true), ...alClic("rubros", cats.map((c) => c.categoria)),
        plugins: { tooltip: { callbacks: {
          label: (c) => `${NUM.format(cats[c.dataIndex].unidades)} unidades · ${DEC.format(cats[c.dataIndex].pctUnidades)} %`,
          afterLabel: (c) => `en ${NUM.format(cats[c.dataIndex].ventas)} comprobantes`,
        } } },
      },
    });
  }

  function pintarDias(d) {
    const ganador = d.ganador ? d.ganador.diaNum - 1 : -1;
    barrasVerticales("g-dias", d.dias.map((x) => DIAS[x.diaNum - 1]), d.dias.map((x) => x.ventas), {
      tooltip: {
        title: (c) => DIAS_LARGOS[c[0].dataIndex],
        label: (c) => `${NUM.format(d.dias[c.dataIndex].ventas)} comprobantes · ${NUM.format(d.dias[c.dataIndex].unidades)} unidades`,
      },
      clic: alClic("dias", d.dias.map((x) => x.diaNum)),
      plugins: ganador >= 0 ? [rotulo([ganador], () => "Más compras")] : [],
    });
  }

  function pintarCalor(celdas) {
    const mapa = new Map(celdas.map((c) => [c.diaNum + "-" + c.hora, c.ventas]));
    const max = Math.max(1, ...celdas.map((c) => c.ventas));
    let html = "<span></span>" + HORAS.map((h) => `<span class="eje">${h}</span>`).join("");
    for (let d = 1; d <= 7; d++) {
      html += `<span class="eje eje-dia">${DIAS[d - 1]}</span>`;
      for (const h of HORAS) {
        const n = mapa.get(d + "-" + h) || 0;
        html += `<span class="celda" style="${n ? "background:" + escalaVerde(n / max) : ""}"
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

  function filaFiltrable(clave, valor) {
    return estado.f[clave].includes(valor) ? "fila-filtro seleccionada" : "fila-filtro";
  }

  function pintarOrigen(lista) {
    const max = Math.max(1, ...lista.map((p) => p.leads));
    $("#t-origen").innerHTML = `<tr><td></td><td class="num apoyo">leads</td><td class="num apoyo">compra</td></tr>` +
      lista.map((p) => {
        const [nombre, icono] = ORIGENES[p.nombre] || [p.nombre, "globe"];
        return `<tr class="${filaFiltrable("origenes", p.nombre)}" data-filtrar="origenes" data-valor="${esc(p.nombre)}">
          <td><span class="con-icono"><i data-lucide="${icono}"></i>${esc(nombre)}</span>
          <div class="pista"><i style="width:${(p.leads / max) * 100}%"></i></div></td>
          <td class="num">${NUM.format(p.leads)}</td><td class="num">${DEC.format(p.conversion)} %</td></tr>`;
      }).join("");
  }

  function pintarAnuncios(anuncios) {
    $("#t-anuncios").innerHTML = anuncios.length ? `<tr><td></td><td class="num apoyo">compraron</td></tr>` +
      anuncios.map((a) => `<tr><td class="texto-largo" title="${esc(a.nombre)}">${esc(a.nombre)}</td>
        <td class="num">${NUM.format(a.compraron)} <span class="apoyo">/ ${NUM.format(a.leads)}</span></td></tr>`).join("")
      : `<tr><td class="apoyo">Sin anuncios con estos filtros</td></tr>`;
  }

  function pintarAsesoras(lista) {
    $("#t-asesoras").innerHTML = `<tr><td></td><td class="num apoyo">leads</td><td class="num apoyo">compraron</td><td class="num apoyo">%</td></tr>` +
      lista.map((a) => `<tr class="${filaFiltrable("asesoras", a.asesora)}" data-filtrar="asesoras" data-valor="${esc(a.asesora)}">
        <td><span class="con-icono"><i data-lucide="user-round"></i>${esc(a.asesora)}</span></td>
        <td class="num">${NUM.format(a.leads)}</td><td class="num">${NUM.format(a.compraron)}</td>
        <td class="num">${DEC.format(a.conversion)}</td></tr>`).join("");
  }

  // ---------- CAPI ----------
  async function cargarCapi() {
    const c = await api("/api/capi/comparativo" + qs());
    const signo = c.variacionPct >= 0 ? "+" : "";
    $("#capi-variacion").textContent = signo + DEC.format(c.variacionPct) + " %";
    const otros = textoFiltros(estado.f, true);
    $("#capi-nota").textContent = c.nota + (otros ? " Filtros aplicados: " + otros + "." : "");
    $("#capi-periodos").innerHTML = [["Antes de CAPI · jul–ago", c.antes, "antes"], ["Con CAPI · sep–oct", c.despues, "despues"]]
      .map(([t, p, cl]) => `<div class="periodo"><div class="periodo-titulo"><i class="cuadro ${cl}"></i>${t}</div>
        <div class="periodo-datos"><div><b>${NUM.format(p.leads)}</b><span>leads</span></div>
        <div><b>${DEC.format(p.ventasPor100)}</b><span>ventas por 100 leads</span></div>
        <div><b>${DEC.format(p.pctCalificados)} %</b><span>listos para comprar</span></div></div></div>`).join("");

    const etiquetas = c.meses.map((m) => MES_CORTO[m.mes] || m.mes);
    const colores = c.meses.map((m) => (m.periodo === "antes" ? COLOR.antes : COLOR.despues));
    const barras = (id, valores, formato) => barrasVerticales(id, etiquetas, valores, {
      grosor: 40, colores,
      tooltip: {
        title: (x) => MESES[c.meses[x[0].dataIndex].mes] + (c.meses[x[0].dataIndex].periodo === "antes" ? " · antes de CAPI" : " · con CAPI"),
        label: (x) => formato(valores[x.dataIndex]),
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
    iconos();
  }

  // ---------- Clientes ----------
  async function cargarClientes() {
    const c = estado.clientes;
    const r = await api("/api/clientes" + qs(estado.f, { q: c.q, pagina: c.pagina }));
    const paginas = Math.max(1, Math.ceil(r.total / r.porPagina));
    $("#total-clientes").textContent = NUM.format(r.total) + " clientes";
    $("#pag-num").textContent = `${r.pagina} de ${NUM.format(paginas)}`;
    $("#pag-ant").disabled = r.pagina <= 1;
    $("#pag-sig").disabled = r.pagina >= paginas;
    $("#clientes-vacio").hidden = r.filas.length > 0;
    $("#t-clientes").hidden = r.filas.length === 0;
    $("#t-clientes").innerHTML = `<tr><th>Cliente</th><th>Llegó</th><th>Origen</th><th>Anuncio</th><th>Etapa</th>
      <th>Asesora</th><th>Compró</th><th class="der">Días a compra</th></tr>` +
      r.filas.map((x) => {
        const [etapa, clase] = ETAPAS[x.etapa] || [x.etapa, ""];
        const [origen, icono] = ORIGENES[x.origen] || [x.origen, "globe"];
        const compro = x.compro
          ? `<span class="pildora ok">Sí</span> ${(x.categoriasCompradas || []).map((y) => `<span class="etiqueta-rubro">${esc(y)}</span>`).join("")}`
          : `<span class="pildora">No</span>`;
        return `<tr><td><b>${esc(x.nombre)}</b></td><td>${FECHA.format(new Date(x.llegada))}</td>
          <td><span class="con-icono"><i data-lucide="${icono}"></i>${esc(origen)}</span></td>
          <td class="texto-largo" style="max-width:220px" title="${esc(x.anuncio || "")}">${esc(x.anuncio || "—")}</td>
          <td><span class="pildora ${clase}">${esc(etapa)}</span></td><td>${esc(x.asesora)}</td>
          <td>${compro}</td><td class="der">${x.diasHastaCompra ?? "—"}</td></tr>`;
      }).join("");
    iconos();
  }

  // ---------- Hallazgos ----------
  async function cargarHallazgos() {
    const h = await api("/api/hallazgos" + qs());
    const filtros = textoFiltros();
    $("#hallazgos-mes").textContent = "Frases armadas por la API con los datos" + (filtros ? " filtrados · " + filtros : " de jul–oct 2026");
    $("#hallazgos").innerHTML = h.map((x) => `<div class="hallazgo">
      <span class="hallazgo-icono"><i data-lucide="${esc(x.icono)}"></i></span><p>${esc(x.texto)}</p></div>`).join("");
    iconos();
  }

  // ---------- Navegación ----------
  function cargarPestana() {
    const t = estado.pestana;
    const carga = t === "mes" ? cargarMes() : t === "capi" ? cargarCapi() : t === "clientes" ? cargarClientes() : cargarHallazgos();
    return carga.catch((e) => console.error(e));
  }

  function cambiarPestana(t) {
    estado.pestana = t;
    $$(".pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.tab === t));
    $$("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== t; });
    escribirUrl();
    cargarPestana();
  }

  async function iniciar() {
    leerUrl();
    fetch(API + "/api/salud").then((r) => r.json()).then((s) => {
      $("#chip-mongo span").textContent = `MongoDB ${s.mongo} · ${NUM.format(s.leads + s.ventas)} documentos`;
    }).catch(() => {});
    estado.opciones = await api("/api/opciones").catch(() => null);
    actualizarBarra();
    const inicial = location.hash.slice(1);
    cambiarPestana(["mes", "capi", "clientes", "hallazgos"].includes(inicial) ? inicial : "mes");
    iconos();
  }

  // ---------- Eventos ----------
  document.addEventListener("click", (e) => {
    const boton = e.target.closest(".filtro-boton");
    const abierto = e.target.closest(".filtro");
    $$(".filtro .menu").forEach((m) => {
      const div = m.parentElement;
      if (boton && div === boton.parentElement) {
        if (m.hidden) pintarMenu(div);
        m.hidden = !m.hidden;
      } else if (div !== abierto) {
        m.hidden = true;
      }
    });
    const quitar = e.target.closest("[data-quitar]");
    if (quitar) {
      const k = quitar.dataset.quitar;
      if (k === "compro") aplicar({ compro: null });
      else alternar(k, k === "dias" ? Number(quitar.dataset.valor) : quitar.dataset.valor);
    }
    const todos = e.target.closest("[data-todos]");
    if (todos) { aplicar({ [todos.dataset.todos]: [] }); todos.closest(".menu").hidden = true; }
    const rapido = e.target.closest("[data-rapido]");
    if (rapido) { rapido.closest(".menu").hidden = true; aplicarRapido(rapido.dataset.rapido); }
    const dest = e.target.closest("[data-destacado]");
    if (dest && !dest.disabled) aplicar(estado.destacados[Number(dest.dataset.destacado)].filtro);
    const fila = e.target.closest("[data-filtrar]");
    if (fila) alternar(fila.dataset.filtrar, fila.dataset.valor);
  });

  document.addEventListener("change", (e) => {
    const caja = e.target.closest(".menu input[type=checkbox]");
    if (!caja) return;
    const clave = caja.closest(".filtro").dataset.filtro;
    alternar(clave, clave === "dias" ? Number(caja.value) : caja.value);
  });

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

  $("#limpiar").addEventListener("click", () => aplicar({}, true));
  $$("#f-compro button").forEach((b) => b.addEventListener("click", () =>
    aplicar({ compro: b.dataset.v === "" ? null : b.dataset.v === "true" })));
  $$(".pestanas button").forEach((b) => b.addEventListener("click", () => cambiarPestana(b.dataset.tab)));
  let espera;
  $("#buscar").addEventListener("input", (e) => {
    clearTimeout(espera);
    espera = setTimeout(() => { estado.clientes.q = e.target.value.trim(); estado.clientes.pagina = 1; cargarClientes(); }, 300);
  });
  $("#pag-ant").addEventListener("click", () => { estado.clientes.pagina--; cargarClientes(); });
  $("#pag-sig").addEventListener("click", () => { estado.clientes.pagina++; cargarClientes(); });

  iconos();
  iniciar();
})();
