package pe.luislopez.bi.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pe.luislopez.bi.dto.Dtos.Salud;
import pe.luislopez.bi.service.MetricasService;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class SaludController {
    private final MetricasService metricas;

    /** Sirve para comprobar que la API está viva y conectada a MongoDB. */
    @GetMapping("/salud")
    public Salud salud() {
        return metricas.salud();
    }
}
