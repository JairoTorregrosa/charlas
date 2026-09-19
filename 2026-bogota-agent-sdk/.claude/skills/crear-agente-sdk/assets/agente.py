"""TODO nombre — TODO qué hace, en una línea.

    uv run python agente.py
    uv run python agente.py "otra pregunta"
"""

import entorno  # carga ANTHROPIC_API_KEY de .env

import asyncio
import json
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, HookMatcher, ResultMessage, SystemMessage,
    TextBlock, ToolUseBlock, create_sdk_mcp_server, query, tool,
)

from observar import Bitacora

AQUI = Path(__file__).parent.resolve()
PEDIDO = "TODO el pedido por defecto"

# SYSTEM PROMPT: quién es y qué no debe adivinar.
SYSTEM_PROMPT = """TODO Eres ... Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines TODO."""


# TOOL PROPIA: datos o acciones de tu código. Bórrala si no la necesitas.
# El esquema simple es {"campo": tipo}. Para listas u objetos pasa un JSON Schema completo:
#   {"type": "object", "properties": {"filas": {"type": "array", "items": {"type": "object",
#     "properties": {"categoria": {"type": "string"}, "monto": {"type": "number"}}}}}, "required": ["filas"]}
# Las sumas y los conteos van aquí, en código: el LLM clasifica, tu función calcula.
@tool("TODO_nombre", "TODO qué devuelve y cuándo pedirla.", {"TODO_arg": str})
async def mi_tool(args):
    return {"content": [{"type": "text", "text": f"TODO resultado para {args['TODO_arg']}"}]}


PROPIAS = create_sdk_mcp_server(name="propias", version="1.0.0", tools=[mi_tool])


# HOOK: ve los argumentos de cada tool call antes de que corra.
async def guardrail(entrada, tool_use_id, contexto):
    prohibido = False  # TODO la condición sobre entrada["tool_input"]
    if not prohibido:
        return {}
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "TODO qué debe hacer el agente en su lugar.",
    }}


def mostrar(m):
    if isinstance(m, SystemMessage) and m.subtype == "init":
        print(f"ARRANQUE  tools={m.data.get('tools')} mcp={m.data.get('mcp_servers')}\n")
    elif isinstance(m, AssistantMessage):
        for b in m.content:
            if isinstance(b, ToolUseBlock):
                print(f"-> {b.name} {json.dumps(b.input, ensure_ascii=False)}")
            elif isinstance(b, TextBlock) and b.text.strip():
                print(f"\nAGENTE    {b.text.strip()}")
    elif isinstance(m, ResultMessage):
        print(f"\n[{m.subtype}] {m.num_turns} turns · {m.duration_ms / 1000:.1f} s · "
              f"USD {m.total_cost_usd or 0:.4f}")


async def main(pedido=PEDIDO):
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        # WORKSPACE Y TOOLS
        cwd=str(AQUI / "workspace"),
        setting_sources=["project"],            # [] si no hay skills
        skills=["TODO-nombre-de-la-skill"],
        tools=["Skill"],                        # + las nativas que el objetivo exija
        mcp_servers={"propias": PROPIAS},
        # GUARDRAILS
        allowed_tools=["Skill", "mcp__propias__TODO_nombre"],
        disallowed_tools=[],
        permission_mode="dontAsk",
        hooks={"PreToolUse": [HookMatcher(matcher="mcp__propias__TODO_nombre", hooks=[guardrail])]},
        max_turns=12,
        max_budget_usd=0.25,
        # AISLAMIENTO
        strict_mcp_config=True,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        stderr=lambda _: None,
    )

    print(f"PEDIDO    {pedido}\n")
    bitacora = Bitacora(AQUI / "salidas", pedido=pedido, system_prompt=SYSTEM_PROMPT)
    try:
        async for m in query(prompt=pedido, options=opciones):
            bitacora.anotar(m)                  # cada evento queda guardado, pase lo que pase
            mostrar(m)
    except Exception as e:                      # tocar un tope lanza excepción: es a propósito
        print(f"\n[corte] {e}")
    finally:
        bitacora.cerrar()

asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else PEDIDO))
