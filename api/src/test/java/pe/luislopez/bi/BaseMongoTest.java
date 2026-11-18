package pe.luislopez.bi;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.function.Predicate;

import org.bson.BsonArray;
import org.bson.BsonDocument;
import org.bson.BsonValue;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.MongoTemplate;

/**
 * Usa la base bi_leads_test del MongoDB local, cargada con datos/ejemplo (datos inventados).
 * Requiere MongoDB corriendo en 127.0.0.1:27017.
 */
@SpringBootTest(properties = {
        "spring.mongodb.uri=mongodb://127.0.0.1:27017/bi_leads_test",
        "bi.clave=clave-de-prueba",
        "bi.secreto=secreto-de-prueba"})
public abstract class BaseMongoTest {
    protected static final String MES = "2026-10";
    protected static List<BsonDocument> leadsEjemplo;
    protected static List<BsonDocument> ventasEjemplo;

    @Autowired
    protected MongoTemplate mongo;

    @BeforeEach
    void cargarEjemplo() throws IOException {
        if (leadsEjemplo != null) {
            return;
        }
        leadsEjemplo = leer("leads");
        ventasEjemplo = leer("ventas");
        reemplazar("leads", leadsEjemplo);
        reemplazar("ventas", ventasEjemplo);
    }

    private static List<BsonDocument> leer(String nombre) throws IOException {
        String json = Files.readString(Path.of("..", "datos", "ejemplo", nombre + ".json"));
        return BsonArray.parse(json).stream().map(BsonValue::asDocument).toList();
    }

    private void reemplazar(String coleccion, List<BsonDocument> docs) {
        var c = mongo.getCollection(coleccion).withDocumentClass(BsonDocument.class);
        c.drop();
        c.insertMany(docs);
    }

    /** Conteo hecho en Java, sin MongoDB: sirve para comprobar lo que calcula el pipeline. */
    protected static long contar(List<BsonDocument> docs, Predicate<BsonDocument> condicion) {
        return docs.stream().filter(condicion).count();
    }

    protected static Predicate<BsonDocument> delMes(String mes) {
        return d -> d.getString("mes").getValue().equals(mes);
    }

    protected static Predicate<BsonDocument> compro() {
        return d -> d.getBoolean("compro").getValue();
    }
}
