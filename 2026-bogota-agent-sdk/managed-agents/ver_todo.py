"""Lista lo que hay en la cuenta: agentes, entornos y sesiones.

Con un id de sesión, además imprime su historial de eventos. El historial queda
guardado en el servidor, así que se puede leer completo después de que terminó.

    uv run python ver_todo.py
    uv run python ver_todo.py sesn_...
"""

import sys

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
cliente = Anthropic()


def bloque(titulo, filas):
    print(f"\n{titulo}")
    print("-" * len(titulo))
    for fila in filas or ["(vacío)"]:
        print(f"  {fila}")


bloque("AGENTES", [f"{a.id}  {a.name}  modelo={a.model.id}"
                   for a in cliente.beta.agents.list(limit=20)])

bloque("ENTORNOS", [f"{e.id}  {e.name}"
                    for e in cliente.beta.environments.list(limit=20)])

bloque("SESIONES RECIENTES", [f"{s.id}  {s.status:<12} {s.title}"
                              for s in cliente.beta.sessions.list(limit=10, order="desc")])

if len(sys.argv) > 1:
    sesion_id = sys.argv[1]
    bloque(f"EVENTOS DE {sesion_id}",
           [f"{e.type:<28} {str(getattr(e, 'name', '') or '')}"
            for e in cliente.beta.sessions.events.list(sesion_id, limit=100, order="asc")])
