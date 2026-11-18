package pe.luislopez.bi.controller;

import pe.luislopez.bi.dto.Dtos.Ingreso;
import pe.luislopez.bi.dto.Dtos.Salud;
import pe.luislopez.bi.dto.Dtos.Token;
import pe.luislopez.bi.service.MetricasService;
import pe.luislopez.bi.service.TokenService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class AccesoController {
    private final TokenService tokens;
    private final MetricasService metricas;

    @PostMapping("/ingresar")
    public ResponseEntity<Token> ingresar(@RequestBody Ingreso ingreso) {
        if (!tokens.claveCorrecta(ingreso.clave())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
        return ResponseEntity.ok(new Token(tokens.emitir(), TokenService.DURACION_SEG));
    }

    /** Libre: sirve para comprobar que la API está viva y conectada a MongoDB. */
    @GetMapping("/salud")
    public Salud salud() {
        return metricas.salud();
    }
}
