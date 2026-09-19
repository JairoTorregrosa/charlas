"""El mismo agente del vuelo, con custom tools: el loop corre en Anthropic y las tools corren AQUÍ.

Es el puente entre los dos mundos del taller. El agente pide `hoy`, `gmail_buscar`
o `gmail_leer`; la sesión se pausa (`requires_action`); este script ejecuta la tool
y devuelve el resultado con `user.custom_tool_result`; la sesión sigue.

Todo evento queda guardado en salidas/<sesión>/eventos.jsonl, crudo y en orden.

    uv run python agente_custom_tools.py
    uv run python agente_custom_tools.py "¿Dónde me quedo en Medellín?"
"""

import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
cliente = Anthropic()
AQUI = Path(__file__).parent.resolve()
PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools; no adivines fechas ni reservas."""

CORREOS = {
    "c1": {"de": "Avianca", "asunto": "¡Vuela a Cartagena desde $189.900!", "fecha": "2026-09-15",
           "cuerpo": "Promoción válida hasta agotar existencias. Compra en avianca.com."},
    "c2": {"de": "Wingo", "asunto": "Tu vuelo BOG → CTG", "fecha": "2026-09-13",
           "cuerpo": "Vuelo BOG → CTG el domingo 13 de septiembre de 2026 a las 10:40. Reserva WX7Q2."},
    "c3": {"de": "LATAM", "asunto": "Confirmación de reserva", "fecha": "2026-09-16",
           "cuerpo": "Tu vuelo BOG → MDE sale el jueves 24 de septiembre de 2026 a las 06:15. Reserva ABC123."},
    "c4": {"de": "Booking.com", "asunto": "Tu reserva en Medellín", "fecha": "2026-09-17",
           "cuerpo": "Hotel en El Poblado, del 24 al 26 de septiembre de 2026. Reserva BK-88412."},
}

TOOLS = [
    {"type": "custom", "name": "hoy",
     "description": "La fecha de hoy. Pídela siempre antes de razonar sobre fechas.",
     "input_schema": {"type": "object", "properties": {}}},
    {"type": "custom", "name": "gmail_buscar",
     "description": "Busca correos recibidos desde una fecha (AAAA-MM-DD). Devuelve id, remitente, asunto y fecha.",
     "input_schema": {"type": "object", "properties": {"desde": {"type": "string"}}, "required": ["desde"]}},
    {"type": "custom", "name": "gmail_leer",
     "description": "Devuelve el correo completo con ese id.",
     "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
]


def ejecutar(nombre, entrada):
    if nombre == "hoy":
        return "sábado 19 de septiembre de 2026"
    if nombre == "gmail_buscar":
        return "\n".join(f"{i} · {c['de']} · {c['asunto']} · {c['fecha']}"
                         for i, c in CORREOS.items() if c["fecha"] >= entrada["desde"]) or "Sin correos."
    if nombre == "gmail_leer":
        c = CORREOS.get(entrada["id"])
        return f"De: {c['de']}\nAsunto: {c['asunto']}\nFecha: {c['fecha']}\n\n{c['cuerpo']}" if c else "No existe ese correo."
    return f"Tool desconocida: {nombre}"


pedido = sys.argv[1] if len(sys.argv) > 1 else PREGUNTA

agente = cliente.beta.agents.create(name="Asistente de viaje · custom tools", model="claude-sonnet-5",
                                    system=SYSTEM_PROMPT, tools=TOOLS)
sesion = cliente.beta.sessions.create(
    agent=agente.id, environment_id=os.environ["ENVIRONMENT_ID"], title="Taller Bogotá · custom tools",
    budget={"type": "limit", "max_list_cost": {"amount": "50", "currency": "USD"}},   # 50 centavos
)
carpeta = AQUI / "salidas" / sesion.id
carpeta.mkdir(parents=True, exist_ok=True)
print(f"agente {agente.id}\nsesión {sesion.id}\n\nTÚ              {pedido}")

pendientes = {}
with (carpeta / "eventos.jsonl").open("w") as bitacora, cliente.beta.sessions.events.stream(sesion.id) as stream:
    cliente.beta.sessions.events.send(
        sesion.id, events=[{"type": "user.message", "content": [{"type": "text", "text": pedido}]}])
    for evento in stream:
        bitacora.write(evento.model_dump_json() + "\n")
        bitacora.flush()
        match evento.type:
            case "agent.custom_tool_use":
                pendientes[evento.id] = evento
                print(f"EL AGENTE PIDE  {evento.name}({json.dumps(evento.input, ensure_ascii=False)})")
            case "agent.message":
                for b in evento.content:
                    if b.type == "text":
                        print(f"EL AGENTE DICE  {b.text}")
            case "session.error":
                print(f"ERROR           {evento}")
            case "session.status_idle":
                if evento.stop_reason and evento.stop_reason.type == "requires_action":
                    for event_id in evento.stop_reason.event_ids:
                        t = pendientes.pop(event_id, None)
                        if t is None:          # ya respondida: el idle puede repetirse mientras llegan resultados
                            continue
                        resultado = ejecutar(t.name, t.input)
                        print(f"MI CÓDIGO       {resultado.splitlines()[0][:90]}")
                        cliente.beta.sessions.events.send(sesion.id, events=[{
                            "type": "user.custom_tool_result", "custom_tool_use_id": event_id,
                            "content": [{"type": "text", "text": resultado}]}])
                else:
                    break

uso = cliente.beta.sessions.retrieve(sesion.id).usage
print(f"\nEVENTOS         {carpeta}/eventos.jsonl\nUSO             {uso}")
