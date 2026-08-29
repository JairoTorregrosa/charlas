"""agent_parcero.py — El Parcero Crítico.

Le das la URL de un repo público de GitHub. Lo clona, lo lee y escribe un roast:
humor contra el código, nunca contra la persona.

Terminal:   uv run agent_parcero.py https://github.com/JairoTorregrosa/crea-tu-web
Notebook:   from agent_parcero import parcero; await parcero("https://github.com/...")

Su casa es `workspace_parcero/`: ahí clona (`repos/`), ahí escribe (`roast.md`),
y de ahí carga su skill (`.claude/skills`) y su ayudante (`.claude/agents`).
No tiene tools propias: solo las que trae el SDK, el skill y el ayudante.
"""

import asyncio
import os
import shlex
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    ToolUseBlock,
    query,
)

from proveedores import proveedor

# Con qué cerebro corre: "claude" (suscripción de Claude Code) u otro de docs/proveedores.md.
MODELO, ENV = proveedor(os.environ.get("TALLER_PROVEEDOR", "claude"))
from claude_agent_sdk.types import StreamEvent

WORKSPACE = (Path(__file__).parent / "workspace_parcero").resolve()

# --- Quién es ------------------------------------------------------------------
SYSTEM_PROMPT = """# Quién eres

Eres El Parcero Crítico: revisas código ajeno con humor seco y criterio técnico.
Hablas en español colombiano, de tú, con frases cortas.
Te burlas del código, nunca de quien lo escribió. Si algo está bien hecho, lo dices sin rodeos.

# Dónde trabajas

- Tu carpeta es `{cwd}`. Los repos se clonan en `repos/` y se leen; no se modifican.
- El único archivo que escribes es `roast.md`.

# Reglas

- Cita líneas reales, con número. Si no la leíste, no la cites.
- Lee completos máximo 3 archivos. Para el resto usa Grep.
- Usa el skill `roast-de-codigo` para el criterio y el formato.
- Tienes 30 vueltas y 60 centavos de dólar. Si se acaban, escribe lo que tengas.
- Si el repo no existe o no se puede clonar, dilo y para."""


# --- Los porteros: código tuyo que corre ANTES de cada herramienta ---------------
# Un hook recibe lo que el modelo quiere hacer y devuelve {} (sigue) o un "deny" con motivo.
# El motivo se lo lee el modelo como si fuera el resultado de la herramienta: no se cae, se adapta.

PERMITIDOS = {"ls", "wc", "find", "head", "cat", "du"}


async def solo_clonar(input_data, tool_use_id, context):
    comando = input_data["tool_input"].get("command", "")
    palabras = shlex.split(comando) if comando else []
    es_clone = palabras[:2] == ["git", "clone"]
    if es_clone or (palabras and palabras[0] in PERMITIDOS):
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Bash aquí solo sirve para `git clone`, `ls`, `wc`, `find`, `head`, `cat`. Para leer usa Read; para buscar, Grep.",
        }
    }


async def solo_roast(input_data, tool_use_id, context):
    archivo = Path(input_data["tool_input"].get("file_path", "")).name
    if archivo == "roast.md":
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Solo puedes escribir roast.md. {archivo} se queda como está.",
        }
    }


# --- El agente -------------------------------------------------------------------
async def parcero(repo_url: str) -> ResultMessage | None:
    """Roastea el repo. Imprime el texto en vivo y devuelve el recibo."""
    (WORKSPACE / "repos").mkdir(exist_ok=True)

    opciones = ClaudeAgentOptions(
        model=MODELO,
        system_prompt=SYSTEM_PROMPT.format(cwd=WORKSPACE),
        cwd=str(WORKSPACE),                       # su casa
        setting_sources=["project"],              # carga .claude/skills y .claude/agents de su casa
        allowed_tools=["Bash", "Read", "Glob", "Grep", "Write", "Edit", "Skill", "Agent"],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[solo_clonar]),
                HookMatcher(matcher="Write|Edit", hooks=[solo_roast]),
            ]
        },
        include_partial_messages=True,            # para ver el texto llegar letra por letra
        max_turns=30,
        max_budget_usd=0.60,
        env=ENV,
        stderr=lambda _: None,
    )

    recibo = None
    USER_PROMPT = f"Roastea {repo_url}."
    async for m in query(prompt=USER_PROMPT, options=opciones):
        if isinstance(m, StreamEvent) and m.parent_tool_use_id is None:
            # Texto del Parcero llegando letra por letra (los ayudantes no se imprimen).
            delta = m.event.get("delta", {})
            if delta.get("type") == "text_delta":
                print(delta["text"], end="", flush=True)
        elif isinstance(m, AssistantMessage):
            quien = "  [inspector]" if m.parent_tool_use_id else "[parcero]"
            for b in m.content:
                if isinstance(b, ToolUseBlock):
                    detalle = b.input.get("command") or b.input.get("file_path") or b.input.get("pattern") or b.input.get("skill") or b.input.get("description") or ""
                    print(f"\n{quien} usa {b.name}: {str(detalle)[:90]}")
        elif isinstance(m, ResultMessage):
            recibo = m
            print(f"\n\n[fin] {m.num_turns} vueltas · USD {m.total_cost_usd:.3f} · {m.duration_ms / 1000:.0f}s")
    return recibo


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/JairoTorregrosa/crea-tu-web"
    asyncio.run(parcero(url))
