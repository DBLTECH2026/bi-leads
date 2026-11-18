package pe.luislopez.bi;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;

import org.bson.BsonString;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.server.ResponseStatusException;
import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.dto.Filtro;
import pe.luislopez.bi.service.MetricasService;

class MetricasServiceTest extends BaseMongoTest {
    private static final Filtro OCTUBRE = Filtro.deMeses(MES);

    @Autowired
    MetricasService metricas;

    @Test
    void resumenCuadraConElConteoEnJava() {
        Resumen r = metricas.resumen(OCTUBRE);
        assertThat(r.leads()).isEqualTo(contar(leadsEjemplo, delMes(MES)));
        assertThat(r.compraron()).isEqualTo(contar(leadsEjemplo, delMes(MES).and(compro())));
        assertThat(r.ventas()).isEqualTo(contar(ventasEjemplo, delMes(MES)));
        assertThat(r.periodo()).isEqualTo("octubre 2026");
    }

    @Test
    void diasCuentaCadaDiaYEligeAlGanador() {
        Dias d = metricas.dias(Filtro.todo());
        assertThat(d.dias()).hasSize(7);
        d.dias().forEach(dia -> assertThat(dia.ventas()).isEqualTo(
                contar(ventasEjemplo, v -> v.getInt32("diaNum").getValue() == dia.diaNum())));
        assertThat(d.ganador().dia()).isEqualTo("sábado"); // el ejemplo lo fija a propósito
    }

    @Test
    void embudoNuncaCrece() {
        List<Etapa> e = metricas.embudo(Filtro.todo());
        for (int i = 1; i < e.size(); i++) {
            assertThat(e.get(i).cantidad()).isLessThanOrEqualTo(e.get(i - 1).cantidad());
        }
    }

    @Test
    void filtrosMultiplesSeCombinan() {
        Filtro f = new Filtro(List.of("2026-09", MES), null, List.of("directo"), null, null, null);
        long esperado = contar(leadsEjemplo, delMes("2026-09").or(delMes(MES))
                .and(l -> l.getDocument("origen").getString("canal").getValue().equals("directo")));
        assertThat(metricas.resumen(f).leads()).isEqualTo(esperado);
    }

    @Test
    void filtroPorRubroSoloCuentaEsasVentas() {
        Filtro f = new Filtro(null, List.of("BARBERÍA"), null, null, null, null);
        long esperado = contar(ventasEjemplo, v -> v.getArray("categorias").contains(new BsonString("BARBERÍA")));
        assertThat(metricas.resumen(f).ventas()).isEqualTo(esperado).isPositive();
    }

    @Test
    void noCompraronNoTieneVentas() {
        Filtro f = new Filtro(null, null, null, null, null, false);
        assertThat(metricas.resumen(f).ventas()).isZero();
        assertThat(metricas.resumen(f).compraron()).isZero();
        assertThat(metricas.resumen(f).leads()).isEqualTo(contar(leadsEjemplo, compro().negate()));
    }

    @Test
    void clientesQueCompraronTraenSusRubrosConLookup() {
        Pagina<Cliente> p = metricas.clientes(new Filtro(null, null, null, null, null, true), null, 1);
        assertThat(p.total()).isEqualTo(contar(leadsEjemplo, compro()));
        assertThat(p.filas()).allSatisfy(c -> assertThat(c.categoriasCompradas()).isNotEmpty());
    }

    @Test
    void buscarPorNombreNoDistingueMayusculas() {
        Pagina<Cliente> p = metricas.clientes(Filtro.todo(), "torres", 1);
        assertThat(p.filas()).isNotEmpty().allSatisfy(c -> assertThat(c.nombre()).containsIgnoringCase("torres"));
    }

    @Test
    void mesMalEscritoEsError400() {
        assertThatThrownBy(() -> metricas.resumen(Filtro.deMeses("octubre")))
                .isInstanceOf(ResponseStatusException.class);
    }
}
