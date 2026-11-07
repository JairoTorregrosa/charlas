"""Conversar con una sesión: mandar un mensaje y atender lo que pida hasta que termine.

Reglas que este módulo resuelve para que el taller no tropiece con ellas:

1. El stream solo entrega lo que pasa después de abrirlo. Se abre primero y
   después se manda el mensaje.
2. `session.status_idle` no siempre significa "terminé". Con stop_reason
   `requires_action`, la sesión está esperando que respondas: el resultado de
   una custom tool o la aprobación de una tool con `always_ask`. El evento trae
   `event_ids` con exactamente lo que falta.
3. Se responde una sola vez por evento. Responder dos veces la misma llamada
   devuelve error.
"""
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import anthropic

HerramientaLocal = Callable[[dict[str, Any]], str]
# Devuelve True/False, o (False, "motivo") para que el agente sepa por qué se negó.
Aprobador = Callable[[Any], "bool | tuple[bool, str]"]

# Eventos que pueden quedar esperando una respuesta tuya.
_ESPERAN_RESPUESTA = {"agent.custom_tool_use", "agent.tool_use", "agent.mcp_tool_use"}


@dataclass
class Resultado:
    motivo: str  # end_turn, budget_reached, retries_exhausted, refusal o terminated
    texto: str = ""
    errores: list[str] = field(default_factory=list)
    # Con un outcome: satisfied, needs_revision, max_iterations_reached, failed o interrupted.
    evaluaciones: list[str] = field(default_factory=list)


def mensaje(texto: str) -> Any:
    return {"type": "user.message", "content": [{"type": "text", "text": texto}]}


def conversar(
    client: anthropic.Anthropic,
    session_id: str,
    texto: str | None = None,
    *,
    eventos: list[Any] | None = None,
    herramientas: dict[str, HerramientaLocal] | None = None,
    aprobar: Aprobador | None = None,
    mostrar: bool = True,
) -> Resultado:
    """Manda `texto` a la sesión y atiende sus pedidos hasta que quede idle de verdad.

    eventos: en vez de un mensaje, los eventos que quieras mandar (por ejemplo un
        `user.define_outcome`).
    herramientas: nombre de custom tool -> función que recibe el input y devuelve texto.
    aprobar: función que decide si se permite una tool con permiso `always_ask`.
    """
    if eventos is None:
        if texto is None:
            raise ValueError("Pasa un texto o una lista de eventos.")
        eventos = [mensaje(texto)]
    herramientas = herramientas or {}
    vistos: dict[str, Any] = {}
    respondidos: set[str] = set()
    partes: list[str] = []
    errores: list[str] = []
    evaluaciones: list[str] = []

    try:
        with client.beta.sessions.events.stream(session_id) as stream:
            client.beta.sessions.events.send(session_id, events=eventos)
            evento: Any
            for evento in stream:
                if mostrar:
                    imprimir(evento)

                if evento.type in _ESPERAN_RESPUESTA:
                    vistos[evento.id] = evento
                elif evento.type == "agent.message":
                    partes.extend(b.text for b in evento.content if b.type == "text")
                elif evento.type == "span.outcome_evaluation_end":
                    evaluaciones.append(evento.result)
                elif evento.type == "session.error":
                    errores.append(_describir_error(evento))
                elif evento.type == "session.status_terminated":
                    return Resultado("terminated", "".join(partes), errores, evaluaciones)
                elif evento.type == "session.status_idle":
                    motivo = evento.stop_reason.type
                    if motivo != "requires_action":
                        return Resultado(motivo, "".join(partes), errores, evaluaciones)
                    pendientes = [i for i in evento.stop_reason.event_ids if i not in respondidos]
                    respuestas: list[Any] = [
                        _responder(_buscar(client, session_id, i, vistos), herramientas, aprobar)
                        for i in pendientes
                    ]
                    if respuestas:
                        client.beta.sessions.events.send(session_id, events=respuestas)
                        respondidos.update(pendientes)
    except KeyboardInterrupt:
        # Salir del script no detiene la sesión en el servidor: hay que interrumpirla.
        client.beta.sessions.events.send(session_id, events=[{"type": "user.interrupt"}])
        print(f"\nInterrumpí la sesión {session_id}.")
        raise
    except anthropic.APIConnectionError:
        # Se cayó el wifi. El agente sigue trabajando en el servidor; no vuelvas a
        # correr el caso, que crea otra sesión y cobra otra vez.
        print(
            f"\n{ROJO}Se cortó la conexión, pero la sesión sigue en el servidor.{FIN}\n"
            f"Retómala con: uv run pasos/reanudar.py {session_id}"
        )
        raise SystemExit(1) from None

    raise RuntimeError(
        "El stream se cerró antes de que la sesión terminara. La sesión sigue viva en el "
        f"servidor: revísala en https://platform.claude.com/sessions ({session_id})."
    )


def _buscar(client: anthropic.Anthropic, session_id: str, evento_id: str, vistos: dict[str, Any]) -> Any:
    """El evento casi siempre llegó por el stream. Si no, se busca en el historial."""
    if evento_id in vistos:
        return vistos[evento_id]
    for evento in client.beta.sessions.events.list(session_id):
        if evento.id == evento_id:
            vistos[evento_id] = evento
            return evento
    raise RuntimeError(f"La sesión espera respuesta al evento {evento_id}, pero no aparece en su historial.")


