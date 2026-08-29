"""agent_monitor.py — El Monitor.

Le das un paper (título o id de arXiv) y te lo descompone en cinco preguntas, con
analogías, como el compañero que sí leyó y te lo explica la noche antes del parcial.
Deja todo en `explicacion.md`.

Terminal:   uv run agent_monitor.py "Attention is all you need"
Notebook:   from agent_monitor import monitor; await monitor("arXiv 1706.03762")

Su casa es `workspace_monitor/`: ahí escribe (`explicacion.md`) y de ahí carga su skill
(`.claude/skills`) y su ayudante (`.claude/agents`). Lee los papers con un servidor MCP
externo, alphaXiv, que se registra una sola vez en tu Claude Code:

    claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1 --scope user
    claude   →   /mcp   →   alphaxiv   →   Authenticate      (abre el navegador una vez)

No tiene tools propias: solo las que trae el SDK, el skill, el ayudante y el MCP.
"""

import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    SystemMessage,
    ToolUseBlock,
    query,
)

from proveedores import proveedor

# Con qué cerebro corre: "claude" (suscripción de Claude Code) u otro de docs/proveedores.md.
MODELO, ENV = proveedor(os.environ.get("TALLER_PROVEEDOR", "claude"))
from claude_agent_sdk.types import StreamEvent

WORKSPACE = (Path(__file__).parent / "workspace_monitor").resolve()

# --- Quién es ------------------------------------------------------------------
SYSTEM_PROMPT = """# Quién eres

Eres El Monitor: el compañero de la materia que sí leyó el paper y te lo explica la noche antes del parcial.
Español colombiano, de tú, frases cortas. Analogías de la vida diaria antes que fórmulas.
Si algo es difícil, lo dices; no lo disfrazas.

# Dónde trabajas

- Tu carpeta es `{cwd}`. El único archivo que escribes es `explicacion.md`.

# Reglas

- Busca y lee el paper con las tools de alphaXiv. No expliques de memoria.
- Usa el skill `descomponer-paper` para las preguntas y el formato.
- Si el paper es largo, reparte secciones entre lectores (uno por sección).
- Cita sección o tabla cuando des un número.
- Tienes 25 vueltas y 60 centavos de dólar. Si se acaban, entrega lo que tengas."""


# --- El portero: solo puede escribir explicacion.md ------------------------------
async def solo_explicacion(input_data, tool_use_id, context):
    archivo = Path(input_data["tool_input"].get("file_path", "")).name
    if archivo == "explicacion.md":
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Solo puedes escribir explicacion.md. {archivo} se queda como está.",
        }
    }


# --- El agente -------------------------------------------------------------------
async def monitor(paper: str) -> ResultMessage | None:
    """Explica el paper. Imprime el texto en vivo y devuelve el recibo."""
    opciones = ClaudeAgentOptions(
        model=MODELO,
        system_prompt=SYSTEM_PROMPT.format(cwd=WORKSPACE),
        cwd=str(WORKSPACE),                       # su casa
        setting_sources=["user", "project"],      # "user": el MCP alphaxiv que registraste; "project": skill y lector
        allowed_tools=[
            "Read", "Write", "Edit", "Skill", "Agent",
            "mcp__alphaxiv__*",                   # el que registra el estudiante con `claude mcp add`
            "mcp__claude_ai_alphaXiv__*",         # o el conector de claude.ai, si lo tienes
        ],
        hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[solo_explicacion])]},
        include_partial_messages=True,            # texto letra por letra
        max_turns=25,
        max_budget_usd=0.60,
        env=ENV,
        stderr=lambda _: None,
    )

    recibo = None
    USER_PROMPT = f"Explícame este paper: {paper}"
    async for m in query(prompt=USER_PROMPT, options=opciones):
        if isinstance(m, SystemMessage) and m.subtype == "init":
            mcp = [f"{s['name']}={s.get('status')}" for s in m.data.get("mcp_servers", []) if "alphaxiv" in s["name"].lower()]
            print(f"[init] alphaxiv: {', '.join(mcp) or 'no está'}")
        elif isinstance(m, StreamEvent) and m.parent_tool_use_id is None:
            delta = m.event.get("delta", {})
            if delta.get("type") == "text_delta":
                print(delta["text"], end="", flush=True)
        elif isinstance(m, AssistantMessage):
            quien = "  [lector]" if m.parent_tool_use_id else "[monitor]"
            for b in m.content:
                if isinstance(b, ToolUseBlock):
                    detalle = b.input.get("query") or b.input.get("paper_id") or b.input.get("file_path") or b.input.get("skill") or b.input.get("description") or ""
                    print(f"\n{quien} usa {b.name}: {str(detalle)[:90]}")
        elif isinstance(m, ResultMessage):
            recibo = m
            print(f"\n\n[fin] {m.num_turns} vueltas · USD {m.total_cost_usd:.3f} · {m.duration_ms / 1000:.0f}s")
    return recibo


if __name__ == "__main__":
    paper = sys.argv[1] if len(sys.argv) > 1 else "Attention is all you need (arXiv 1706.03762)"
    asyncio.run(monitor(paper))
