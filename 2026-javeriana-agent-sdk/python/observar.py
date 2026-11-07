"""observar.py — la bitácora del agente. Guarda TODO lo que emite el SDK y lo vuelve legible.

Cada corrida deja una carpeta salidas/<fecha-hora>/ con dos archivos:

  eventos.jsonl    cada mensaje del SDK, crudo y completo, uno por línea. Se escribe
                   en el momento: si el agente se cae, lo que alcanzó a pasar queda.
  transcript.md    lo mismo, para leer: qué tenía el agente antes de empezar y,
                   llamada por llamada al LLM, qué papeles nuevos había en el
                   contexto y qué respondió.

    bitacora = Bitacora(AQUI / "salidas", pedido=pedido, system_prompt=SYSTEM_PROMPT)
    async for m in query(...):
        bitacora.anotar(m)
    bitacora.cerrar()
"""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ResultMessage, SystemMessage, TextBlock, ThinkingBlock,
    ToolResultBlock, ToolUseBlock, UserMessage,
)


def _texto(contenido):
    if isinstance(contenido, str) or contenido is None:
        return contenido or ""
    return "\n".join(c.get("text", json.dumps(c, ensure_ascii=False)) for c in contenido)


def _bloque(s):
    return "```\n" + s.strip() + "\n```\n"


class Bitacora:
    def __init__(self, salidas: Path, pedido: str, system_prompt: str = ""):
        self.carpeta = Path(salidas) / datetime.now().strftime("%Y%m%d-%H%M%S")
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self._eventos = (self.carpeta / "eventos.jsonl").open("w")
        self._md = [f"# Transcript · {self.carpeta.name}\n",
                    "## Antes de empezar\n", "**System prompt**\n", _bloque(system_prompt or "(el del SDK)")]
        self._pendiente = [("user message", pedido, None)]   # papeles nuevos desde la última llamada
        self._llamada = None
        self._n = 0

    def anotar(self, m):
        crudo = asdict(m) if is_dataclass(m) else {"repr": repr(m)}
        self._eventos.write(json.dumps({"n": self._n, "hora": datetime.now().isoformat(),
                                        "tipo": type(m).__name__, **crudo},
                                       ensure_ascii=False, default=str) + "\n")
        self._eventos.flush()
        self._n += 1

        if isinstance(m, SystemMessage) and m.subtype == "init":
            d = m.data
            self._md += [f"**Modelo** `{d.get('model')}` · **permisos** `{d.get('permissionMode')}`\n",
                         f"**Tools** {', '.join(f'`{t}`' for t in d.get('tools', [])) or '(ninguna)'}\n",
                         f"**MCP** {', '.join(f'`{s.get('name')}` ({s.get('status')})' for s in d.get('mcp_servers', [])) or '(ninguno)'}\n",
                         f"**Skills** {', '.join(f'`{s}`' for s in d.get('skills', [])) or '(ninguna)'}\n"]
        elif isinstance(m, UserMessage):
            quien = "subagente · " if m.parent_tool_use_id else ""
            bloques = m.content if isinstance(m.content, list) else [m.content]
            for b in bloques:
                if isinstance(b, ToolResultBlock):
                    etiqueta = f"{quien}tool result{' · ERROR' if b.is_error else ''}"
                    self._pendiente.append((etiqueta, _texto(b.content), b.tool_use_id))
                elif isinstance(b, TextBlock):
                    self._pendiente.append((f"{quien}user message", b.text, None))
                elif isinstance(b, str):
                    self._pendiente.append((f"{quien}user message", b, None))
        elif isinstance(m, AssistantMessage):
            if m.message_id != self._llamada:            # una respuesta del LLM puede llegar en varios mensajes
                self._llamada = m.message_id
                self._abrir_llamada(m)
            for b in m.content:
                if isinstance(b, ToolUseBlock):
                    self._md += [f"- **tool call** `{b.name}` · id `{b.id[-6:]}`\n",
                                 _bloque(json.dumps(b.input, ensure_ascii=False, indent=2))]
                elif isinstance(b, TextBlock) and b.text.strip():
                    self._md += ["- **assistant message**\n", _bloque(b.text)]
                elif isinstance(b, ThinkingBlock) and b.thinking.strip():
                    self._md += ["- *pensó*\n", _bloque(b.thinking)]
        elif isinstance(m, ResultMessage):
            self._md += ["## Recibo\n",
                         f"`{m.subtype}` · {m.num_turns} turns (num_turns del SDK) · "
                         f"{self._llamadas} llamadas al LLM · {m.duration_ms / 1000:.1f} s · "
                         f"USD {m.total_cost_usd or 0:.4f}\n"]
            if m.permission_denials:
                self._md.append(f"**Negados por permisos o hooks:** {len(m.permission_denials)}\n")

    _llamadas = 0

    def _abrir_llamada(self, m):
        self._llamadas += 1
        u = m.usage or {}
        leidos = sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        quien = " (subagente)" if m.parent_tool_use_id else ""
        self._md += [f"## Llamada {self._llamadas} al LLM{quien}\n",
                     f"El LLM leyó el contexto completo: **{leidos:,} tokens**. Papeles nuevos desde la llamada anterior:\n"]
        for etiqueta, texto, ref in self._pendiente:
            self._md += [f"- **{etiqueta}**" + (f" · id `{ref[-6:]}`" if ref else "") + "\n", _bloque(texto)]
        if not self._pendiente:
            self._md.append("- (ninguno)\n")
        self._pendiente = []
        self._md.append("**Respondió:**\n")

    def cerrar(self):
        self._eventos.close()
        (self.carpeta / "transcript.md").write_text("\n".join(self._md))
        print(f"\nBITÁCORA  {self.carpeta}/transcript.md  ·  eventos.jsonl ({self._n} eventos)")
