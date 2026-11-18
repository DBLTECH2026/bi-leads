package pe.luislopez.bi;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.hamcrest.Matchers;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

/** La API es pública y recibe los filtros por la URL, igual que en el ejemplo del curso. */
@AutoConfigureMockMvc
class ApiPublicaTest extends BaseMongoTest {
    @Autowired
    MockMvc mvc;

    @Test
    void resumenConVariosFiltrosEnLaUrl() throws Exception {
        mvc.perform(get("/api/resumen").param("meses", "2026-09,2026-10").param("origenes", "facebook,instagram")
                        .param("dias", "6,7"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.periodo").value("setiembre y octubre 2026"))
                .andExpect(jsonPath("$.leads").isNumber());
    }

    @Test
    void opcionesListaLosValoresDeCadaFiltro() throws Exception {
        mvc.perform(get("/api/opciones"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.meses.length()").value(4))
                .andExpect(jsonPath("$.dias.length()").value(7));
    }

    @Test
    void mesMalEscritoEs400() throws Exception {
        mvc.perform(get("/api/resumen").param("meses", "octubre")).andExpect(status().isBadRequest());
    }

    @Test
    void saludMuestraLaVersionDeMongo() throws Exception {
        mvc.perform(get("/api/salud"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.mongo").value(Matchers.startsWith("8.")))
                .andExpect(jsonPath("$.baseDatos").value("bi_leads_test"));
    }
}
