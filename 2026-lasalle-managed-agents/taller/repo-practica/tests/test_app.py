import pytest

from cafe.app import crear_app


@pytest.fixture
def cliente():
    return crear_app().test_client()


def test_salud(cliente):
    assert cliente.get("/salud").json == {"ok": True}


def test_pedidos_de_un_cliente(cliente):
    r = cliente.get("/pedidos", query_string={"correo": "laura.mejia@example.com"})
    assert r.status_code == 200
    assert [p["numero"] for p in r.json] == ["CO-1001"]


def test_pedidos_sin_correo(cliente):
    assert cliente.get("/pedidos").status_code == 400


def test_correo_sin_pedidos(cliente):
    assert cliente.get("/pedidos", query_string={"correo": "nadie@example.com"}).json == []


def test_descargar_factura(cliente):
    r = cliente.get("/facturas/FV-2301.txt")
    assert r.status_code == 200
    assert b"FV-2301" in r.data


def test_factura_que_no_existe(cliente):
    assert cliente.get("/facturas/FV-9999.txt").status_code == 404
