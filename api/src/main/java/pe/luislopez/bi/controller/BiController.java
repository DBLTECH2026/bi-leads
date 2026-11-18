package pe.luislopez.bi.controller;

import java.util.List;

import pe.luislopez.bi.dto.Dtos.Anuncios;
import pe.luislopez.bi.dto.Dtos.Asesora;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Hallazgo;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.service.CapiService;
import pe.luislopez.bi.service.HallazgosService;
import pe.luislopez.bi.service.MetricasService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Endpoints del dashboard. Si no llega ?mes=, se usa el mes por defecto (octubre 2026). */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class BiController {
    private final MetricasService metricas;
    private final CapiService capi;
    private final HallazgosService hallazgos;
    private final String mesDefecto;

    public BiController(MetricasService metricas, CapiService capi, HallazgosService hallazgos,
                        @Value("${bi.mes-por-defecto}") String mesDefecto) {
        this.metricas = metricas;
        this.capi = capi;
        this.hallazgos = hallazgos;
        this.mesDefecto = mesDefecto;
    }

    private String mes(String mes) {
        return mes == null || mes.isBlank() ? mesDefecto : mes;
    }

    @GetMapping("/resumen")
    public Resumen resumen(@RequestParam(required = false) String mes) {
        return metricas.resumen(mes(mes));
    }

    @GetMapping("/embudo")
    public List<Etapa> embudo(@RequestParam(required = false) String mes) {
        return metricas.embudo(mes(mes));
    }

    @GetMapping("/compras/dias")
    public Dias dias(@RequestParam(required = false) String mes) {
        return metricas.dias(mes(mes));
    }

    @GetMapping("/compras/calor")
    public List<Celda> calor(@RequestParam(required = false) String mes) {
        return metricas.calor(mes(mes));
    }

    @GetMapping("/compras/categorias")
    public List<Categoria> categorias(@RequestParam(required = false) String mes) {
        return metricas.categorias(mes(mes));
    }

    @GetMapping("/capi/comparativo")
    public Comparativo comparativo() {
        return capi.comparativo();
    }

    @GetMapping("/anuncios/top")
    public Anuncios anuncios(@RequestParam(required = false) String mes) {
        return metricas.anuncios(mes(mes));
    }

    @GetMapping("/asesoras")
    public List<Asesora> asesoras(@RequestParam(required = false) String mes) {
        return metricas.asesoras(mes(mes));
    }

    @GetMapping("/clientes")
    public Pagina<Cliente> clientes(@RequestParam(required = false) String mes,
                                    @RequestParam(required = false) Boolean compro,
                                    @RequestParam(required = false) String q,
                                    @RequestParam(defaultValue = "1") int pagina) {
        return metricas.clientes(mes(mes), compro, q, pagina);
    }

    @GetMapping("/hallazgos")
    public List<Hallazgo> hallazgos(@RequestParam(required = false) String mes) {
        return hallazgos.hallazgos(mes(mes));
    }
}
