package pe.luislopez.bi;

import static org.assertj.core.api.Assertions.assertThat;

import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.service.CapiService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

class CapiServiceTest extends BaseMongoTest {
    @Autowired
    CapiService capi;

    @Test
    void comparaJulioAgostoContraSetiembreOctubre() {
        Comparativo c = capi.comparativo();
        assertThat(c.meses()).extracting(MesCapi::mes).containsExactly("2026-07", "2026-08", "2026-09", "2026-10");
        assertThat(c.meses()).extracting(MesCapi::periodo).containsExactly("antes", "antes", "despues", "despues");
        c.meses().forEach(m -> assertThat(m.leads()).isEqualTo(contar(leadsEjemplo, delMes(m.mes()))));
        assertThat(c.antes().leads() + c.despues().leads()).isEqualTo(leadsEjemplo.size());
        assertThat(c.nota()).contains("Correlación");
    }
}
