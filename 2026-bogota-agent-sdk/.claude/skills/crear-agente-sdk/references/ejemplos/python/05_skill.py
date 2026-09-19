"""05 · un skill — el procedimiento, en markdown, escrito por alguien que no programa.

El skill vive en disco, no en el código:

    workspace/.claude/skills/buscar-vuelo/SKILL.md

Dos opciones lo cargan:
    cwd="…/workspace"           la carpeta donde vive el agente
    setting_sources=["project"] léele el .claude/ a esa carpeta

Lo barato: el LLM solo tiene en contexto el nombre y la descripción del skill.
El cuerpo (los 5 pasos) se carga cuando decide usarlo. Vas a ver la tool `Skill`
en el stream justo antes de que cambie de método.

Compara el orden de tools con el de 04: allí improvisaba, aquí sigue el procedimiento.

    uv run python 05_skill.py
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

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
        cwd=str(AQUI / "workspace"),
        setting_sources=["project"],       # lee workspace/.claude/
        skills=["buscar-vuelo"],           # y de ahí, solo este
        tools=["Skill"],                   # si pasas `tools`, incluye "Skill" a mano
        mcp_servers={
            "reloj": RELOJ,
            "gmail": {"command": sys.executable, "args": [str(AQUI / "gmail_mcp.py")]},
        },
        allowed_tools=["Skill", "mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        max_turns=12,
        max_budget_usd=0.20,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    async for m in query(prompt=PREGUNTA, options=opciones):
        linea(m)


asyncio.run(main())
