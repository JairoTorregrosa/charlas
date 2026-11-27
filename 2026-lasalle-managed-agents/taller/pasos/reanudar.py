"""Retomar una sesión después de que se cayó el wifi.

La sesión siguió trabajando en el servidor. Este script espera a que termine,
muestra el último mensaje del agente y baja sus outputs. Si la sesión quedó
esperando una aprobación o una custom tool, te dice cuál y la puedes responder
desde la Console.

Uso: uv run pasos/reanudar.py <session_id>
"""
import sys
import time

from taller.config import cliente
from taller.recursos import bajar_salidas, resumen_costo

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
session_id = sys.argv[1]
client = cliente()

while (sesion := client.beta.sessions.retrieve(session_id)).status in ("running", "rescheduling"):
    print(f"  · sigue {sesion.status}…", flush=True)
    time.sleep(10)

eventos = list(client.beta.sessions.events.list(session_id))
ultimo = next((e for e in reversed(eventos) if e.type == "agent.message"), None)
if ultimo is not None:
    print("\n".join(b.text for b in ultimo.content if b.type == "text"))

idle = next((e for e in reversed(eventos) if e.type == "session.status_idle"), None)
motivo = idle.stop_reason.type if idle else sesion.status
print(f"\nestado: {sesion.status} ({motivo})")
if motivo == "requires_action":
    print("La sesión espera una respuesta tuya. Contéstala en "
          f"https://platform.claude.com/sessions/{session_id} o con: ant beta:sessions connect {session_id}")
bajar_salidas(client, session_id)
print(resumen_costo(client, session_id))
