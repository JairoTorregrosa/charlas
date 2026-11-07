"""10 · salida estructurada — el agente entrega datos, no un párrafo.

El 08 responde con texto para una persona. Si la respuesta la va a leer otro
programa (un calendario, una base de datos, un bot), pídele un JSON con forma
fija: output_format con un JSON Schema. El SDK valida la respuesta contra el
schema y la deja en ResultMessage.structured_output, ya como dict de Python.

Mismo agente del 08 (tool, MCP, skill, topes), una sola diferencia: la forma de
la respuesta. Y un tope de dinero más bajo, para que veas que también corta.

    uv run python 10_salida_estructurada.py
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

import asyncio
import json
import sys
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions, ResultError, ResultMessage, create_sdk_mcp_server, query, tool,
)

from mostrar import linea

AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal que lee el correo del usuario.
Usa tus tools y skills; no adivines fechas ni reservas.
Si no encuentras un vuelo futuro, deja encontrado=false y los demás campos en null."""

VUELO = {
    "type": "object",
    "properties": {
        "encontrado": {"type": "boolean"},
        "aerolinea": {"type": ["string", "null"]},
        "origen": {"type": ["string", "null"], "description": "código IATA, p. ej. BOG"},
        "destino": {"type": ["string", "null"], "description": "código IATA, p. ej. MDE"},
        "fecha": {"type": ["string", "null"], "description": "AAAA-MM-DD"},
        "hora": {"type": ["string", "null"], "description": "HH:MM, 24 horas"},
        "reserva": {"type": ["string", "null"]},
    },
    "required": ["encontrado", "aerolinea", "origen", "destino", "fecha", "hora", "reserva"],
    "additionalProperties": False,
}


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    return {"content": [{"type": "text", "text": "sábado 7 de noviembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])


async def main(pedido=PREGUNTA):
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5-5",
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
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        output_format={"type": "json_schema", "schema": VUELO},   # ← la pieza nueva
        max_turns=12,
        max_budget_usd=0.25,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {pedido}\n")
    try:
        async for m in query(prompt=pedido, options=opciones):
            linea(m)
            if isinstance(m, ResultMessage) and m.structured_output is not None:
                vuelo = m.structured_output
                print("\nJSON VALIDADO (ResultMessage.structured_output)")
                print(json.dumps(vuelo, ensure_ascii=False, indent=2))
                if vuelo.get("encontrado"):
                    print(f"\n→ ya es un dict: vuelo['reserva'] = {vuelo['reserva']!r}")
    except ResultError as e:
        print(f"\n[corte] {e}")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else PREGUNTA))
