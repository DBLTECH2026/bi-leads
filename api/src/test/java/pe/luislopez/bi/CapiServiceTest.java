package pe.luislopez.bi;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Comparator;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.Destacado;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.dto.Filtro;
import pe.luislopez.bi.service.CapiService;
import pe.luislopez.bi.service.DestacadosService;

class CapiServiceTest extends BaseMongoTest {
    @Autowired
    CapiService capi;

    @Autowired
    DestacadosService destacados;

    @Test
    void comparaJulioAgostoContraSetiembreOctubreAunqueSeFiltreUnMes() {
        Comparativo c = capi.comparativo(Filtro.deMeses(MES));
        assertThat(c.meses()).extracting(MesCapi::mes).containsExactly("2026-07", "2026-08", "2026-09", "2026-10");
        assertThat(c.meses()).extracting(MesCapi::periodo).containsExactly("antes", "antes", "despues", "despues");
        c.meses().forEach(m -> assertThat(m.leads()).isEqualTo(contar(leadsEjemplo, delMes(m.mes()))));
        assertThat(c.nota()).contains("Correlación");
    }

    @Test
    void elDestacadoMesConMasVentasCoincideYTraeSuFiltro() {
        String esperado = List.of("2026-07", "2026-08", "2026-09", "2026-10").stream()
                .max(Comparator.comparingLong(m -> contar(ventasEjemplo, delMes(m)))).orElseThrow();
        Destacado mes = destacados.destacados(Filtro.todo()).stream()
                .filter(d -> d.clave().equals("mes")).findFirst().orElseThrow();
        assertThat(mes.filtro()).containsEntry("meses", List.of(esperado));
    }
}
