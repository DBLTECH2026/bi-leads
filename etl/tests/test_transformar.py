from datetime import datetime, timezone

from etl import transformar as t


def test_utc_a_lima_cambia_de_dia():
    f = t.a_lima("2026-10-01T04:59:00.000Z")
    assert (f.year, f.month, f.day, f.hour) == (2026, 9, 30, 23)


def test_erp_local_se_lee_como_lima():
    f = t.erp_a_lima("2026-10-01 09:21:55")
    assert f.astimezone(timezone.utc).hour == 14


def test_campos_de_fecha():
    c = t.campos_fecha(t.a_lima("2026-10-06T20:00:00Z"))  # martes 6-oct, 15:00 Lima
    assert c == {"mes": "2026-10", "dia": "martes", "diaNum": 2, "hora": 15}


def test_periodo_capi_por_mes_completo():
    assert t.periodo_capi(t.a_lima("2026-08-29T15:00:00Z")) == "antes"
    assert t.periodo_capi(t.a_lima("2026-08-31T15:00:00Z")) == "antes"
    assert t.periodo_capi(t.a_lima("2026-09-01T15:00:00Z")) == "despues"


def test_raiz_de_categoria():
    padres = {124: None, 125: 124, 126: 125, 151: None}
    assert t.raiz(126, padres) == 124
    assert t.raiz(999, padres) is None


def test_rubro_prefiere_el_principal_y_luego_la_prioridad():
    nombres = {124: "BARBERÍA", 133: "SALÓN", 151: "MARCAS"}
    assert t.elegir_rubro([151, 133, 124], principal=133, nombres=nombres) == "SALÓN"
    assert t.elegir_rubro([151, 133, 124], principal=151, nombres=nombres) == "BARBERÍA"
    assert t.elegir_rubro([151], principal=None, nombres=nombres) == "OTROS"


def test_seudonimos_por_id():
    s = t.seudonimos([5, 3, 4, 3])
    assert s == {3: "Asesora A", 4: "Asesora B", 5: "Asesora C"}


def test_nombre_limpio_quita_numeros_largos():
    assert t.nombre_limpio(None, "51987654321") == "Sin nombre"
    assert t.nombre_limpio("  Carlos   Quispe ", "x") == "Carlos Quispe"
    assert t.nombre_limpio(None, "Ana 987654321") == "Ana"
    assert t.nombre_limpio(None, "") == "Sin nombre"
    assert t.nombre_limpio(None, "luana14@gmail.com") == "Sin nombre"
    assert t.nombre_limpio(None, "Luana luana14@gmail") == "Luana"


def test_hash_estable_dentro_de_una_corrida():
    h = t.Hasheador("sal")
    assert h("L", 10) == h("L", 10)
    assert h("L", 10) != h("L", 11)
    assert h("L", 10).startswith("L-")


def test_dias_hasta_compra():
    a = datetime(2026, 10, 1, 10, tzinfo=t.LIMA)
    b = datetime(2026, 10, 4, 9, tzinfo=t.LIMA)
    assert t.dias_entre(a, b) == 2


def test_sin_marca_quita_el_nombre_de_la_empresa():
    assert t.sin_marca("Maximiza tu Inversión con ACME") == "Maximiza tu Inversión"
    assert t.sin_marca("ACME Group") is None
    assert t.sin_marca("Mobiliario Premium con Envío Seguro") == "Mobiliario Premium con Envío Seguro"
    assert t.nombre_limpio(None, "Acme Group") == "Sin nombre"
    assert t.nombre_limpio(None, "Elia Rojas") == "Elia Rojas"
    assert t.nombre_limpio(None, "Acme_Group") == "Sin nombre"
    assert t.sin_marca("Silla Ultracme") == "Silla Ultracme"
