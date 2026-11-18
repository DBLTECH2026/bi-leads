package pe.luislopez.bi.service;

import java.time.YearMonth;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

import lombok.RequiredArgsConstructor;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Service;
import pe.luislopez.bi.dto.Dtos.Anuncios;
import pe.luislopez.bi.dto.Dtos.Asesora;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Conteo;
import pe.luislopez.bi.dto.Dtos.Dia;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Opcion;
import pe.luislopez.bi.dto.Dtos.Opciones;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.dto.Dtos.Salud;
import pe.luislopez.bi.dto.Filtro;
import pe.luislopez.bi.repository.LeadRepository;
import pe.luislopez.bi.repository.VentaRepository;

/** Indicadores según los filtros. Los cálculos los hace MongoDB; aquí solo se arma la respuesta. */
@Service
@RequiredArgsConstructor
public class MetricasService {
    static final String[] DIAS = {"lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"};
    static final Locale PE = Locale.forLanguageTag("es-PE");
    private static final int POR_PAGINA = 20;

    private final MongoTemplate mongo;
    private final LeadRepository leads;
    private final VentaRepository ventas;
    private final Filtros filtros;

    List<Document> agregar(String coleccion, String pipeline, Document filtro) {
        return agregar(coleccion, pipeline, Map.of("__FILTRO__", filtro));
    }

    List<Document> agregar(String coleccion, String pipeline, Map<String, Object> valores) {
        return mongo.getCollection(coleccion).aggregate(Pipelines.de(pipeline, valores)).into(new ArrayList<>());
    }

    long contar(String coleccion, Document filtro) {
        return mongo.getCollection(coleccion).countDocuments(filtro);
    }

    static long n(Document d, String campo) {
        Object v = d.get(campo);
        return v instanceof Number num ? num.longValue() : 0;
    }

    static double pct(long parte, long total) {
        return total == 0 ? 0 : Math.round(parte * 1000.0 / total) / 10.0;
    }

    static double por100(long ventas, long leads) {
        return leads == 0 ? 0 : Math.round(ventas * 10000.0 / leads) / 100.0;
    }

    static String nombreMes(String mes) {
        return YearMonth.parse(mes).getMonth().getDisplayName(TextStyle.FULL, PE);
    }

    public Resumen resumen(Filtro f) {
        Document fl = filtros.leads(f);
        Document fv = filtros.ventas(f);
        long totalLeads = contar("leads", fl);
        long deAnuncio = contar("leads", Filtros.y(fl, new Document("origen.tipo", "anuncio")));
        long calificados = contar("leads", Filtros.y(fl, new Document("calificado", true)));
        long compraron = contar("leads", Filtros.y(fl, new Document("compro", true)));
        long totalVentas = contar("ventas", fv);
        List<Document> u = agregar("ventas", Pipelines.UNIDADES, fv);
        long unidades = u.isEmpty() ? 0 : n(u.get(0), "unidades");
        return new Resumen(f.periodo(), totalLeads, deAnuncio, pct(deAnuncio, totalLeads), calificados, compraron,
                pct(compraron, totalLeads), totalVentas, por100(totalVentas, totalLeads), unidades);
    }

    public List<Etapa> embudo(Filtro f) {
        List<Document> r = agregar("leads", Pipelines.EMBUDO, filtros.leads(f));
        Document d = r.isEmpty() ? new Document() : r.get(0);
        long total = n(d, "llegaron");
        return List.of(
                new Etapa("llegaron", "Escribieron", total, total == 0 ? 0 : 100),
                new Etapa("interes", "Mostraron interés", n(d, "interes"), pct(n(d, "interes"), total)),
                new Etapa("listos", "Listos para comprar", n(d, "listos"), pct(n(d, "listos"), total)),
                new Etapa("compraron", "Compraron", n(d, "compraron"), pct(n(d, "compraron"), total)));
    }

    public Dias dias(Filtro f) {
        Map<Integer, Dia> porDia = new LinkedHashMap<>();
        for (int i = 1; i <= 7; i++) {
            porDia.put(i, new Dia(i, DIAS[i - 1], 0, 0));
        }
        for (Document d : agregar("ventas", Pipelines.VENTAS_POR_DIA, filtros.ventas(f))) {
            int num = d.get("_id", Document.class).getInteger("diaNum");
            porDia.put(num, new Dia(num, DIAS[num - 1], n(d, "ventas"), n(d, "unidades")));
        }
        List<Dia> lista = new ArrayList<>(porDia.values());
        Dia ganador = lista.stream().filter(x -> x.ventas() > 0).max(Comparator.comparingLong(Dia::ventas)).orElse(null);
        return new Dias(lista, ganador);
    }

