package pe.luislopez.bi.service;

import static pe.luislopez.bi.service.MetricasService.n;
import static pe.luislopez.bi.service.MetricasService.pct;
import static pe.luislopez.bi.service.MetricasService.por100;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import lombok.RequiredArgsConstructor;
import org.bson.Document;
import org.springframework.stereotype.Service;
import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.dto.Dtos.Periodo;
import pe.luislopez.bi.dto.Filtro;

/** Mes a mes y antes/después de Meta CAPI (activa desde el 30-ago-2026): jul-ago contra sep-oct. */
@Service
@RequiredArgsConstructor
public class CapiService {
    public static final String NOTA =
            "Correlación, no causalidad: también cambian la temporada y la inversión en anuncios.";

    private final MetricasService metricas;
    private final Filtros filtros;

    /** Leads, ventas y conversión de cada mes, con los filtros aplicados. */
    public List<MesCapi> porMes(Filtro f) {
        Map<String, Long> ventasPorMes = new HashMap<>();
        for (Document d : metricas.agregar("ventas", Pipelines.VENTAS_POR_MES, filtros.ventas(f))) {
            ventasPorMes.put(d.getString("_id"), n(d, "ventas"));
        }
        return metricas.agregar("leads", Pipelines.LEADS_POR_MES, filtros.leads(f)).stream()
                .map(d -> {
                    String mes = d.getString("_id");
                    long leads = n(d, "leads");
                    long ventas = ventasPorMes.getOrDefault(mes, 0L);
                    Object mediana = d.get("medianaDias");
                    return new MesCapi(mes, d.getString("periodo"), leads, n(d, "calificados"),
                            pct(n(d, "calificados"), leads), n(d, "compraron"), ventas, por100(ventas, leads),
                            mediana instanceof Number m ? m.doubleValue() : null, n(d, "leadsCapi"));
                })
                .toList();
    }

    /** Siempre compara los 4 meses: usa los demás filtros (rubro, origen, asesora…) pero no los meses. */
    public Comparativo comparativo(Filtro f) {
        List<MesCapi> meses = porMes(f.sinMeses());
        Periodo antes = periodo("antes", meses);
        Periodo despues = periodo("despues", meses);
        double variacion = antes.ventasPor100() == 0 ? 0
                : Math.round((despues.ventasPor100() / antes.ventasPor100() - 1) * 1000) / 10.0;
        return new Comparativo(meses, antes, despues, variacion, NOTA);
    }

    private static Periodo periodo(String nombre, List<MesCapi> meses) {
        List<MesCapi> del = meses.stream().filter(m -> nombre.equals(m.periodo())).toList();
        long leads = del.stream().mapToLong(MesCapi::leads).sum();
        long ventas = del.stream().mapToLong(MesCapi::ventas).sum();
        long calificados = del.stream().mapToLong(MesCapi::calificados).sum();
        return new Periodo(nombre, leads, ventas, por100(ventas, leads), pct(calificados, leads));
    }
}
