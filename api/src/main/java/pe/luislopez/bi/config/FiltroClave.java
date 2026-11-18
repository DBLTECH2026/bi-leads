package pe.luislopez.bi.config;

import java.io.IOException;
import java.util.Set;

import pe.luislopez.bi.service.TokenService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** Todo /api/** pide el token, salvo ingresar y salud. Las peticiones OPTIONS (CORS) pasan libres. */
@Component
@RequiredArgsConstructor
public class FiltroClave extends OncePerRequestFilter {
    private static final Set<String> LIBRES = Set.of("/api/ingresar", "/api/salud");

    private final TokenService tokens;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest req) {
        String ruta = req.getRequestURI();
        return !ruta.startsWith("/api/") || LIBRES.contains(ruta) || "OPTIONS".equals(req.getMethod());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain cadena)
            throws ServletException, IOException {
        String cabecera = req.getHeader("Authorization");
        String token = cabecera != null && cabecera.startsWith("Bearer ") ? cabecera.substring(7) : null;
        if (tokens.valido(token)) {
            cadena.doFilter(req, res);
            return;
        }
        res.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setContentType("application/json;charset=UTF-8");
        res.getWriter().write("{\"error\":\"Ingresa la clave del dashboard\"}");
    }
}
