package pe.luislopez.bi.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.bson.Document;

/**
 * Aggregation pipelines escritos igual que en la pestaña "Aggregations" de MongoDB Compass.
 * "__FILTRO__" se reemplaza por el $match de los filtros DESPUÉS de parsear el JSON:
 * así un valor que llega por la URL nunca puede inyectar operadores.
 */
public final class Pipelines {
    private Pipelines() {
    }

    /** Parsea un arreglo JSON de etapas y reemplaza los marcadores por sus valores. */
    public static List<Document> de(String json, Map<String, Object> valores) {
        List<Document> etapas = Document.parse("{p:" + json + "}").getList("p", Document.class);
        List<Document> salida = new ArrayList<>();
        for (Document etapa : etapas) {
            salida.add((Document) reemplazar(etapa, valores));
        }
        return salida;
    }

    private static Object reemplazar(Object nodo, Map<String, Object> valores) {
        if (nodo instanceof String s && valores.containsKey(s)) {
            return valores.get(s);
        }
        if (nodo instanceof Document d) {
            Document copia = new Document();
            d.forEach((k, v) -> copia.append(k, reemplazar(v, valores)));
            return copia;
        }
        if (nodo instanceof List<?> lista) {
            return lista.stream().map(v -> reemplazar(v, valores)).toList();
        }
        return nodo;
    }

    // ---------- leads ----------

    public static final String EMBUDO = """
            [
              { $match: "__FILTRO__" },
              { $group: {
                  _id: null,
                  llegaron:  { $sum: 1 },
                  interes:   { $sum: { $cond: [ { $or: [
                                 { $not: [ { $in: [ "$etapa", [ "INACTIVO", "EN_CALIFICACION" ] ] } ] },
                                 "$calificado", "$compro" ] }, 1, 0 ] } },
                  listos:    { $sum: { $cond: [ "$calificado", 1, 0 ] } },
                  compraron: { $sum: { $cond: [ "$compro", 1, 0 ] } }
              } }
            ]""";

    /** Leads por mes (sirve para CAPI y para «ventas por mes»). */
    public static final String LEADS_POR_MES = """
            [
              { $match: "__FILTRO__" },
              { $group: {
                  _id: "$mes",
                  periodo:     { $first: "$capi.periodo" },
                  leads:       { $sum: 1 },
                  calificados: { $sum: { $cond: [ "$calificado", 1, 0 ] } },
                  compraron:   { $sum: { $cond: [ "$compro", 1, 0 ] } },
                  leadsCapi:   { $sum: { $cond: [ "$capi.leadEnviado", 1, 0 ] } },
                  medianaDias: { $median: { input: "$diasHastaCompra", method: "approximate" } }
              } },
              { $sort: { _id: 1 } }
            ]""";

    public static final String MEDIANA_DIAS = """
            [
              { $match: "__FILTRO__" },
              { $match: { diasHastaCompra: { $ne: null } } },
              { $group: { _id: null, mediana: { $median: { input: "$diasHastaCompra", method: "approximate" } } } }
            ]""";

    public static final String ANUNCIOS_Y_ORIGENES = """
            [
              { $match: "__FILTRO__" },
              { $facet: {
                  anuncios: [
                    { $match: { "origen.tipo": "anuncio", "origen.anuncio": { $ne: null } } },
                    { $group: { _id: "$origen.anuncio", leads: { $sum: 1 },
                                compraron: { $sum: { $cond: [ "$compro", 1, 0 ] } } } },
                    { $sort: { compraron: -1, leads: -1 } },
                    { $limit: 8 }
                  ],
                  origenes: [
                    { $group: { _id: "$origen.canal", leads: { $sum: 1 },
                                compraron: { $sum: { $cond: [ "$compro", 1, 0 ] } } } },
                    { $sort: { leads: -1 } }
                  ]
              } }
            ]""";

    public static final String ASESORAS = """
            [
              { $match: "__FILTRO__" },
              { $group: { _id: "$asesora", leads: { $sum: 1 },
                          calificados: { $sum: { $cond: [ "$calificado", 1, 0 ] } },
                          compraron:   { $sum: { $cond: [ "$compro", 1, 0 ] } } } },
              { $sort: { _id: 1 } }
            ]""";

    /** Clientes con lo que compraron: $lookup une cada lead con sus ventas. */
    public static final String CLIENTES = """
            [
              { $match: "__FILTRO__" },
              { $sort: { llegada: -1 } },
              { $skip: "__SALTAR__" },
              { $limit: "__LIMITE__" },
              { $lookup: { from: "ventas", localField: "_id", foreignField: "leadId", as: "compras" } },
              { $project: {
                  nombre: 1, llegada: 1, dia: 1, origen: 1, etapa: 1, asesora: 1, compro: 1, diasHastaCompra: 1,
                  categorias: { $setUnion: [ { $reduce: { input: "$compras.categorias", initialValue: [],
                                  in: { $concatArrays: [ "$$value", "$$this" ] } } }, [] ] }
              } }
            ]""";

    // ---------- ventas ----------

    public static final String UNIDADES = """
            [
              { $match: "__FILTRO__" },
              { $unwind: "$items" },
              { $group: { _id: null, unidades: { $sum: "$items.cantidad" } } }
            ]""";

    public static final String VENTAS_POR_DIA = """
            [
              { $match: "__FILTRO__" },
              { $group: { _id: { diaNum: "$diaNum", dia: "$dia" },
                          ventas: { $sum: 1 },
                          unidades: { $sum: { $sum: "$items.cantidad" } } } },
              { $sort: { "_id.diaNum": 1 } }
            ]""";

    public static final String MAPA_DE_CALOR = """
            [
              { $match: "__FILTRO__" },
              { $match: { hora: { $ne: null } } },
              { $group: { _id: { diaNum: "$diaNum", hora: "$hora" }, ventas: { $sum: 1 } } }
            ]""";

    public static final String CATEGORIAS = """
            [
              { $match: "__FILTRO__" },
              { $unwind: "$items" },
              { $group: { _id: "$items.categoria",
                          ventas: { $addToSet: "$_id" },
                          unidades: { $sum: "$items.cantidad" } } },
              { $project: { ventas: { $size: "$ventas" }, unidades: 1 } },
              { $sort: { unidades: -1 } }
            ]""";

    public static final String VENTAS_POR_MES = """
            [
              { $match: "__FILTRO__" },
              { $group: { _id: "$mes", ventas: { $sum: 1 }, unidades: { $sum: { $sum: "$items.cantidad" } } } },
              { $sort: { _id: 1 } }
            ]""";
}
