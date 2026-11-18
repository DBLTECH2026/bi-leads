package pe.luislopez.bi.dto;

import java.time.YearMonth;
import java.time.format.TextStyle;
import java.util.List;
import java.util.Locale;

/**
 * Filtros múltiples del dashboard. Llegan por la URL, por ejemplo:
 * {@code ?meses=2026-09,2026-10&rubros=SALÓN&origenes=facebook,instagram&dias=6,7&compro=true}.
 * Una lista vacía significa "todos".
 */
public record Filtro(List<String> meses, List<String> rubros, List<String> origenes, List<String> asesoras,
                     List<Integer> dias, Boolean compro) {

    private static final Locale PE = Locale.forLanguageTag("es-PE");

    public Filtro {
        meses = limpio(meses);
        rubros = limpio(rubros);
        origenes = limpio(origenes);
        asesoras = limpio(asesoras);
        dias = dias == null ? List.of() : List.copyOf(dias);
    }

    private static List<String> limpio(List<String> valores) {
        return valores == null ? List.of() : valores.stream().map(String::trim).filter(v -> !v.isEmpty()).toList();
    }

    public static Filtro todo() {
        return new Filtro(null, null, null, null, null, null);
    }

    public static Filtro deMeses(String... meses) {
        return new Filtro(List.of(meses), null, null, null, null, null);
    }

    /** El mismo filtro pero con todos los meses (para comparar mes a mes, como en CAPI). */
    public Filtro sinMeses() {
        return new Filtro(null, rubros, origenes, asesoras, dias, compro);
    }

    /** Texto del periodo: «octubre 2026», «setiembre y octubre 2026» o «jul–oct 2026». */
    public String periodo() {
        if (meses.isEmpty()) {
            return "jul–oct 2026";
        }
        List<String> nombres = meses.stream().sorted()
                .map(m -> YearMonth.parse(m).getMonth().getDisplayName(TextStyle.FULL, PE)).toList();
        String anio = meses.stream().sorted().reduce((a, b) -> b).orElseThrow().substring(0, 4);
        if (nombres.size() == 1) {
            return nombres.get(0) + " " + anio;
        }
        return String.join(", ", nombres.subList(0, nombres.size() - 1)) + " y " + nombres.get(nombres.size() - 1)
                + " " + anio;
    }
}
