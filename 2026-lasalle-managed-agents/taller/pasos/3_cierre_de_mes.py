"""Caso 3 · El cierre de mes.

Primer día hábil de octubre. La contadora de Café Origen necesita la
conciliación bancaria de septiembre: cruzar las facturas que salieron del ERP
con el extracto del banco. Los dos archivos vienen como salen en la vida real.

Qué aprendes:
- Skills: el agente carga la skill xlsx de Anthropic para entregar un Excel de
  verdad, con hojas y formato, no un CSV.
- Outcomes: en vez de un mensaje, le das el resultado que esperas y una rúbrica.
  Un evaluador, con su propio contexto, revisa el entregable contra la rúbrica y
  le devuelve al agente lo que falta, hasta que cumple o se acaban las rondas.

Uso: uv run pasos/3_cierre_de_mes.py
"""
from taller.config import DATOS, MODELO, cliente
from taller.recursos import bajar_salidas, guardar_agente, guardar_entorno, resumen_costo, subir_archivo
from taller.sesion import conversar

CIERRE = DATOS / "cierre"

# La rúbrica describe cómo se ve un buen entregable, no las respuestas. Cada
# criterio tiene que poder calificarse solo, con un sí o un no.
RUBRICA = """\
# Conciliación bancaria de septiembre

## Archivo
- Existe /mnt/session/outputs/conciliacion_septiembre.xlsx y abre sin errores.
- Tiene las hojas Resumen, Conciliadas, Pendientes, Banco sin factura y Gastos bancarios.

## Facturas
- Las facturas anuladas no se cuentan como cuentas por cobrar.
- Ninguna factura aparece dos veces, aunque la exportación del ERP la repita.
- El total facturado del Resumen se calcula desde las facturas válidas y no copia la fila TOTAL del ERP.
- Cada factura válida aparece en exactamente una hoja: Conciliadas o Pendientes.
- Un pago parcial deja la factura en Pendientes con el saldo que falta.

## Banco
- Cada movimiento del extracto queda clasificado: pago de factura, pago sin factura, gasto bancario u otro ingreso.
- Un pago que cubre varias facturas se asocia con todas ellas.
- Un pago sin número de factura se asocia por cliente y valor, y la hoja lo marca como asociado sin referencia.
- El GMF (4x1000) se reporta separado de las demás comisiones.

## Cuadre
- En el Resumen: total conciliado + total pendiente = total facturado válido.
- Las cifras van en pesos colombianos sin decimales.

## Memo
- Existe /mnt/session/outputs/memo.md, de máximo 12 líneas, con los hallazgos que la contadora tiene que revisar a mano.
"""

DESCRIPCION = """\
Haz la conciliación bancaria de septiembre de 2026 de Café Origen SAS.
Las facturas están en /mnt/session/uploads/facturas_septiembre.xlsx (exportadas del ERP)
y el extracto del banco en /mnt/session/uploads/extracto_septiembre.csv.
Entrega el Excel y el memo que describe la rúbrica en /mnt/session/outputs/."""

client = cliente()

entorno = guardar_entorno(client, "oficina", {
    "type": "cloud",
    "networking": {"type": "limited", "allow_package_managers": True},
    "packages": {"pip": ["pandas", "openpyxl"]},
})

agente = guardar_agente(client, "contable", {
    "name": "taller-analista-contable",
    "model": MODELO,
    "system": (
        "Eres analista contable en una empresa colombiana. Trabajas con Python y pandas. "
        "Revisas la calidad de los datos antes de cruzarlos y nunca fuerzas un cuadre: "
        "si algo no cuadra, lo reportas. Responde en español."
    ),
    "tools": [{
        "type": "agent_toolset_20260401",
        "configs": [
            {"name": "web_fetch", "enabled": False},
            {"name": "web_search", "enabled": False},
        ],
    }],
    "skills": [{"type": "anthropic", "skill_id": "xlsx"}],
})

subidos = [subir_archivo(client, CIERRE / n) for n in ("facturas_septiembre.xlsx", "extracto_septiembre.csv")]

sesion = client.beta.sessions.create(
    agent=agente,
    environment_id=entorno,
    title="caso 3 · cierre de mes",
    resources=[
        {"type": "file", "file_id": subidos[0], "mount_path": "facturas_septiembre.xlsx"},
        {"type": "file", "file_id": subidos[1], "mount_path": "extracto_septiembre.csv"},
    ],
    budget={"type": "limit", "max_list_cost": {"amount": "150", "currency": "USD"}},
)
print(f"sesión {sesion.id}\n")

resultado = conversar(client, sesion.id, eventos=[{
    "type": "user.define_outcome",
    "description": DESCRIPCION,
    "rubric": {"type": "text", "content": RUBRICA},
    "max_iterations": 3,
}])

print(f"\nterminó: {resultado.motivo} · rondas del evaluador: {' → '.join(resultado.evaluaciones) or 'ninguna'}")
bajar_salidas(client, sesion.id, subidos=tuple(subidos))
print(resumen_costo(client, sesion.id))
print(f"mírala paso a paso en https://platform.claude.com/sessions/{sesion.id}")
