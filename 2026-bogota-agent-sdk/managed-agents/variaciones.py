"""Tres variaciones del mismo agente, para comparar qué cambia cuando cambias la definición.

  solo-lectura   toolset con todo apagado salvo read, glob y grep: le pides bash y no puede
  sin-chat       un pedido, deja un archivo en el sandbox y termina: un agente no necesita chat
  tacaño         tope de 1 centavo de USD por sesión: el budget corta

Cada sesión guarda todos sus eventos en salidas/<sesión>/eventos.jsonl.

    uv run python variaciones.py            # las tres
    uv run python variaciones.py sin-chat   # una
"""

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from bandeja import CORREOS

load_dotenv()                                      # managed-agents/.env: AGENT_ID, ENVIRONMENT_ID, SKILL_ID
load_dotenv(__import__("pathlib").Path(__file__).resolve().parent.parent / ".env")   # .env de la raíz del kit: ANTHROPIC_API_KEY
cliente = Anthropic()
AQUI = Path(__file__).parent.resolve()
SYSTEM_PROMPT = "Eres un asistente personal. Respondes en español, corto y con datos. No adivines."
TODO = [{"type": "agent_toolset_20260401"}]
SOLO_LECTURA = [{"type": "agent_toolset_20260401", "default_config": {"enabled": False},
                 "configs": [{"name": n, "enabled": True} for n in ("read", "glob", "grep")]}]

VARIACIONES = {
    "solo-lectura": dict(tools=SOLO_LECTURA, centavos="50",
                         pedido="Corre `python3 --version` con bash y dime qué sale."),
    "sin-chat": dict(tools=TODO, centavos="50",
                     pedido=f"Esta es mi bandeja:\n{CORREOS}\n\nHoy es sábado 19 de septiembre de 2026. "
                            "Escribe /tmp/itinerario.md con mi próximo vuelo y mi hotel, y muéstrame el archivo con cat."),
    "tacaño": dict(tools=TODO, centavos="1",
                   pedido="Escribe y corre con bash un script que imprima los primeros 200 números primos, "
                          "luego explícame el algoritmo en diez párrafos."),
}


def correr(nombre, v):
    print(f"\n=== {nombre} ===")
    agente = cliente.beta.agents.create(name=f"Variación · {nombre}", model="claude-sonnet-5",
                                        system=SYSTEM_PROMPT, tools=v["tools"])
    sesion = cliente.beta.sessions.create(
        agent=agente.id, environment_id=os.environ["ENVIRONMENT_ID"], title=f"Taller Bogotá · {nombre}",
        budget={"type": "limit", "max_list_cost": {"amount": v["centavos"], "currency": "USD"}})
    carpeta = AQUI / "salidas" / sesion.id
    carpeta.mkdir(parents=True, exist_ok=True)
    print(f"agente {agente.id} · sesión {sesion.id} · tope {v['centavos']} centavos")
    with (carpeta / "eventos.jsonl").open("w") as bitacora, cliente.beta.sessions.events.stream(sesion.id) as stream:
        cliente.beta.sessions.events.send(
            sesion.id, events=[{"type": "user.message", "content": [{"type": "text", "text": v["pedido"]}]}])
        for e in stream:
            bitacora.write(e.model_dump_json() + "\n")
            bitacora.flush()
            match e.type:
                case "agent.tool_use":
                    print(f"  PIDE  {e.name} {json.dumps(e.input, ensure_ascii=False)[:110]}")
                case "agent.message":
                    for b in e.content:
                        if b.type == "text":
                            print(f"  DICE  {b.text[:400]}")
                case "session.error":
                    print(f"  ERROR {e.error}")
                case "session.status_idle" | "session.status_terminated":
                    print(f"  FIN   {e.type} · {getattr(e, 'stop_reason', None)}")
                    break
    u = cliente.beta.sessions.retrieve(sesion.id).usage
    print(f"  USO   {u.active_seconds:.1f} s · salida {u.output_tokens} tokens · {u.list_cost.amount} centavos")


for nombre in (sys.argv[1:] or VARIACIONES):
    correr(nombre, VARIACIONES[nombre])
