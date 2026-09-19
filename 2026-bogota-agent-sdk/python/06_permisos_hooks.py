"""06 · permisos y hooks — quién decide si una tool corre.

Cuatro palancas, de la más tosca a la más fina:

  disallowed_tools   con el nombre pelado, la tool desaparece del contexto.
                     El set base trae Skill, Read, Bash, Write y Edit; mira el
                     ARRANQUE: de esas cinco solo sobreviven Skill y Read.
  allowed_tools      lo que se aprueba sin preguntar. No restringe: solo aprueba.
  permission_mode    "dontAsk" niega lo que no esté aprobado, en vez de quedarse
                     esperando a un humano que en un script no existe.
  hook PreToolUse    tu código, que ve los ARGUMENTOS. Las listas filtran por
                     nombre de tool; solo el hook sabe qué correo está abriendo.

El motivo del `deny` vuelve al LLM como resultado de la tool: no se cae, cambia
de ruta. Escríbelo como instrucción, no como log.

Ojo con lo verificado: un hook que devuelve "allow" NO salta las reglas deny.

    uv run python 06_permisos_hooks.py
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions, HookMatcher, create_sdk_mcp_server, query, tool,
)

from mostrar import linea

AQUI = Path(__file__).parent.resolve()
PRIVADOS = {"c2", "c4"}   # cambia los ids y vuelve a correr: el agente cambia de ruta
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


@tool("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.", {})
async def hoy(args):
    return {"content": [{"type": "text", "text": "sábado 19 de septiembre de 2026"}]}


RELOJ = create_sdk_mcp_server(name="reloj", version="1.0.0", tools=[hoy])


async def guardrail(entrada, tool_use_id, contexto):
    correo = entrada["tool_input"].get("id")
    if correo not in PRIVADOS:
        return {}                                  # sin opinión: que siga el proceso normal
    print(f"      🚫 el hook bloquea leer({correo})")
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"El correo {correo} está marcado como privado y no se puede abrir. "
            "Trabaja con el asunto y la fecha que ya viste en la lista."),
    }}


async def main():
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        cwd=str(AQUI / "workspace"),
        setting_sources=["project"],
        skills=["buscar-vuelo"],
        tools=["Skill", "Read", "Bash", "Write", "Edit"],   # el set base de este agente
        mcp_servers={
            "reloj": RELOJ,
            "gmail": {"command": sys.executable, "args": [str(AQUI / "gmail_mcp.py")]},
        },
        allowed_tools=["Skill", "mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
        disallowed_tools=["Bash", "Write", "Edit"],
        permission_mode="dontAsk",
        hooks={"PreToolUse": [HookMatcher(matcher="mcp__gmail__leer", hooks=[guardrail])]},
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