    public List<Celda> calor(Filtro f) {
        return agregar("ventas", Pipelines.MAPA_DE_CALOR, filtros.ventas(f)).stream()
                .map(d -> {
                    Document id = d.get("_id", Document.class);
                    return new Celda(id.getInteger("diaNum"), id.getInteger("hora"), n(d, "ventas"));
                })
                .sorted(Comparator.comparingInt(Celda::diaNum).thenComparingInt(Celda::hora))
                .toList();
    }

    public List<Categoria> categorias(Filtro f) {
        List<Document> r = agregar("ventas", Pipelines.CATEGORIAS, filtros.ventas(f));
        long total = r.stream().mapToLong(d -> n(d, "unidades")).sum();
        return r.stream()
                .map(d -> new Categoria(d.getString("_id"), n(d, "ventas"), n(d, "unidades"),
                        pct(n(d, "unidades"), total)))
                .toList();
    }

    public Anuncios anuncios(Filtro f) {
        Document r = agregar("leads", Pipelines.ANUNCIOS_Y_ORIGENES, filtros.leads(f)).get(0);
        return new Anuncios(conteos(r.getList("anuncios", Document.class)),
                conteos(r.getList("origenes", Document.class)));
    }

    private static List<Conteo> conteos(List<Document> docs) {
        return docs.stream()
                .map(d -> new Conteo(d.getString("_id"), n(d, "leads"), n(d, "compraron"),
                        pct(n(d, "compraron"), n(d, "leads"))))
                .toList();
    }

    public List<Asesora> asesoras(Filtro f) {
        return agregar("leads", Pipelines.ASESORAS, filtros.leads(f)).stream()
                .map(d -> new Asesora(d.getString("_id"), n(d, "leads"), n(d, "calificados"), n(d, "compraron"),
                        pct(n(d, "compraron"), n(d, "leads"))))
                .toList();
    }

    /** Mediana de días entre que el cliente escribe y compra (null si nadie compró). */
    public Double medianaDias(Filtro f) {
        List<Document> r = agregar("leads", Pipelines.MEDIANA_DIAS, filtros.leads(f));
        return r.isEmpty() || !(r.get(0).get("mediana") instanceof Number m) ? null : m.doubleValue();
    }

    public Pagina<Cliente> clientes(Filtro f, String q, int pagina) {
        Document filtro = filtros.leads(f);
        if (q != null && !q.isBlank()) {
            filtro = Filtros.y(filtro,
                    new Document("nombre", new Document("$regex", Pattern.quote(q.trim())).append("$options", "i")));
        }
        int p = Math.max(pagina, 1);
        long total = contar("leads", filtro);
        List<Cliente> filas = agregar("leads", Pipelines.CLIENTES, Map.of(
                "__FILTRO__", filtro, "__SALTAR__", (p - 1) * POR_PAGINA, "__LIMITE__", POR_PAGINA))
                .stream().map(MetricasService::cliente).toList();
        return new Pagina<>(total, p, POR_PAGINA, filas);
    }

    private static Cliente cliente(Document d) {
        Document o = d.get("origen", Document.class);
        return new Cliente(d.getString("nombre"), d.get("llegada", Date.class).toInstant(), d.getString("dia"),
                o.getString("canal"), o.getString("anuncio"), d.getString("etapa"), d.getString("asesora"),
                d.getBoolean("compro", false), d.getInteger("diasHastaCompra"),
                d.getList("categorias", String.class));
    }

    /** Valores posibles de cada filtro, con cuántos registros tiene cada uno. */
    public Opciones opciones() {
        List<String> meses = mongo.getCollection("leads").distinct("mes", String.class).into(new ArrayList<>());
        meses.sort(Comparator.naturalOrder());
        // Consulta derivada de Spring Data: el nombre del método ES la consulta (countByMes)
        List<Opcion> opMeses = meses.stream()
                .map(m -> new Opcion(m, nombreMes(m), leads.countByMes(m))).toList();
        List<Opcion> rubros = categorias(Filtro.todo()).stream()
                .map(c -> new Opcion(c.categoria(), c.categoria(), c.unidades())).toList();
        List<Opcion> origenes = anuncios(Filtro.todo()).origenes().stream()
                .map(c -> new Opcion(c.nombre(), c.nombre(), c.leads())).toList();
        List<Opcion> ases = asesoras(Filtro.todo()).stream()
                .map(a -> new Opcion(a.asesora(), a.asesora(), a.leads())).toList();
        List<Opcion> dias = new ArrayList<>();
        for (int i = 1; i <= 7; i++) {
            dias.add(new Opcion(String.valueOf(i), DIAS[i - 1], ventas.countByDiaNum(i)));
        }
        return new Opciones(opMeses, rubros, origenes, ases, dias);
    }

    public Salud salud() {
        Document info = mongo.executeCommand("{ buildInfo: 1 }");
        return new Salud(true, info.getString("version"), mongo.getDb().getName(), leads.count(), ventas.count());
    }
}
