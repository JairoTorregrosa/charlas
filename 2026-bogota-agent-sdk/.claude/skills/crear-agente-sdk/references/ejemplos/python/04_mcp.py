"""04 · MCP — tools que no escribiste tú, en un proceso aparte.

`gmail_mcp.py` es un servidor MCP falso con la bandeja de correo: buscar y leer.
El SDK lo lanza como subproceso y habla con él por stdio. Para el agente no hay
diferencia entre esas tools y `hoy()`: las ve igual, con nombre mcp__gmail__*.

Dos cosas que salvan la demo en una sala:
  strict_mcp_config=True   sin esto entran los conectores de tu cuenta claude.ai
                           (Gmail real, Drive, Calendar) y el agente los usa
  mcp_servers inline       porque strict_mcp_config también ignora el .mcp.json
                           de la carpeta: si quieres un servidor, decláralo aquí

Mira en el ARRANQUE el estado de cada servidor: connected · pending · needs-auth.

    uv run python 04_mcp.py
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

from mostrar import linea

AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    return {"content": [{"type": "text", "text": "sábado 19 de septiembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])


async def main():
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        mcp_servers={
            "reloj": RELOJ,                                             # dentro de este proceso
            "gmail": {"command": sys.executable,                         # proceso aparte, por stdio
                      "args": [str(AQUI / "gmail_mcp.py")]},
        },
        allowed_tools=["mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
        setting_sources=[],
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=10,
        max_budget_usd=0.20,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    async for m in query(prompt=PREGUNTA, options=opciones):
        linea(m)


asyncio.run(main())
