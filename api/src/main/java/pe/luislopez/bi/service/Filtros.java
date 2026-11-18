package pe.luislopez.bi.service;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

import lombok.RequiredArgsConstructor;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import pe.luislopez.bi.dto.Filtro;

/** Traduce el Filtro del dashboard a un $match de MongoDB para cada colección. */
@Component
@RequiredArgsConstructor
public class Filtros {
    private static final Pattern MES = Pattern.compile("^[0-9]{4}-(0[1-9]|1[0-2])$");

    private final MongoTemplate mongo;

    public static void validar(Filtro f) {
        for (String mes : f.meses()) {
            if (!MES.matcher(mes).matches()) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "mes debe tener la forma AAAA-MM: " + mes);
            }
        }
        for (Integer dia : f.dias()) {
            if (dia == null || dia < 1 || dia > 7) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "día debe ir de 1 (lunes) a 7 (domingo)");
            }
        }
    }

    private static Document en(List<?> valores) {
        return new Document("$in", valores);
    }

    /** $match para la colección leads (el día y el mes son los de llegada del cliente). */
    public Document leads(Filtro f) {
        validar(f);
        Document d = new Document();
        if (!f.meses().isEmpty()) {
            d.append("mes", en(f.meses()));
        }
        if (!f.origenes().isEmpty()) {
            d.append("origen.canal", en(f.origenes()));
        }
        if (!f.asesoras().isEmpty()) {
            d.append("asesora", en(f.asesoras()));
        }
        if (!f.dias().isEmpty()) {
            d.append("diaNum", en(f.dias()));
        }
        if (f.compro() != null) {
            d.append("compro", f.compro());
        }
        if (!f.rubros().isEmpty()) {
            // Clientes que compraron alguno de esos rubros (en cualquier fecha)
            List<String> ids = mongo.getCollection("ventas")
                    .distinct("leadId", new Document("categorias", en(f.rubros())).append("leadId", new Document("$ne", null)),
                            String.class)
                    .into(new ArrayList<>());
            d.append("_id", en(ids));
        }
        return d;
    }

    /** $match para la colección ventas (el día y el mes son los de la compra). */
    public Document ventas(Filtro f) {
        validar(f);
        if (Boolean.FALSE.equals(f.compro())) {
            return new Document("_id", new Document("$exists", false)); // «no compraron» no tiene ventas
        }
        Document d = new Document();
        if (!f.meses().isEmpty()) {
            d.append("mes", en(f.meses()));
        }
        if (!f.rubros().isEmpty()) {
            d.append("categorias", en(f.rubros()));
        }
        if (!f.origenes().isEmpty()) {
            d.append("origen", en(f.origenes()));
        }
        if (!f.asesoras().isEmpty()) {
            d.append("asesora", en(f.asesoras()));
        }
        if (!f.dias().isEmpty()) {
            d.append("diaNum", en(f.dias()));
        }
        return d;
    }

    /** Une un filtro con una condición extra sin pisarla (p. ej. compro=false y luego compro=true da 0). */
    public static Document y(Document filtro, Document extra) {
        return new Document("$and", List.of(filtro, extra));
    }
}
