import pytest

from etl.guardas import DatoProhibido, revisar


def test_rechaza_campo_de_monto():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "V-1", "total": 10}])


def test_rechaza_campo_anidado_de_telefono():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "L-1", "origen": {"celular": "x"}}])


def test_rechaza_valor_con_forma_de_telefono():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "L-1", "nombre": "Juan 987654321"}])


def test_rechaza_valor_con_forma_de_dni():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "L-1", "nombre": "Juan 45678912"}])


def test_rechaza_correo():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "L-1", "nombre": "ana@gmail.com"}])


def test_rechaza_el_nombre_de_la_empresa():
    with pytest.raises(DatoProhibido):
        revisar([{"_id": "L-1", "origen": {"anuncio": "Ofertas ACME"}}])


def test_acepta_documento_limpio():
    revisar([{"_id": "L-12345678ab", "leadId": "L-99999999", "nombre": "Juan", "hora": 15,
              "items": [{"producto": "Sillón barbero", "cantidad": 2}]}])
