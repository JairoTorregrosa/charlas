# facturador

Calcula los totales de una factura de venta en pesos colombianos: subtotal,
descuentos, IVA, retención en la fuente y total a pagar.

Reglas que el código tiene que cumplir:

- El IVA general es del 19 % y se calcula sobre el valor **después** del descuento.
- Las líneas excluidas de IVA no suman a la base gravada.
- La retención en la fuente se calcula sobre el subtotal (después de descuentos y antes de IVA).
- Cada valor se redondea al peso más cercano. Las mitades suben: 28,5 queda en 29.

```sh
python -m pytest
```
