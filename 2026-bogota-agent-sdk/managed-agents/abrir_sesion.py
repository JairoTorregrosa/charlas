"""Abre una sesión, manda la pregunta y va imprimiendo los eventos.

Una sesión es una instancia del agente corriendo dentro de un entorno. El
sandbox empieza a aprovisionarse al crearla, no al primer mensaje.

Dos cosas que hay que hacer en este orden:
  1. abrir el stream
  2. mandar el mensaje
Al revés se pierden los primeros eventos: solo llega lo que se emite después
de abrir el stream.

    uv run python abrir_sesion.py
    uv run python abrir_sesion.py "¿Dónde me quedo en Medellín?"
"""

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from bandeja import MENSAJE

load_dotenv()                                      # managed-agents/.env: AGENT_ID, ENVIRONMENT_ID, SKILL_ID
load_dotenv(__import__("pathlib").Path(__file__).resolve().parent.parent / ".env")   # .env de la raíz del kit: ANTHROPIC_API_KEY
cliente = Anthropic()

pedido = sys.argv[1] if len(sys.argv) > 1 else MENSAJE

sesion = cliente.beta.sessions.create(
    agent=os.environ["AGENT_ID"],                 # el id solo: fija la última versión del agente
    environment_id=os.environ["ENVIRONMENT_ID"],
    title="Taller Bogotá · próximo vuelo",
    # Tope duro. El monto va en centavos, como string, y solo en USD.
    budget={"type": "limit", "max_list_cost": {"amount": "50", "currency": "USD"}},
)
carpeta = Path(__file__).parent / "salidas" / sesion.id
carpeta.mkdir(parents=True, exist_ok=True)
print(f"sesión {sesion.id}\n")

# Todo evento queda guardado, crudo y en orden, en salidas/<sesión>/eventos.jsonl
with (carpeta / "eventos.jsonl").open("w") as bitacora, cliente.beta.sessions.events.stream(sesion.id) as stream:
    cliente.beta.sessions.events.send(
        sesion.id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": pedido}]}],
    )
    for evento in stream:
        bitacora.write(evento.model_dump_json() + "\n")
        bitacora.flush()
        match evento.type:
            case "agent.message":
                for bloque in evento.content:
                    if bloque.type == "text":
                        print(f"EL AGENTE DICE  {bloque.text}")
            case "agent.thinking":
                print("EL AGENTE PIENSA")
            case "agent.tool_use":
                print(f"EL AGENTE PIDE  {evento.name} {json.dumps(evento.input, ensure_ascii=False)[:140]}")
            case "agent.tool_result":
                print("LA TOOL RESPONDE")
            case "session.usage":
                u = evento.usage
                print(f"USO             {u.active_seconds:.1f} s activos · {u.output_tokens} tokens de salida · {u.list_cost.amount} centavos de USD")
            case "session.error":
                print(f"ERROR           {evento}")
            case "session.status_idle":
                # Una sesión que termina su trabajo queda `idle`, no `terminated`.
                print(f"\nFIN             la sesión quedó idle · eventos en {carpeta}/eventos.jsonl")
                break
