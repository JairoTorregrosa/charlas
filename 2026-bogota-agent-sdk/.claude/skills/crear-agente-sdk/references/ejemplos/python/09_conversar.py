"""09 · conversar — el contraste.

Los ocho archivos anteriores corren y terminan. Ninguno es un chat, y aun así
todos son agentes. Conversar es una función más, y hay que pedirla:

  ClaudeSDKClient   abre la conexión, la mantiene y te deja mandar varios
                    mensajes en la misma sesión (y solo él permite interrupt())
  resume=id         la otra vía: query() con el session_id de una corrida
                    anterior retoma esa conversación

Aquí van dos turnos. El segundo ("¿y el anterior?") solo tiene sentido si el
agente recuerda el primero: esa es la prueba.

    uv run python 09_conversar.py
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, create_sdk_mcp_server, tool

from mostrar import linea

AQUI = Path(__file__).parent.resolve()

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
        max_turns=12,
        max_budget_usd=0.30,
        stderr=lambda _: None,
    )

    async with ClaudeSDKClient(options=opciones) as agente:
        for turno in ["Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.",
                      "¿Y el vuelo anterior a ese? Responde solo con la fecha."]:
            print(f"\nPREGUNTA  {turno}\n")
            await agente.query(turno)
            async for m in agente.receive_response():   # termina en el ResultMessage del turno
                linea(m)


asyncio.run(main())
