"""07 · un subagente — delegar para no ensuciar el contexto.

`lector-de-correos` busca y lee en la bandeja, y devuelve UNA frase. Su contexto
es propio: el padre nunca ve los 4 correos completos, solo el resumen. Eso es lo
que compra un subagente, además de poder correr varios en paralelo.

Lo único que viaja del padre al hijo es el prompt de la llamada a la tool `Agent`.
El hijo no ve la conversación del padre.

Dos detalles que confunden en vivo:
  - la tool aparece como "Agent" en el stream y como "Task" en la lista del ARRANQUE
  - los mensajes del hijo traen `parent_tool_use_id`; el impresor los marca [subagente]

    uv run python 07_subagente.py
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition, ClaudeAgentOptions, create_sdk_mcp_server, query, tool,
)

from mostrar import linea

AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    return {"content": [{"type": "text", "text": "sábado 19 de septiembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])

LECTOR = AgentDefinition(
    description="Lee la bandeja de correo y devuelve los vuelos que encuentre. "
                "Úsalo cuando haya que revisar correos.",
    prompt="Haz UNA sola búsqueda con el rango que te pidan y lee los correos que "
           "puedan ser vuelos. Devuelve una línea por vuelo: fecha, hora, ruta y "
           "código de reserva. No opines ni expliques el proceso.",
    tools=["mcp__gmail__buscar", "mcp__gmail__leer"],   # lo que no está aquí, no existe para él
    model="haiku",                                      # el hijo puede ser más barato que el padre
    maxTurns=8,                     # en Python los campos de varias palabras van en camelCase
    background=False,               # en primer plano, para verlo en el stream
)


async def main():
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        agents={"lector-de-correos": LECTOR},
        tools=["Agent"],
        mcp_servers={
            "reloj": RELOJ,
            "gmail": {"command": sys.executable, "args": [str(AQUI / "gmail_mcp.py")]},
        },
        allowed_tools=["Agent", "mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
        forward_subagent_text=True,        # sin esto solo verías sus tool calls
        setting_sources=[],
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=12,
        max_budget_usd=0.25,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    async for m in query(prompt=PREGUNTA, options=opciones):
        linea(m)


asyncio.run(main())
