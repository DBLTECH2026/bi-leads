package pe.luislopez.bi.service;

import static pe.luislopez.bi.service.Pipelines.validarMes;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

import pe.luislopez.bi.dto.Dtos.Anuncios;
import pe.luislopez.bi.dto.Dtos.Asesora;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Conteo;
import pe.luislopez.bi.dto.Dtos.Dia;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.dto.Dtos.Salud;
import pe.luislopez.bi.repository.LeadRepository;
import pe.luislopez.bi.repository.VentaRepository;
import lombok.RequiredArgsConstructor;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Service;

/** Indicadores del mes. Los cálculos los hace MongoDB; aquí solo se arma la respuesta. */
@Service
@RequiredArgsConstructor
public class MetricasService {
    static final String[] DIAS = {"lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"};
    private static final int POR_PAGINA = 20;

    private final MongoTemplate mongo;
    private final LeadRepository leads;
    private final VentaRepository ventas;

    List<Document> agregar(String coleccion, String pipeline, Map<String, Object> valores) {
        return mongo.getCollection(coleccion).aggregate(Pipelines.de(pipeline, valores)).into(new ArrayList<>());
    }

    static long n(Document d, String campo) {
        Object v = d.get(campo);
        return v instanceof Number num ? num.longValue() : 0;
    }

    static double pct(long parte, long total) {
        return total == 0 ? 0 : Math.round(parte * 1000.0 / total) / 10.0;
    }

    public Resumen resumen(String mes) {
        validarMes(mes);
        // Consultas derivadas de Spring Data: el nombre del método ES la consulta.
        long totalLeads = leads.countByMes(mes);
        long deAnuncio = leads.countByMesAndOrigenTipo(mes, "anuncio");
        long calificados = leads.countByMesAndCalificadoTrue(mes);
        long compraron = leads.countByMesAndComproTrue(mes);
        long totalVentas = ventas.countByMes(mes);
        List<Document> u = agregar("ventas", Pipelines.UNIDADES, Map.of("__MES__", mes));
        long unidades = u.isEmpty() ? 0 : n(u.get(0), "unidades");
        return new Resumen(mes, totalLeads, deAnuncio, pct(deAnuncio, totalLeads), calificados, compraron,
                pct(compraron, totalLeads), totalVentas, CapiService.por100(totalVentas, totalLeads), unidades);
    }

    public List<Etapa> embudo(String mes) {
        validarMes(mes);
        List<Document> r = agregar("leads", Pipelines.EMBUDO, Map.of("__MES__", mes));
        Document d = r.isEmpty() ? new Document() : r.get(0);
        long total = n(d, "llegaron");
        return List.of(
                new Etapa("llegaron", "Escribieron", total, total == 0 ? 0 : 100),
                new Etapa("interes", "Mostraron interés", n(d, "interes"), pct(n(d, "interes"), total)),
                new Etapa("listos", "Listos para comprar", n(d, "listos"), pct(n(d, "listos"), total)),
                new Etapa("compraron", "Compraron", n(d, "compraron"), pct(n(d, "compraron"), total)));
    }

    public Dias dias(String mes) {
        validarMes(mes);
        Map<Integer, Dia> porDia = new LinkedHashMap<>();
        for (int i = 1; i <= 7; i++) {
            porDia.put(i, new Dia(i, DIAS[i - 1], 0, 0));
        }
        for (Document d : agregar("ventas", Pipelines.VENTAS_POR_DIA, Map.of("__MES__", mes))) {
            int num = d.get("_id", Document.class).getInteger("diaNum");
            porDia.put(num, new Dia(num, DIAS[num - 1], n(d, "ventas"), n(d, "unidades")));
        }
        List<Dia> lista = new ArrayList<>(porDia.values());
        Dia ganador = lista.stream().max(Comparator.comparingLong(Dia::ventas)).orElse(null);
        return new Dias(lista, ganador);
    }

    public List<Celda> calor(String mes) {
        validarMes(mes);
        return agregar("ventas", Pipelines.MAPA_DE_CALOR, Map.of("__MES__", mes)).stream()
                .map(d -> {
                    Document id = d.get("_id", Document.class);
                    return new Celda(id.getInteger("diaNum"), id.getInteger("hora"), n(d, "ventas"));
                })
                .sorted(Comparator.comparingInt(Celda::diaNum).thenComparingInt(Celda::hora))
                .toList();
    }

    public List<Categoria> categorias(String mes) {
        validarMes(mes);
        List<Document> r = agregar("ventas", Pipelines.CATEGORIAS, Map.of("__MES__", mes));
        long total = r.stream().mapToLong(d -> n(d, "unidades")).sum();
        return r.stream()
                .map(d -> new Categoria(d.getString("_id"), n(d, "ventas"), n(d, "unidades"),
                        pct(n(d, "unidades"), total)))
                .toList();
    }

    public Anuncios anuncios(String mes) {
        validarMes(mes);
        Document f = agregar("leads", Pipelines.ANUNCIOS_Y_PLATAFORMAS, Map.of("__MES__", mes)).get(0);
        return new Anuncios(conteos(f.getList("anuncios", Document.class)),
                conteos(f.getList("plataformas", Document.class)));
    }

    private static List<Conteo> conteos(List<Document> docs) {
        return docs.stream()
                .map(d -> new Conteo(d.getString("_id"), n(d, "leads"), n(d, "compraron"),
                        pct(n(d, "compraron"), n(d, "leads"))))
                .toList();
    }

    public List<Asesora> asesoras(String mes) {
        validarMes(mes);
        return agregar("leads", Pipelines.ASESORAS, Map.of("__MES__", mes)).stream()
                .map(d -> new Asesora(d.getString("_id"), n(d, "leads"), n(d, "calificados"), n(d, "compraron"),
                        pct(n(d, "compraron"), n(d, "leads"))))
                .toList();
    }

    public Pagina<Cliente> clientes(String mes, Boolean compro, String q, int pagina) {
        validarMes(mes);
        Document filtro = new Document("mes", mes);
        if (compro != null) {
            filtro.append("compro", compro);
        }
        if (q != null && !q.isBlank()) {
            filtro.append("nombre", new Document("$regex", Pattern.quote(q.trim())).append("$options", "i"));
        }
        int p = Math.max(pagina, 1);
        long total = mongo.getCollection("leads").countDocuments(filtro);
        List<Cliente> filas = agregar("leads", Pipelines.CLIENTES, Map.of(
                "__FILTRO__", filtro, "__SALTAR__", (p - 1) * POR_PAGINA, "__LIMITE__", POR_PAGINA))
                .stream().map(MetricasService::cliente).toList();
        return new Pagina<>(total, p, POR_PAGINA, filas);
    }

    private static Cliente cliente(Document d) {
        Document o = d.get("origen", Document.class);
        String origen = "directo".equals(o.getString("tipo")) ? "directo"
                : (o.getString("plataforma") == null ? "anuncio" : o.getString("plataforma"));
        return new Cliente(d.getString("nombre"), d.get("llegada", Date.class).toInstant(), d.getString("dia"),
                origen, o.getString("anuncio"), d.getString("etapa"), d.getString("asesora"),
                d.getBoolean("compro", false), d.getInteger("diasHastaCompra"),
                d.getList("categorias", String.class));
    }

    public Salud salud() {
        Document info = mongo.executeCommand("{ buildInfo: 1 }");
        return new Salud(true, info.getString("version"), mongo.getDb().getName(), leads.count(), ventas.count());
    }
}
