"""agent_vivienda.py — Buscador de vivienda.

Le das lo que buscas (zona, presupuesto, cuartos) y busca avisos reales en internet,
los evalúa con su método y deja una tabla en `candidatos.md`.

Terminal:   uv run agent_vivienda.py "Apartamento en Chapinero, máximo 2.500.000 al mes, 2 habitaciones"
Notebook:   from agent_vivienda import vivienda
            r = await vivienda("Chapinero, máximo 2.500.000, 2 habitaciones")
            await vivienda("Ahora lo mismo en Teusaquillo", resume=r.session_id)   # sigue la conversación

Su casa es `workspace_vivienda/`: ahí escribe (`candidatos.md`) y de ahí carga su skill
(`.claude/skills`), su ayudante (`.claude/agents`) y sus buscadores (`.mcp.json`: Exa y
Firecrawl, sin llave), así que funciona con cualquier proveedor de `proveedores.py`.
Necesita internet.
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
    TextBlock,
    ToolUseBlock,
    query,
)

from proveedores import proveedor

# Con qué cerebro corre: "claude" (suscripción de Claude Code) u otro de docs/proveedores.md.
MODELO, ENV = proveedor(os.environ.get("TALLER_PROVEEDOR", "claude"))

WORKSPACE = (Path(__file__).parent / "workspace_vivienda").resolve()

# --- Quién es ------------------------------------------------------------------
SYSTEM_PROMPT = """# Quién eres

Buscas apartamentos en arriendo en Bogotá para una persona. Respondes corto y con datos.
Español colombiano. Cifras en pesos, con puntos de miles.

# Dónde trabajas

- Tu carpeta es `{cwd}`. El único archivo que escribes es `candidatos.md`.

# Reglas

- Busca en portales colombianos (Metrocuadrado, Fincaraíz, Ciencuadras, Habi) con `web_search_exa` o `firecrawl_search`.
- Lee cada aviso con `firecrawl_scrape` o `web_fetch_exa`. Si uno falla, prueba el otro.
- Usa el skill `evaluar-apto-bogota` para qué mirar y cómo presentar la tabla.
- Entre 3 y 5 candidatos. Cada uno con su link real.
- Si un dato no está en el aviso, escribe "no dice". Nunca inventes un apartamento ni un precio.
- Tienes 30 vueltas y 80 centavos de dólar. Si se acaban, entrega lo que tengas.
- Si un portal no se deja leer, prueba otro y sigue."""


# --- El portero: solo puede escribir candidatos.md --------------------------------
async def solo_candidatos(input_data, tool_use_id, context):
    archivo = Path(input_data["tool_input"].get("file_path", "")).name
    if archivo == "candidatos.md":
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Solo puedes escribir candidatos.md. {archivo} se queda como está.",
        }
    }


# --- El agente -------------------------------------------------------------------
async def vivienda(pedido: str, *, resume: str | None = None) -> ResultMessage | None:
    """Busca según el pedido. Con `resume` sigue la conversación anterior. Devuelve el recibo."""
    opciones = ClaudeAgentOptions(
        model=MODELO,
        system_prompt=SYSTEM_PROMPT.format(cwd=WORKSPACE),
        cwd=str(WORKSPACE),                       # su casa
        setting_sources=["project"],              # carga .claude/skills, .claude/agents y .mcp.json de su casa
        allowed_tools=["mcp__exa__*", "mcp__firecrawl__*", "WebFetch", "Read", "Write", "Edit", "Skill", "Agent"],
        disallowed_tools=["WebSearch"],           # la búsqueda del servidor de Anthropic; solo existe con Claude
        hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[solo_candidatos])]},
        resume=resume,                            # id de una conversación anterior, para seguirla
        max_turns=30,
        max_budget_usd=0.80,                      # buscar en internet es caro: tope duro
        env=ENV,
        stderr=lambda _: None,
    )

    recibo = None
    USER_PROMPT = pedido
    async for m in query(prompt=USER_PROMPT, options=opciones):
        if isinstance(m, AssistantMessage):
            quien = "  [revisor]" if m.parent_tool_use_id else "[buscador]"
            for b in m.content:
                if isinstance(b, TextBlock) and b.text.strip():
                    print(f"{quien} {b.text.strip()}")
                elif isinstance(b, ToolUseBlock):
                    detalle = b.input.get("query") or b.input.get("url") or b.input.get("file_path") or b.input.get("skill") or b.input.get("description") or ""
                    print(f"{quien} usa {b.name}: {str(detalle)[:90]}")
        elif isinstance(m, ResultMessage):
            recibo = m
            print(f"\n[fin] {m.num_turns} vueltas · USD {m.total_cost_usd:.3f} · {m.duration_ms / 1000:.0f}s · sesión {m.session_id}")
    return recibo


if __name__ == "__main__":
    pedido = sys.argv[1] if len(sys.argv) > 1 else "Apartamento en arriendo en Chapinero, máximo 2.500.000 al mes, 2 habitaciones, que acepten perro."
    asyncio.run(vivienda(pedido))
