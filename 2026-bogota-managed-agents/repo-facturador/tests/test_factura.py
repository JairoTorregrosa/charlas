from decimal import Decimal as D

from facturador import Linea, a_pesos, calcular


def test_una_linea_gravada():
    t = calcular([Linea("Teclado", 1, D("100000"))])
    assert (t.subtotal, t.iva, t.total) == (100000, 19000, 119000)


def test_varias_unidades():
    t = calcular([Linea("Cable USB-C", 3, D("12500"))])
    assert (t.bruto, t.iva, t.total) == (37500, 7125, 44625)


def test_el_iva_va_despues_del_descuento():
    t = calcular([Linea("Monitor", 1, D("800000"), descuento_pct=D("0.10"))])
    assert (t.descuentos, t.subtotal, t.iva, t.total) == (80000, 720000, 136800, 856800)


def test_linea_excluida_no_paga_iva():
    t = calcular([Linea("Arroz 5 kg", 2, D("18000"), excluida_iva=True)])
    assert (t.subtotal, t.iva, t.total) == (36000, 0, 36000)


def test_factura_mixta_con_descuento():
    t = calcular([
        Linea("Portátil", 1, D("2500000"), descuento_pct=D("0.05")),
        Linea("Libro", 2, D("45000"), excluida_iva=True),
    ])
    assert (t.subtotal, t.iva, t.total) == (2465000, 451250, 2916250)


def test_retencion_sobre_el_subtotal():
    t = calcular([Linea("Asesoría", 1, D("1000000"))], retencion_pct=D("0.11"))
    assert (t.iva, t.retencion, t.total) == (190000, 110000, 1080000)


def test_las_mitades_suben():
    assert a_pesos(D("28.5")) == 29
    assert a_pesos(D("10.5")) == 11


def test_iva_con_mitad_de_peso():
    t = calcular([Linea("Borrador", 1, D("150"))])
    assert t.iva == 29  # 150 × 19 % = 28,5


def test_factura_vacia():
    t = calcular([])
    assert (t.bruto, t.iva, t.total) == (0, 0, 0)
