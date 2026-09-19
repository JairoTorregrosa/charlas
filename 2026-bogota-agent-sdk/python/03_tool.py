"""03 · una tool propia — `hoy()`, una función tuya que el LLM puede llamar.

Tres piezas:
  @tool(nombre, descripción, esquema)   la descripción es lo que el LLM lee
                                        para decidir si la llama. Escríbela bien.
  create_sdk_mcp_server(...)            las empaqueta en un servidor MCP que vive
                                        dentro de este mismo proceso de Python
  mcp_servers={"reloj": RELOJ}          la clave "reloj" da el nombre completo
                                        de la tool: mcp__reloj__hoy

Y dos listas que se confunden todo el tiempo:
  tools          qué existe          (`[]` = ninguna nativa; el set base)
  allowed_tools  qué se aprueba solo (no restringe: solo evita la pregunta)

La fecha va fija a propósito: el mismo resultado hoy y el día del taller.

    uv run python 03_tool.py
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

from mostrar import linea

PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    print("      ⚙  corriendo hoy() en tu Python")
    return {"content": [{"type": "text", "text": "sábado 19 de septiembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])


async def main():
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        mcp_servers={"reloj": RELOJ},
        allowed_tools=["mcp__reloj__hoy"],   # quítalo y la corrida se queda esperando permiso
        setting_sources=[],
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=4,
        max_budget_usd=0.10,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    async for m in query(prompt=PREGUNTA, options=opciones):
        linea(m)


asyncio.run(main())
