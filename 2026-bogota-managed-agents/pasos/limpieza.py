"""Limpieza · Borra lo que creaste en el taller.

Sesiones (y sus outputs), environments, memory stores y archivos se borran.
Los agents no se pueden borrar: se archivan. Archivar no tiene vuelta atrás.
Lo que no se logre borrar queda anotado para la próxima corrida.

Uso: uv run pasos/limpieza.py
"""
import json
import time

import anthropic

from taller import estado
from taller.config import BETA, RAIZ, cliente

client = cliente()
creados = estado.ids()
fallas: list[str] = []


def intentar(descripcion: str, accion) -> bool:
    try:
        accion()
        print(f"  ✓ {descripcion}")
        return True
    except anthropic.NotFoundError:
        print(f"  · {descripcion}: ya no existía")
        return True
    except anthropic.APIStatusError as e:
        print(f"  ✗ {descripcion}: {e.status_code} {e.message}")
        fallas.append(descripcion)
        return False


def detener(session_id: str) -> None:
    """Una sesión en running no se puede borrar: primero se interrumpe y se espera."""
    client.beta.sessions.events.send(session_id, events=[{"type": "user.interrupt"}])
    for _ in range(15):
        if client.beta.sessions.retrieve(session_id).status != "running":
            return
        time.sleep(2)


agentes = {v for k, v in creados.items() if k.startswith("agente:")}
# El vuln-patcher lo crea ant apply: aquí se borran sus sesiones; el agent, el
# environment, la skill y el vault se archivan con ant (mira el README).
lock = RAIZ / "agente" / "claude-lock.json"
if lock.exists():
    agentes |= {v["id"] for k, v in json.loads(lock.read_text())["resources"].items() if "agents/" in k}

print("Sesiones del taller")
for sesion in client.beta.sessions.list():
    if sesion.agent.id not in agentes:
        continue
    if sesion.status == "running":
        detener(sesion.id)
    intentar(f"sesión {sesion.id} ({sesion.title})", lambda s=sesion.id: client.beta.sessions.delete(s))
sesiones_ok = not fallas

borrar = {
    "entorno:": ("environment", lambda r: client.beta.environments.delete(r)),
    "memoria:": ("memory store", lambda r: client.beta.memory_stores.delete(r)),
    "archivo:": ("archivo", lambda r: client.beta.files.delete(r, betas=[BETA])),
}
print("Environments, memory stores y archivos")
for clave, recurso_id in creados.items():
    for prefijo, (nombre, accion) in borrar.items():
        if clave.startswith(prefijo) and intentar(f"{nombre} {recurso_id}", lambda a=accion, r=recurso_id: a(r)):
            estado.olvidar(clave)

# Los agents se archivan al final y solo si sus sesiones se borraron: sin el ID
# del agent, una corrida futura no encontraría las sesiones que quedaron.
print("Agents (se archivan)")
if sesiones_ok:
    for clave, recurso_id in creados.items():
        if clave.startswith("agente:") and intentar(f"agent {recurso_id}", lambda r=recurso_id: client.beta.agents.archive(r)):
            estado.olvidar(clave)
else:
    print("  · no se archivan hasta que todas sus sesiones estén borradas")

if fallas:
    print(f"\nQuedaron {len(fallas)} sin borrar. Vuelve a correr la limpieza en un minuto.")
    raise SystemExit(1)
estado.ARCHIVO.unlink(missing_ok=True)
print("\nListo. Revisa en https://platform.claude.com que no quede nada corriendo.")
