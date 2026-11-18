package pe.luislopez.bi.service;

import static pe.luislopez.bi.service.MetricasService.nombreMes;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pe.luislopez.bi.dto.Dtos.Asesora;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Conteo;
import pe.luislopez.bi.dto.Dtos.Destacado;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.dto.Filtro;

/**
 * «Filtros inteligentes»: lo que más sobresale con los filtros actuales. Cada destacado trae el filtro que lo
 * aísla, así el dashboard puede aplicarlo con un clic (p. ej. «Mes con más ventas: agosto» → meses=2026-08).
 */
@Service
@RequiredArgsConstructor
public class DestacadosService {
    /** Para comparar conversiones solo se toman grupos con al menos estos leads. */
    static final int MINIMO_LEADS = 30;

    private final MetricasService metricas;
    private final CapiService capi;

    public List<Destacado> destacados(Filtro f) {
        List<Destacado> d = new ArrayList<>();

        capi.porMes(f).stream().filter(m -> m.ventas() > 0).max(Comparator.comparingLong(MesCapi::ventas))
                .ifPresent(m -> d.add(new Destacado("mes", "calendar-check", "Mes con más ventas", nombreMes(m.mes()),
                        m.ventas() + " ventas · " + m.ventasPor100() + " por 100 leads",
                        Map.of("meses", List.of(m.mes())))));

        Dias dias = metricas.dias(f);
        if (dias.ganador() != null) {
            d.add(new Destacado("dia", "calendar-days", "Día con más compras", dias.ganador().dia(),
                    dias.ganador().ventas() + " ventas", Map.of("dias", List.of(dias.ganador().diaNum()))));
        }

        Map<Integer, Long> porHora = new TreeMap<>();
        for (Celda c : metricas.calor(f)) {
            porHora.merge(c.hora(), c.ventas(), Long::sum);
        }
        porHora.entrySet().stream().max(Map.Entry.comparingByValue())
                .ifPresent(e -> d.add(new Destacado("hora", "clock", "Hora pico de compra",
                        e.getKey() + ":00 – " + (e.getKey() + 1) + ":00", e.getValue() + " ventas", Map.of())));

        List<Categoria> cats = metricas.categorias(f);
        if (!cats.isEmpty()) {
            Categoria c = cats.get(0);
            d.add(new Destacado("rubro", "armchair", "Rubro más vendido", c.categoria(),
                    c.pctUnidades() + " % de las unidades", Map.of("rubros", List.of(c.categoria()))));
        }

        metricas.anuncios(f).origenes().stream().filter(o -> o.leads() >= MINIMO_LEADS && o.compraron() > 0)
                .max(Comparator.comparingDouble(Conteo::conversion))
                .ifPresent(o -> d.add(new Destacado("origen", "megaphone", "Origen que mejor convierte", o.nombre(),
                        o.conversion() + " % compra (" + o.compraron() + " de " + o.leads() + ")",
                        Map.of("origenes", List.of(o.nombre())))));

        metricas.asesoras(f).stream()
                .filter(a -> a.leads() >= MINIMO_LEADS && a.compraron() > 0 && a.asesora().startsWith("Asesora"))
                .max(Comparator.comparingDouble(Asesora::conversion))
                .ifPresent(a -> d.add(new Destacado("asesora", "headset", "Asesora que mejor cierra", a.asesora(),
                        a.conversion() + " % compra (" + a.compraron() + " de " + a.leads() + ")",
                        Map.of("asesoras", List.of(a.asesora())))));
        return d;
    }
}
