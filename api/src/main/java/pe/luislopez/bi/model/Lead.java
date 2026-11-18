package pe.luislopez.bi.model;

import java.time.Instant;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

/** Un cliente que escribió por WhatsApp (un chat nuevo del CRM). */
@Data
@Document("leads")
public class Lead {
    @Id
    private String id;
    private String nombre;
    private Instant llegada;
    private String mes;
    private String dia;
    private Integer diaNum;
    private Integer hora;
    private Origen origen;
    private Capi capi;
    private String etapa;
    private boolean calificado;
    private String asesora;
    private boolean compro;
    private Instant primeraCompra;
    private Integer diasHastaCompra;

    @Data
    public static class Origen {
        private String tipo;        // anuncio | directo
        private String plataforma;  // facebook | instagram | whatsapp | null
        private String anuncio;
        private boolean clickId;
    }

    @Data
    public static class Capi {
        private String periodo;     // antes | despues
        private boolean leadEnviado;
    }
}
