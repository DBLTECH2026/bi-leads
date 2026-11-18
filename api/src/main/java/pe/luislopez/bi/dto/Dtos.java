package pe.luislopez.bi.dto;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/** Respuestas de la API. Records: inmutables y se convierten solos a JSON. Ninguno lleva montos. */
public final class Dtos {
    private Dtos() {
    }

    public record Resumen(String periodo, long leads, long deAnuncio, double pctAnuncio, long calificados,
                          long compraron, double conversion, long ventas, double ventasPor100, long unidades) {
    }

    public record Etapa(String clave, String nombre, long cantidad, double pctDelTotal) {
    }

    public record Dia(int diaNum, String dia, long ventas, long unidades) {
    }

    public record Dias(List<Dia> dias, Dia ganador) {
    }

    public record Celda(int diaNum, int hora, long ventas) {
    }

    public record Categoria(String categoria, long ventas, long unidades, double pctUnidades) {
    }

    public record MesCapi(String mes, String periodo, long leads, long calificados, double pctCalificados,
                          long compraron, long ventas, double ventasPor100, Double medianaDias, long leadsCapi) {
    }

    public record Periodo(String periodo, long leads, long ventas, double ventasPor100, double pctCalificados) {
    }

    public record Comparativo(List<MesCapi> meses, Periodo antes, Periodo despues, double variacionPct,
                              String nota) {
    }

    public record Conteo(String nombre, long leads, long compraron, double conversion) {
    }

    public record Anuncios(List<Conteo> anuncios, List<Conteo> origenes) {
    }

    public record Asesora(String asesora, long leads, long calificados, long compraron, double conversion) {
    }

    public record Cliente(String nombre, Instant llegada, String dia, String origen, String anuncio,
                          String etapa, String asesora, boolean compro, Integer diasHastaCompra,
                          List<String> categoriasCompradas) {
    }

    public record Pagina<T>(long total, int pagina, int porPagina, List<T> filas) {
    }

    public record Hallazgo(String icono, String texto) {
    }

    /** Un dato que sobresale; «filtro» es el filtro que se aplica al hacerle clic (puede ir vacío). */
    public record Destacado(String clave, String icono, String titulo, String valor, String detalle,
                            Map<String, Object> filtro) {
    }

    public record Opcion(String valor, String etiqueta, long cantidad) {
    }

    public record Opciones(List<Opcion> meses, List<Opcion> rubros, List<Opcion> origenes, List<Opcion> asesoras,
                           List<Opcion> dias) {
    }

    public record Salud(boolean ok, String mongo, String baseDatos, long leads, long ventas) {
    }
}
