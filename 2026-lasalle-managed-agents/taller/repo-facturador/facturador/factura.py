"""Totales de una factura de venta en pesos colombianos."""
from dataclasses import dataclass
from decimal import Decimal

IVA_GENERAL = Decimal("0.19")


@dataclass(frozen=True)
class Linea:
    descripcion: str
    cantidad: int
    precio_unitario: Decimal  # en pesos, antes de IVA
    descuento_pct: Decimal = Decimal("0")  # 0.10 es un 10 %
    excluida_iva: bool = False


@dataclass(frozen=True)
class Totales:
    bruto: int
    descuentos: int
    subtotal: int
    iva: int
    retencion: int
    total: int


def a_pesos(valor: Decimal) -> int:
    """Redondea al peso más cercano."""
    return round(float(valor))


def calcular(lineas: list[Linea], retencion_pct: Decimal = Decimal("0")) -> Totales:
    bruto = sum((l.cantidad * l.precio_unitario for l in lineas), Decimal("0"))
    descuentos = sum((l.cantidad * l.precio_unitario * l.descuento_pct for l in lineas), Decimal("0"))
    subtotal = bruto - descuentos

    # Base gravada: lo que paga IVA.
    base_gravada = sum((l.cantidad * l.precio_unitario for l in lineas if not l.excluida_iva), Decimal("0"))
    iva = base_gravada * IVA_GENERAL
    retencion = subtotal * retencion_pct

    return Totales(
        bruto=a_pesos(bruto),
        descuentos=a_pesos(descuentos),
        subtotal=a_pesos(subtotal),
        iva=a_pesos(iva),
        retencion=a_pesos(retencion),
        total=a_pesos(subtotal + iva - retencion),
    )
