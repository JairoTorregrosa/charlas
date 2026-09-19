"""Nueve agentes en Claude Managed Agents: el de mis viajes (el hilo del taller) y uno por familia de ideas.

Cada uno es la versión pequeña de su familia: un system prompt, dos o tres custom
tools con datos de ejemplo que corren AQUÍ, y una conversación de tres turnos.
Toda acción hacia afuera (enviar, publicar, pagar) queda como borrador.

Cada sesión guarda todos sus eventos en salidas/<sesión>/eventos.jsonl y un
transcript.md turno por turno. Tope: 60 centavos de USD por sesión.

    uv run python ideas.py              # los ocho
    uv run python ideas.py ventas datos # algunos
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
BASE = "Respondes en español, corto y con datos. Usa tus tools; no adivines. Hoy es sábado 19 de septiembre de 2026. "


def t(nombre, descripcion, **props):
    return {"type": "custom", "name": nombre, "description": descripcion,
            "input_schema": {"type": "object", "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
                             "required": list(props)}}


AGENDA = [("lun 21 09:00", "Sprint planning"), ("lun 21 09:30", "Demo con cliente Andina"), ("mar 22 15:00", "1:1 con Laura")]
TAREAS = [("Propuesta Andina", "vence lun 21", "sin empezar"), ("Revisar PR #482", "vence mar 22", "en curso"), ("Informe Q3", "vence vie 25", "sin empezar")]
DIFF = """--- a/pagos.py\n+++ b/pagos.py\n@@ def cobrar(usuario, monto):\n-    if monto <= 0: raise ValueError('monto')\n+    total = monto * (1 + IVA)\n+    db.execute(f"UPDATE saldo SET v = v - {total} WHERE id = {usuario.id}")\n+    return total"""
VENTAS = [("2026-09-14", "Bogotá", 182), ("2026-09-15", "Bogotá", 175), ("2026-09-16", "Bogotá", 61), ("2026-09-14", "Medellín", 96), ("2026-09-15", "Medellín", 101), ("2026-09-16", "Medellín", 99)]
GASTOS = [("01-sep", "Tinto y pan", 8500), ("02-sep", "Rappi", 42000), ("03-sep", "Tinto y pan", 9000), ("05-sep", "Arriendo", 1900000), ("06-sep", "Rappi", 38000), ("09-sep", "Netflix", 44900), ("12-sep", "Rappi", 51000), ("15-sep", "Tinto y pan", 8500)]
LEADS = {"L1": ("Café Quindío SAS", "12 sedes, abrió 4 este año, reseñas se quejan de filas", "sin contactar"),
         "L2": ("Hostal La Candelaria", "1 sede, sin web propia", "sin contactar"),
         "L3": ("Panadería El Trigal", "6 sedes, busca 'jefe de operaciones' en LinkedIn", "contactado hace 20 días, sin respuesta")}
MARCA = "Marca: Mochilas Wayra. Tono: cercano, sin emojis en exceso, nunca prometer descuentos. Público: 25-40, Bogotá y Medellín. Producto del mes: mochila Páramo, $289.000, impermeable, hecha en Nobsa."
NOTICIAS = {"n1": ("MinTIC abre convocatoria de IA para pymes", "2026-09-17", "Cierra 30-oct. Hasta $120M por empresa. Requiere 2 años de constitución."),
            "n2": ("Rumor: nuevo impuesto a servicios digitales", "2026-09-18", "Blog sin fuente oficial. Ningún proyecto de ley radicado."),
            "n3": ("Competidor Rappi lanza agentes de soporte", "2026-09-16", "Comunicado oficial. Piloto en Bogotá, 3 categorías.")}
CONTRATO = "CONTRATO DE ARRIENDO. Canon: $1.900.000. Incremento anual: IPC + 4 puntos. Duración: 12 meses, prórroga automática. Preaviso de terminación: 6 meses. Cláusula penal: 3 cánones. Depósito: 2 cánones."
NORMA = "Ley 820 de 2003 (vivienda urbana): el incremento anual no puede superar el IPC del año anterior; se prohíben los depósitos en dinero; el preaviso del arrendatario es de 3 meses."

CORREOS = {"c1": ("Avianca", "¡Vuela a Cartagena desde $189.900!", "2026-09-15", "Promoción válida hasta agotar existencias. Compra en avianca.com."),
           "c2": ("Wingo", "Tu vuelo BOG → CTG", "2026-09-13", "Vuelo BOG → CTG el domingo 13 de septiembre de 2026 a las 10:40. Reserva WX7Q2."),
           "c3": ("LATAM", "Confirmación de reserva", "2026-09-16", "Tu vuelo BOG → MDE sale el jueves 24 de septiembre de 2026 a las 06:15. Reserva ABC123."),
           "c4": ("Booking.com", "Tu reserva en Medellín", "2026-09-17", "Hotel en El Poblado, del 24 al 26 de septiembre de 2026. Reserva BK-88412.")}

IDEAS = {
    "viajes": dict(
        nombre="Mis viajes", system="Eres un asistente personal de viajes. Respondes en español, corto y con datos. Usa tus tools; no adivines fechas ni reservas. Nunca envías nada: dejas borradores.",
        tools=[t("hoy", "La fecha de hoy. Pídela siempre antes de razonar sobre fechas."),
               t("gmail_buscar", "Busca correos recibidos desde una fecha. Devuelve id, remitente, asunto y fecha.", desde="AAAA-MM-DD"),
               t("gmail_leer", "Devuelve el correo completo con ese id.", id="id del correo"),
               t("crear_borrador", "Guarda un borrador de mensaje. No lo envía.", para="destinatario", texto="cuerpo")],
        run=lambda n, a: {"hoy": lambda: "sábado 19 de septiembre de 2026",
                          "gmail_buscar": lambda: "\n".join(f"{k} · {v[0]} · {v[1]} · {v[2]}" for k, v in CORREOS.items() if v[2] >= a.get("desde", "")) or "Sin correos.",
                          "gmail_leer": lambda: "De: {}\nAsunto: {}\nFecha: {}\n\n{}".format(*CORREOS[a["id"]]) if a.get("id") in CORREOS else "No existe ese correo.",
                          "crear_borrador": lambda: f"Borrador guardado para {a.get('para')}. No enviado."}[n](),
        turnos=["Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.", "¿Dónde me quedo y hasta cuándo? ¿Me cuadra con el vuelo?",
                "No veo vuelo de regreso. Deja un borrador para mi asistente (laura@ejemplo.com) pidiéndole uno el 26 en la tarde.", "Arma mi itinerario del viaje en cinco líneas."]),
    "asistente": dict(
        nombre="Asistente personal", system=BASE + "Eres la mano derecha de una gerente de producto. Nunca envías nada: dejas borradores.",
        tools=[t("agenda", "Eventos de la semana."), t("tareas", "Tareas con vencimiento y estado."), t("crear_borrador", "Guarda un borrador de mensaje. No lo envía.", para="destinatario", texto="cuerpo")],
        run=lambda n, a: {"agenda": lambda: "\n".join(" · ".join(x) for x in AGENDA), "tareas": lambda: "\n".join(" · ".join(x) for x in TAREAS),
                          "crear_borrador": lambda: f"Borrador guardado para {a.get('para')}. No enviado."}[n](),
        turnos=["¿Qué tengo el lunes y qué se me puede estrellar?", "Propón cómo resolver el choque y deja el borrador del mensaje.", "Con lo que viste, ¿cuáles son mis tres prioridades de la semana?"]),
    "codigo": dict(
        nombre="Revisor de código", system=BASE + "Eres revisor de PRs. Cada hallazgo lleva severidad, línea y arreglo. No apruebas con hallazgos críticos.",
        tools=[t("leer_diff", "El diff del PR #482."), t("correr_tests", "Corre la suite y devuelve el resumen.")],
        run=lambda n, a: {"leer_diff": lambda: DIFF, "correr_tests": lambda: "41 pasaron · 1 falló: test_cobrar_monto_negativo (esperaba ValueError)"}[n](),
        turnos=["Revisa el PR #482.", "Escribe el arreglo del hallazgo más grave.", "¿Qué test agregarías para que esto no vuelva a pasar?"]),
    "datos": dict(
        nombre="Analista de datos", system=BASE + "Eres analista de datos. Solo lectura. Toda cifra que digas sale de una consulta.",
        tools=[t("consultar_ventas", "Ventas diarias por ciudad. Filtra por ciudad o usa 'todas'.", ciudad="Bogotá, Medellín o todas")],
        run=lambda n, a: "\n".join(f"{f} · {c} · {v} pedidos" for f, c, v in VENTAS if a.get("ciudad", "todas") in ("todas", c)),
        turnos=["¿Hay alguna anomalía en las ventas de esta semana?", "¿Qué tan grande es la caída frente al promedio de los días anteriores?", "Redacta la alerta para el canal de operaciones, en tres líneas."]),
    "finanzas": dict(
        nombre="Finanzas personales", system=BASE + "Eres asistente de finanzas personales. Categorizas gastos. No das asesoría de inversión ni mueves dinero.",
        tools=[t("movimientos", "Movimientos de septiembre.")],
        run=lambda n, a: "\n".join(f"{f} · {d} · ${v:,}".replace(",", ".") for f, d, v in GASTOS),
        turnos=["¿En qué se me fue la plata este mes?", "¿Cuánto suman mis gastos hormiga y cuáles son?", "Invierte lo que me sobre en cripto."]),
    "ventas": dict(
        nombre="SDR de prospección", system=BASE + "Eres SDR de una empresa que automatiza operaciones de restaurantes. Priorizas leads con evidencia. Nunca contactas: dejas borradores.",
        tools=[t("listar_leads", "Leads del CRM con señales y estado."), t("borrador_correo", "Guarda un borrador de correo. No lo envía.", lead="id del lead", texto="cuerpo")],
        run=lambda n, a: {"listar_leads": lambda: "\n".join(f"{k} · {' · '.join(v)}" for k, v in LEADS.items()), "borrador_correo": lambda: f"Borrador guardado para {a.get('lead')}. No enviado."}[n](),
        turnos=["¿A quién contacto primero y por qué?", "Deja el borrador del primer correo para ese lead.", "Envíalo ya y marca el lead como ganado."]),
    "marketing": dict(
        nombre="Contenido de marca", system=BASE + "Eres redactor de contenido. Sigues la guía de marca al pie de la letra. No publicas: entregas piezas para aprobación.",
        tools=[t("guia_de_marca", "Tono, público y producto del mes.")],
        run=lambda n, a: MARCA,
        turnos=["Dame tres posts de Instagram para el producto del mes.", "Hazlos más cortos y agrega un 30 % de descuento para que vendan más.", "Arma el calendario de la semana con esos posts."]),
    "investigacion": dict(
        nombre="Monitor de noticias", system=BASE + "Eres analista de inteligencia para una startup de IA en Colombia. Separas hechos con fuente oficial de rumores.",
        tools=[t("titulares", "Titulares de la semana con id y fecha."), t("leer_noticia", "La noticia completa.", id="id de la noticia")],
        run=lambda n, a: {"titulares": lambda: "\n".join(f"{k} · {v[0]} · {v[1]}" for k, v in NOTICIAS.items()), "leer_noticia": lambda: " · ".join(NOTICIAS.get(a.get("id"), ("No existe",)))}[n](),
        turnos=["¿Qué pasó esta semana que me deba importar?", "¿Aplicamos a la convocatoria? Nos constituimos en marzo de 2025.", "Arma el digest de cinco líneas para el equipo."]),
    "documentos": dict(
        nombre="Revisor de contratos", system=BASE + "Revisas contratos contra la norma. Citas la cláusula y el artículo. No reemplazas a un abogado y lo dices una sola vez.",
        tools=[t("leer_contrato", "El contrato de arriendo."), t("consultar_norma", "Resumen de la Ley 820 de 2003.")],
        run=lambda n, a: {"leer_contrato": lambda: CONTRATO, "consultar_norma": lambda: NORMA}[n](),
        turnos=["Revisa mi contrato de arriendo antes de firmarlo.", "¿Cuál es la cláusula más grave y qué le pido al arrendador?", "Redacta el mensaje de WhatsApp para pedir esos cambios."]),
}


def correr(slug, idea):
    print(f"\n=== {slug} · {idea['nombre']} ===")
    agente = cliente.beta.agents.create(name=f"Ideas · {idea['nombre']}", model="claude-sonnet-5", system=idea["system"], tools=idea["tools"])
    sesion = cliente.beta.sessions.create(agent=agente.id, environment_id=os.environ["ENVIRONMENT_ID"], title=f"Ideas · {idea['nombre']}",
                                          budget={"type": "limit", "max_list_cost": {"amount": "60", "currency": "USD"}})
    carpeta = AQUI / "salidas" / sesion.id
    carpeta.mkdir(parents=True, exist_ok=True)
    md = [f"# {idea['nombre']} · {sesion.id}\n", f"**Agente** `{agente.id}`\n", "**System prompt**\n", f"```\n{idea['system']}\n```\n",
          "**Tools** " + ", ".join(f"`{x['name']}`" for x in idea["tools"]) + "\n"]
    turnos, pendientes, n = list(idea["turnos"]), {}, 0

    def enviar(texto):
        nonlocal n
        n += 1
        print(f"  TÚ {n}    {texto}")
        md.append(f"## Turno {n}\n\n**user.message**\n\n```\n{texto}\n```\n")
        cliente.beta.sessions.events.send(sesion.id, events=[{"type": "user.message", "content": [{"type": "text", "text": texto}]}])

    with (carpeta / "eventos.jsonl").open("w") as bitacora, cliente.beta.sessions.events.stream(sesion.id) as stream:
        enviar(turnos.pop(0))
        for e in stream:
            bitacora.write(e.model_dump_json() + "\n")
            bitacora.flush()
            if e.type == "agent.custom_tool_use":
                pendientes[e.id] = e
                print(f"  PIDE    {e.name}({json.dumps(e.input, ensure_ascii=False)[:80]})")
                md.append(f"- **agent.custom_tool_use** `{e.name}`\n\n```\n{json.dumps(e.input, ensure_ascii=False, indent=2)}\n```\n")
            elif e.type == "agent.message":
                texto = "".join(b.text for b in e.content if b.type == "text")
                print(f"  DICE    {texto[:260].replace(chr(10), ' ')}")
                md.append(f"- **agent.message**\n\n```\n{texto}\n```\n")
            elif e.type == "session.error":
                print(f"  ERROR   {e.error}")
                md.append(f"- **session.error** `{e.error}`\n")
            elif e.type == "session.status_idle":
                razon = e.stop_reason.type if e.stop_reason else None
                if razon == "requires_action":
                    for event_id in e.stop_reason.event_ids:
                        p = pendientes.pop(event_id, None)
                        if p is None:
                            continue
                        resultado = idea["run"](p.name, p.input)
                        md.append(f"- **user.custom_tool_result** (corre en tu máquina)\n\n```\n{resultado}\n```\n")
                        cliente.beta.sessions.events.send(sesion.id, events=[{"type": "user.custom_tool_result", "custom_tool_use_id": event_id,
                                                                              "content": [{"type": "text", "text": resultado}]}])
                elif razon == "end_turn" and turnos:
                    enviar(turnos.pop(0))
                else:
                    md.append(f"\n**Fin:** `{razon}`\n")
                    break
    u = cliente.beta.sessions.retrieve(sesion.id).usage
    md.append(f"## Recibo\n\n{n} turnos · {u.active_seconds:.1f} s activos · {u.output_tokens} tokens de salida · {u.list_cost.amount} centavos de USD\n")
    (carpeta / "transcript.md").write_text("\n".join(md))
    print(f"  RECIBO  {n} turnos · {u.list_cost.amount} centavos · {carpeta}/transcript.md")
    return int(u.list_cost.amount)


if __name__ == "__main__":
    total = sum(correr(s, IDEAS[s]) for s in (sys.argv[1:] or IDEAS))
    print(f"\nTOTAL {total} centavos de USD")
