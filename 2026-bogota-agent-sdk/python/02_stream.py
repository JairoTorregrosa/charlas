"""02 · el stream — todo lo que pasa dentro del agente, mensaje por mensaje.

query() no devuelve un texto: devuelve un flujo. Cada vuelta del loop deja
mensajes en ese flujo y aquí los imprimimos todos con su etiqueta:

    ARRANQUE          el harness ya armó la sesión: modelo, tools, skills, mcp
    EL LLM PIDE       el modelo pidió una tool (tool_use)
    LA TOOL RESPONDE  el harness la ejecutó y le devolvió el resultado (tool_result)
    EL LLM DICE       texto para la persona (assistant message)
    RECIBO            el cierre: costo, duración y num_turns

La tool `hoy` está aquí solo para que haya algo que mirar; en 03 la desarmamos.

    uv run python 02_stream.py
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

from mostrar import linea

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
        tools=[],                                   # de las nativas, ninguna
        mcp_servers={"reloj": RELOJ},
        allowed_tools=["mcp__reloj__hoy"],
        setting_sources=[],
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=4,
        max_budget_usd=0.10,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    i = 0
    async for m in query(prompt=PREGUNTA, options=opciones):
        i += 1
        linea(m, i)   # no salgas con break: deja que el stream termine solo

    # num_turns cuenta vueltas del loop (evaluar + ejecutar tools), no turnos
    # de conversación. Una sola pregunta tuya puede dar num_turns = 7.


asyncio.run(main())
