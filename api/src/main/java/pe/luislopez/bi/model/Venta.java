package pe.luislopez.bi.model;

import java.time.Instant;
import java.util.List;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

/** Un comprobante del ERP (boleta o factura). Sin montos. */
@Data
@Document("ventas")
public class Venta {
    @Id
    private String id;
    private Instant fecha;
    private String mes;
    private String dia;
    private Integer diaNum;
    private Integer hora;
    private String tipo;
    private String cliente;
    private String canal;           // whatsapp | otro
    private String leadId;
    private List<String> categorias;
    private List<Item> items;
    private boolean capiEnviado;

    @Data
    public static class Item {
        private String producto;
        private String categoria;   // BARBERÍA, SALÓN, SPA, HERRAMIENTAS, CALZADO, REPUESTOS…
        private int cantidad;
    }
}
