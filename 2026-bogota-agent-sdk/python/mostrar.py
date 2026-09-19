"""mostrar.py — el impresor del taller.

No es un primitivo del SDK. Traduce cada mensaje del stream a una línea que se
lea desde la última fila de la sala. Todos los ejemplos lo importan para que la
salida se vea igual en las 110 laptops.
"""

import json

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def corto(x, n=100):
    """Una sola línea, recortada, para que nada se desborde en el proyector."""
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def linea(m, i=0):
    """Imprime un mensaje del stream con su etiqueta."""
    # parent_tool_use_id sale lleno solo en los mensajes de un subagente:
    # es el id de la llamada a la tool Agent que lo lanzó.
    padre = getattr(m, "parent_tool_use_id", None)
    hijo = f" [subagente …{padre[-6:]}]" if padre else ""
    n = f"{i:>2} " if i else "   "

    # Ruido de observabilidad que taparía la pantalla en una demo.
    if isinstance(m, SystemMessage) and m.subtype in ("task_progress", "thinking_tokens"):
        return

    if isinstance(m, SystemMessage) and m.subtype == "init":
        d = m.data
        print(f"{n}ARRANQUE      modelo={d.get('model')}")
        print(f"   ├ tools   {corto(d.get('tools'), 120)}")
        print(f"   ├ skills  {corto(d.get('skills'), 80)}")
        print(f"   ├ agents  {corto(d.get('agents'), 80)}")
        print(f"   └ mcp     {corto(d.get('mcp_servers'), 120)}")
    elif isinstance(m, SystemMessage):
        print(f"{n}SISTEMA       {m.subtype}")
    elif isinstance(m, AssistantMessage):
        for b in m.content:
            if isinstance(b, TextBlock):
                print(f"{n}EL LLM DICE{hijo}   {corto(b.text)}")
            elif isinstance(b, ToolUseBlock):
                print(f"{n}EL LLM PIDE{hijo}   {b.name}({corto(b.input, 70)})")
            elif isinstance(b, ThinkingBlock) and b.thinking.strip():
                print(f"{n}EL LLM PIENSA{hijo} {corto(b.thinking, 70)}")
    elif isinstance(m, UserMessage):
        contenido = [] if isinstance(m.content, str) else m.content
        for b in contenido:
            if isinstance(b, ToolResultBlock):
                err = " ✗" if b.is_error else ""
                print(f"{n}LA TOOL RESPONDE{err}{hijo} {corto(b.content)}")
    elif isinstance(m, ResultMessage):
        print(f"{n}RECIBO        {m.subtype} · USD {m.total_cost_usd:.4f} · "
              f"{m.duration_ms / 1000:.1f}s · num_turns={m.num_turns}")
        if m.result:
            print(f"   └ respuesta: {corto(m.result, 300)}")
    else:
        # El stream trae también eventos de observabilidad (límites de uso, avisos).
        print(f"{n}OBSERVABILIDAD {type(m).__name__}")
