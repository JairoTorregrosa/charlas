"""El agente del ejercicio, completo, en Claude Managed Agents.

    «Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.»

Las mismas piezas que actuamos con los letreros:
  system prompt   el del taller
  skill           buscar-vuelo, subida al workspace con la Skills API
  tool            hoy            (custom tool: corre en tu máquina)
  "MCP" gmail     gmail_buscar · gmail_leer   (custom tools: corren en tu máquina)
  harness         el loop corre en Anthropic

Guarda todos los eventos en salidas/<sesión>/eventos.jsonl y un transcript.md.

    uv run python agente_vuelo.py
"""

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from anthropic.lib import files_from_dir
from dotenv import load_dotenv

from ideas import CORREOS, t

load_dotenv()
cliente = Anthropic()
AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."
SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""

TOOLS = [
    # la skill vive en el sandbox: el agente la abre con read
    {"type": "agent_toolset_20260401", "default_config": {"enabled": False},
     "configs": [{"name": n, "enabled": True} for n in ("read", "glob", "grep")]},
    t("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas."),
    t("gmail_buscar", "Busca correos recibidos desde una fecha. Devuelve id, remitente, asunto y fecha.", desde="AAAA-MM-DD"),
    t("gmail_leer", "Devuelve el correo completo con ese id.", id="id del correo"),
]


def ejecutar(n, a):
    if n == "hoy":
        return "sábado 19 de septiembre de 2026"
    if n == "gmail_buscar":
        return "\n".join(f"{k} · {v[0]} · {v[1]} · {v[2]}" for k, v in CORREOS.items() if v[2] >= a.get("desde", "")) or "Sin correos."
    if n == "gmail_leer":
        return "De: {}\nAsunto: {}\nFecha: {}\n\n{}".format(*CORREOS[a["id"]]) if a.get("id") in CORREOS else "No existe ese correo."


skill_id = os.environ.get("SKILL_ID")
if not skill_id:
    skill = cliente.beta.skills.create(files=files_from_dir(str(AQUI / "skills" / "buscar-vuelo")))
    skill_id = skill.id
    print(f"skill  {skill_id}   (agrega SKILL_ID={skill_id} a .env para reusarla)")

agente = cliente.beta.agents.create(name="Agente del vuelo · el del ejercicio", model="claude-sonnet-5", system=SYSTEM_PROMPT,
                                    tools=TOOLS, skills=[{"type": "custom", "skill_id": skill_id, "version": "latest"}])
sesion = cliente.beta.sessions.create(agent=agente.id, environment_id=os.environ["ENVIRONMENT_ID"], title="¿Cuándo es mi próximo vuelo?",
                                      budget={"type": "limit", "max_list_cost": {"amount": "60", "currency": "USD"}})
carpeta = AQUI / "salidas" / sesion.id
carpeta.mkdir(parents=True, exist_ok=True)
pedido = sys.argv[1] if len(sys.argv) > 1 else PREGUNTA
print(f"agente {agente.id}\nsesión {sesion.id}\n\nTÚ              {pedido}")
md = [f"# ¿Cuándo es mi próximo vuelo? · {sesion.id}\n", "**System prompt**\n", f"```\n{SYSTEM_PROMPT}\n```\n", f"## Turno 1\n\n**user.message**\n\n```\n{pedido}\n```\n"]

pendientes, llamadas = {}, 0
with (carpeta / "eventos.jsonl").open("w") as bitacora, cliente.beta.sessions.events.stream(sesion.id) as stream:
    cliente.beta.sessions.events.send(sesion.id, events=[{"type": "user.message", "content": [{"type": "text", "text": pedido}]}])
    for e in stream:
        bitacora.write(e.model_dump_json() + "\n")
        bitacora.flush()
        if e.type == "span.model_request_start":
            llamadas += 1
            md.append(f"### Llamada {llamadas} al LLM\n")
        elif e.type == "agent.tool_use":
            print(f"EL AGENTE PIDE  {e.name} {json.dumps(e.input, ensure_ascii=False)[:120]}   (corre en el sandbox)")
            md.append(f"- **agent.tool_use** `{e.name}` (sandbox)\n\n```\n{json.dumps(e.input, ensure_ascii=False)}\n```\n")
        elif e.type == "agent.custom_tool_use":
            pendientes[e.id] = e
            print(f"EL AGENTE PIDE  {e.name}({json.dumps(e.input, ensure_ascii=False)})")
            md.append(f"- **agent.custom_tool_use** `{e.name}`\n\n```\n{json.dumps(e.input, ensure_ascii=False)}\n```\n")
        elif e.type == "agent.message":
            texto = "".join(b.text for b in e.content if b.type == "text")
            print(f"EL AGENTE DICE  {texto}")
            md.append(f"- **agent.message**\n\n```\n{texto}\n```\n")
        elif e.type == "session.error":
            print(f"ERROR           {e.error}")
        elif e.type == "session.status_idle":
            if e.stop_reason and e.stop_reason.type == "requires_action":
                for event_id in e.stop_reason.event_ids:
                    p = pendientes.pop(event_id, None)
                    if p is None:
                        continue
                    r = ejecutar(p.name, p.input)
                    print(f"MI CÓDIGO       {r.splitlines()[0][:100]}")
                    md.append(f"- **user.custom_tool_result** (corre en tu máquina)\n\n```\n{r}\n```\n")
                    cliente.beta.sessions.events.send(sesion.id, events=[{"type": "user.custom_tool_result", "custom_tool_use_id": event_id,
                                                                          "content": [{"type": "text", "text": r}]}])
            else:
                break

u = cliente.beta.sessions.retrieve(sesion.id).usage
recibo = f"1 turno · {llamadas} llamadas al LLM · {u.active_seconds:.1f} s activos · {u.list_cost.amount} centavos de USD"
md.append(f"## Recibo\n\n{recibo}\n")
(carpeta / "transcript.md").write_text("\n".join(md))
print(f"\nRECIBO          {recibo}\nTRANSCRIPT      {carpeta}/transcript.md")
