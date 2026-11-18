package pe.luislopez.bi.repository;

import pe.luislopez.bi.model.Lead;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface LeadRepository extends MongoRepository<Lead, String> {
    long countByMes(String mes);

    long countByMesAndComproTrue(String mes);

    long countByMesAndCalificadoTrue(String mes);

    long countByMesAndOrigenTipo(String mes, String tipo);
}