def _responder(evento: Any, herramientas: dict[str, HerramientaLocal], aprobar: Aprobador | None) -> dict[str, Any]:
    if evento.type == "agent.custom_tool_use":
        funcion = herramientas.get(evento.name)
        if funcion is None:
            return _resultado_custom(evento.id, f"No hay implementación local para la tool {evento.name}.", error=True)
        try:
            return _resultado_custom(evento.id, funcion(dict(evento.input)))
        except Exception as e:  # el error vuelve al agente para que decida qué hacer
            return _resultado_custom(evento.id, f"{type(e).__name__}: {e}", error=True)

    # agent.tool_use o agent.mcp_tool_use con permiso always_ask
    if aprobar is None:
        return {
            "type": "user.tool_confirmation",
            "tool_use_id": evento.id,
            "result": "deny",
            "deny_message": "Este script no tiene a nadie para aprobar tools.",
        }
    try:
        decision = aprobar(evento)
    except Exception as e:  # sin respuesta, la sesión quedaría pausada para siempre
        decision = (False, f"El aprobador falló ({type(e).__name__}: {e}).")
    permitido, motivo = decision if isinstance(decision, tuple) else (decision, "")
    respuesta: dict[str, Any] = {
        "type": "user.tool_confirmation",
        "tool_use_id": evento.id,
        "result": "allow" if permitido else "deny",
    }
    if not permitido:
        respuesta["deny_message"] = motivo or "La persona a cargo no aprobó este comando."
    return respuesta


def _resultado_custom(tool_use_id: str, texto: str, error: bool = False) -> dict[str, Any]:
    return {
        "type": "user.custom_tool_result",
        "custom_tool_use_id": tool_use_id,
        "content": [{"type": "text", "text": texto}],
        "is_error": error,
    }


def _describir_error(evento: Any) -> str:
    error = getattr(evento, "error", None)
    tipo = getattr(error, "type", None) or str(error)
    detalle = getattr(error, "message", None)
    return f"{tipo}: {detalle}" if detalle else tipo


def _reintentando(evento: Any) -> bool:
    estado = getattr(getattr(evento, "error", None), "retry_status", None)
    return getattr(estado, "type", estado) == "retrying"


# ── Salida en la terminal ────────────────────────────────────────────────

GRIS, AZUL, AMARILLO, ROJO, FIN = "\033[90m", "\033[94m", "\033[93m", "\033[91m", "\033[0m"


def _corto(valor: Any, limite: int = 160) -> str:
    texto = valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def imprimir(evento: Any) -> None:
    tipo = evento.type
    if tipo == "agent.message":
        for bloque in evento.content:
            if bloque.type == "text":
                print(bloque.text, flush=True)
    elif tipo == "agent.tool_use":
        entrada = evento.input.get("command") or evento.input.get("file_path") or evento.input
        print(f"{AZUL}  → {evento.name}{FIN} {GRIS}{_corto(entrada)}{FIN}", flush=True)
    elif tipo in ("agent.custom_tool_use", "agent.mcp_tool_use"):
        print(f"{AMARILLO}  → {evento.name} (la corres tú){FIN} {GRIS}{_corto(evento.input)}{FIN}", flush=True)
    elif tipo == "session.error":
        if _reintentando(evento):
            print(f"{GRIS}  · {_describir_error(evento)} (el servidor reintenta solo){FIN}", flush=True)
        else:
            print(f"{ROJO}  ! error de la sesión: {_describir_error(evento)}{FIN}", flush=True)
    elif tipo == "workflow_run.created":
        fases = " → ".join(getattr(f, "name", "?") for f in evento.phases)
        print(f"{AMARILLO}  ⧉ workflow run «{evento.name}»: {fases}{FIN}", flush=True)
    elif tipo == "workflow_run.status_ended":
        print(f"{AMARILLO}  ⧉ workflow run terminó: {getattr(evento.result, 'type', evento.result)}{FIN}", flush=True)
    elif tipo == "workflow_run.error":
        print(f"{ROJO}  ! workflow run: {_corto(str(getattr(evento, 'error', '')))}{FIN}", flush=True)
    elif tipo == "session.thread_created":
        print(f"{GRIS}  ⧉ nuevo agente en la sesión{FIN}", flush=True)
    elif tipo == "span.outcome_evaluation_start":
        print(f"{AMARILLO}  ⚖ el evaluador revisa el entregable (ronda {evento.iteration + 1}){FIN}", flush=True)
    elif tipo == "span.outcome_evaluation_end":
        print(f"{AMARILLO}  ⚖ veredicto: {evento.result}{FIN} {GRIS}{_corto(evento.explanation or '', 400)}{FIN}", flush=True)
    elif tipo == "session.status_idle" and evento.stop_reason.type != "requires_action":
        print(f"{GRIS}  · sesión en idle ({evento.stop_reason.type}){FIN}", flush=True)
