package pe.luislopez.bi.repository;

import pe.luislopez.bi.model.Venta;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface VentaRepository extends MongoRepository<Venta, String> {
    long countByMes(String mes);
}
