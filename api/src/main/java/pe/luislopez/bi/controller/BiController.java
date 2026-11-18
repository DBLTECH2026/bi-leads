package pe.luislopez.bi.controller;

import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pe.luislopez.bi.dto.Dtos.Anuncios;
import pe.luislopez.bi.dto.Dtos.Asesora;
import pe.luislopez.bi.dto.Dtos.Categoria;
import pe.luislopez.bi.dto.Dtos.Celda;
import pe.luislopez.bi.dto.Dtos.Cliente;
import pe.luislopez.bi.dto.Dtos.Comparativo;
import pe.luislopez.bi.dto.Dtos.Destacado;
import pe.luislopez.bi.dto.Dtos.Dias;
import pe.luislopez.bi.dto.Dtos.Etapa;
import pe.luislopez.bi.dto.Dtos.Hallazgo;
import pe.luislopez.bi.dto.Dtos.MesCapi;
import pe.luislopez.bi.dto.Dtos.Opciones;
import pe.luislopez.bi.dto.Dtos.Pagina;
import pe.luislopez.bi.dto.Dtos.Resumen;
import pe.luislopez.bi.dto.Filtro;
import pe.luislopez.bi.service.CapiService;
import pe.luislopez.bi.service.DestacadosService;
import pe.luislopez.bi.service.HallazgosService;
import pe.luislopez.bi.service.MetricasService;

/**
 * Endpoints del dashboard. Todos aceptan los mismos filtros por la URL (Spring los arma en un Filtro):
 * meses, rubros, origenes, asesoras, dias y compro. Sin filtros = jul–oct 2026 completo.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class BiController {
    private final MetricasService metricas;
    private final CapiService capi;
    private final HallazgosService hallazgos;
    private final DestacadosService destacados;

    @GetMapping("/opciones")
    public Opciones opciones() {
        return metricas.opciones();
    }

    @GetMapping("/resumen")
    public Resumen resumen(@ModelAttribute Filtro filtro) {
        return metricas.resumen(filtro);
    }

    @GetMapping("/destacados")
    public List<Destacado> destacados(@ModelAttribute Filtro filtro) {
        return destacados.destacados(filtro);
    }

    @GetMapping("/embudo")
    public List<Etapa> embudo(@ModelAttribute Filtro filtro) {
        return metricas.embudo(filtro);
    }

    @GetMapping("/compras/meses")
    public List<MesCapi> meses(@ModelAttribute Filtro filtro) {
        return capi.porMes(filtro);
    }

    @GetMapping("/compras/dias")
    public Dias dias(@ModelAttribute Filtro filtro) {
        return metricas.dias(filtro);
    }

    @GetMapping("/compras/calor")
    public List<Celda> calor(@ModelAttribute Filtro filtro) {
        return metricas.calor(filtro);
    }

    @GetMapping("/compras/categorias")
    public List<Categoria> categorias(@ModelAttribute Filtro filtro) {
        return metricas.categorias(filtro);
    }

    @GetMapping("/capi/comparativo")
    public Comparativo comparativo(@ModelAttribute Filtro filtro) {
        return capi.comparativo(filtro);
    }

    @GetMapping("/anuncios/top")
    public Anuncios anuncios(@ModelAttribute Filtro filtro) {
        return metricas.anuncios(filtro);
    }

    @GetMapping("/asesoras")
    public List<Asesora> asesoras(@ModelAttribute Filtro filtro) {
        return metricas.asesoras(filtro);
    }

    @GetMapping("/clientes")
    public Pagina<Cliente> clientes(@ModelAttribute Filtro filtro, @RequestParam(required = false) String q,
                                    @RequestParam(defaultValue = "1") int pagina) {
        return metricas.clientes(filtro, q, pagina);
    }

    @GetMapping("/hallazgos")
    public List<Hallazgo> hallazgos(@ModelAttribute Filtro filtro) {
        return hallazgos.hallazgos(filtro);
    }
}
