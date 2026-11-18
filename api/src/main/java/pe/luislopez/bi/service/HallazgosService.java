package pe.luislopez.bi.service;

import java.time.YearMonth;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

import pe.luislopez.bi.dto.Dtos.Anuncios;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.Conteo;
import pe.luislopez.bi.dto.Dtos.Dia;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Hallazgo;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.dto.Dtos.Resumen;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/** Convierte los números del mes en frases cortas (el "explicar" del dashboard). */
@Service
@RequiredArgsConstructor
public class HallazgosService {
    private static final Locale PE = Locale.forLanguageTag("es-PE");

    private final MetricasService metricas;
    private final CapiService capi;

    public List<Hallazgo> hallazgos(String mes) {
        Resumen r = metricas.resumen(mes);
        List<Hallazgo> h = new ArrayList<>();
        String nombreMes = YearMonth.parse(mes).getMonth().getDisplayName(TextStyle.FULL, PE);

        h.add(new Hallazgo("users", "En %s escribieron %s personas; el %s %% llegó por anuncios de Meta."
                .formatted(nombreMes, entero(r.leads()), dec(r.pctAnuncio()))));
        h.add(new Hallazgo("shopping-bag", "Compraron %s (%s %%): hubo %s ventas por cada 100 leads."
                .formatted(entero(r.compraron()), dec(r.conversion()), dec(r.ventasPor100()))));

        Dias d = metricas.dias(mes);
        if (d.ganador() != null && d.ganador().ventas() > 0) {
            List<String> sinVentas = d.dias().stream().filter(x -> x.ventas() == 0).map(Dia::dia).toList();
            String extra = sinVentas.isEmpty() ? "" : " Sin ventas: " + String.join(", ", sinVentas) + ".";
            h.add(new Hallazgo("calendar-days", "El %s fue el día con más compras (%d).%s"
                    .formatted(d.ganador().dia(), d.ganador().ventas(), extra)));
        }

        Map<Integer, Long> porHora = new TreeMap<>();
        for (Celda c : metricas.calor(mes)) {
            porHora.merge(c.hora(), c.ventas(), Long::sum);
        }
        porHora.entrySet().stream().max(Map.Entry.comparingByValue()).ifPresent(e ->
                h.add(new Hallazgo("clock", "La hora con más compras es de %d:00 a %d:00."
                        .formatted(e.getKey(), e.getKey() + 1))));

        List<Categoria> cats = metricas.categorias(mes);
        if (!cats.isEmpty()) {
            String segundo = cats.size() > 1
                    ? ", seguido de %s (%s %%)".formatted(cats.get(1).categoria(), dec(cats.get(1).pctUnidades()))
                    : "";
            h.add(new Hallazgo("armchair", "Lo más vendido fue %s (%s %% de las unidades)%s."
                    .formatted(cats.get(0).categoria(), dec(cats.get(0).pctUnidades()), segundo)));
        }

        Comparativo c = capi.comparativo();
        if (c.antes().leads() > 0 && c.despues().leads() > 0) {
            double cambioLeads = (c.despues().leads() * 1.0 / c.antes().leads() - 1) * 100;
            h.add(new Hallazgo("trending-up",
                    "Con CAPI llegan %s %% %s leads, pero las ventas por cada 100 leads pasaron de %s a %s (%s%s %%)."
                            .formatted(dec(Math.abs(cambioLeads)), cambioLeads < 0 ? "menos" : "más",
                                    dec(c.antes().ventasPor100()), dec(c.despues().ventasPor100()),
                                    c.variacionPct() >= 0 ? "+" : "", dec(c.variacionPct()))));
        }
        c.meses().stream().filter(m -> m.mes().equals(mes) && m.medianaDias() != null).findFirst()
                .map(MesCapi::medianaDias)
                .ifPresent(m -> h.add(new Hallazgo("timer",
                        "Quien compra lo decide rápido: la mitad compra en %s días o menos."
                                .formatted(dec(m)))));

        Anuncios a = metricas.anuncios(mes);
        a.anuncios().stream().max(Comparator.comparingLong(Conteo::compraron)).filter(x -> x.compraron() > 0)
                .ifPresent(x -> h.add(new Hallazgo("megaphone",
                        "El anuncio que más ventas trajo: «%s» (%d de %s leads compraron)."
                                .formatted(x.nombre(), x.compraron(), entero(x.leads())))));
        return h;
    }

    private static String entero(long v) {
        return String.format(PE, "%,d", v);
    }

    private static String dec(double v) {
        return v == Math.rint(v) ? String.format(PE, "%,d", (long) v) : String.format(PE, "%,.1f", v);
    }
}
