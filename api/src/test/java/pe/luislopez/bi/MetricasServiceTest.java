package pe.luislopez.bi;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;

import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.service.MetricasService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.server.ResponseStatusException;

class MetricasServiceTest extends BaseMongoTest {
    @Autowired
    MetricasService metricas;

    @Test
    void resumenCuadraConElConteoEnJava() {
        Resumen r = metricas.resumen(MES);
        assertThat(r.leads()).isEqualTo(contar(leadsEjemplo, delMes(MES)));
        assertThat(r.compraron()).isEqualTo(contar(leadsEjemplo, delMes(MES).and(compro())));
        assertThat(r.ventas()).isEqualTo(contar(ventasEjemplo, delMes(MES)));
        assertThat(r.compraron()).isPositive();
    }

    @Test
    void diasCuentaCadaDiaYEligeAlGanador() {
        Dias d = metricas.dias(MES);
        assertThat(d.dias()).hasSize(7);
        d.dias().forEach(dia -> assertThat(dia.ventas()).isEqualTo(contar(ventasEjemplo,
                delMes(MES).and(v -> v.getInt32("diaNum").getValue() == dia.diaNum()))));
        long maximo = d.dias().stream().mapToLong(x -> x.ventas()).max().orElseThrow();
        assertThat(d.ganador().ventas()).isEqualTo(maximo);
        assertThat(d.ganador().dia()).isEqualTo("sábado"); // el ejemplo lo fija a propósito
    }

    @Test
    void embudoNuncaCrece() {
        List<Etapa> e = metricas.embudo(MES);
        for (int i = 1; i < e.size(); i++) {
            assertThat(e.get(i).cantidad()).isLessThanOrEqualTo(e.get(i - 1).cantidad());
        }
    }

    @Test
    void clientesFiltraYTraeLoQueCompraronConLookup() {
        Pagina<Cliente> p = metricas.clientes(MES, true, null, 1);
        assertThat(p.total()).isEqualTo(contar(leadsEjemplo, delMes(MES).and(compro())));
        assertThat(p.filas()).allSatisfy(c -> assertThat(c.categoriasCompradas()).isNotEmpty());
    }

    @Test
    void buscarPorNombreNoDistingueMayusculas() {
        Pagina<Cliente> p = metricas.clientes(MES, null, "torres", 1);
        assertThat(p.filas()).isNotEmpty().allSatisfy(c -> assertThat(c.nombre()).containsIgnoringCase("torres"));
    }

    @Test
    void mesInvalidoEsError400() {
        assertThatThrownBy(() -> metricas.resumen("octubre")).isInstanceOf(ResponseStatusException.class);
    }
}
