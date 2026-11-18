package pe.luislopez.bi;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@AutoConfigureMockMvc
class AccesoTest extends BaseMongoTest {
    @Autowired
    MockMvc mvc;

    @Test
    void sinTokenEs401() throws Exception {
        mvc.perform(get("/api/resumen")).andExpect(status().isUnauthorized());
    }

    @Test
    void claveIncorrectaEs401() throws Exception {
        mvc.perform(post("/api/ingresar").contentType(MediaType.APPLICATION_JSON).content("{\"clave\":\"mala\"}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void conLaClaveCorrectaSeVenLosDatos() throws Exception {
        String cuerpo = mvc.perform(post("/api/ingresar").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"clave\":\"clave-de-prueba\"}"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        Matcher m = Pattern.compile("\"token\":\"([^\"]+)\"").matcher(cuerpo);
        org.assertj.core.api.Assertions.assertThat(m.find()).isTrue();
        mvc.perform(get("/api/resumen").header("Authorization", "Bearer " + m.group(1)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.mes").value(MES))
                .andExpect(jsonPath("$.leads").isNumber());
    }

    @Test
    void saludEsLibreYMuestraLaVersionDeMongo() throws Exception {
        mvc.perform(get("/api/salud"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.mongo").value(org.hamcrest.Matchers.startsWith("8.")))
                .andExpect(jsonPath("$.baseDatos").value("bi_leads_test"));
    }
}
