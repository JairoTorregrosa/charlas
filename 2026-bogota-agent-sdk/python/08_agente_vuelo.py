"""08 · el asistente de viaje completo — todas las piezas a la vez.

  tool propia   hoy()                    fecha fija, para que la demo no dependa del reloj
  MCP           gmail                    buscar y leer, en un proceso aparte
  skill         buscar-vuelo             el procedimiento, en markdown
  hook          PreToolUse               el guardrail que ve los argumentos
  topes         max_turns · max_budget   lo que evita que un bucle te cueste dinero

La respuesta correcta es el vuelo de LATAM del jueves 24 de septiembre a las
06:15, BOG → MDE, reserva ABC123. Los otros tres correos son trampas.

Cada corrida deja salidas/<fecha-hora>/eventos.jsonl (todos los eventos, crudos)
y transcript.md (llamada por llamada: qué le entró al LLM y qué respondió).

    uv run python 08_agente_vuelo.py
    uv run python 08_agente_vuelo.py "¿Tengo algo reservado para el fin de semana?"
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions, HookMatcher, ResultError, create_sdk_mcp_server, query, tool,
)

from mostrar import linea
from observar import Bitacora

AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    return {"content": [{"type": "text", "text": "sábado 19 de septiembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])


async def guardrail(entrada, tool_use_id, contexto):
    """Deja pasar todo salvo los correos que el dueño marcó como privados."""
    if entrada["tool_input"].get("id") != "c4":
        return {}
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "El correo c4 es privado. Responde solo sobre vuelos.",
    }}


async def main(pedido=PREGUNTA):
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        cwd=str(AQUI / "workspace"),
        setting_sources=["project"],
        skills=["buscar-vuelo"],
        tools=["Skill"],
        mcp_servers={
            "reloj": RELOJ,
            "gmail": {"command": sys.executable, "args": [str(AQUI / "gmail_mcp.py")]},
        },
        allowed_tools=["Skill", "mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
        hooks={"PreToolUse": [HookMatcher(matcher="mcp__gmail__leer", hooks=[guardrail])]},
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=12,           # al tocar el tope: mensaje de error Y excepción. Es a propósito.
        max_budget_usd=0.25,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {pedido}\n")
    bitacora = Bitacora(AQUI / "salidas", pedido=pedido, system_prompt=SYSTEM_PROMPT)
    try:
        async for m in query(prompt=pedido, options=opciones):
            bitacora.anotar(m)
            linea(m)
    except ResultError as e:
        print(f"\n[corte] {e}")
    finally:
        bitacora.cerrar()


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else PREGUNTA))
