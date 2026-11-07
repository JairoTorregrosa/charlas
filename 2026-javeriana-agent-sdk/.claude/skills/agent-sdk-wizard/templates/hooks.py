# hooks.py — el vigilante del paso 9.
#
# Un hook es código TUYO que corre en TU proceso, en un momento exacto del
# ciclo del agente. Corre ANTES que todo lo demás: antes de las reglas de
# permiso y antes del modo. Por eso es lo único que aguanta incluso con
# permission_mode="bypassPermissions".
#
# Este archivo trae los tres de la skill. Deja el que elegiste, borra los
# otros dos, y al final apunta HOOK a la función que quedó.
#
# TRAMPA: las claves que devuelve un hook van en camelCase, TAMBIÉN en Python
# (hookSpecificOutput, permissionDecision, permissionDecisionReason). Son
# TypedDicts: escribir permission_decision no lanza error, simplemente se
# ignora y el hook no hace nada. Falla en silencio.

import asyncio
import json
import pathlib
import time
from typing import Any


# ─── 9B · Bloquear comandos peligrosos ────────────────────────────────────
# Evento PreToolUse, matcher "Bash". Se registra así:
#   hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[HOOK])]}

PELIGROSOS = ("rm -rf", "rm -fr", "mkfs", "dd if=", ":(){")


async def bloquear_destructivo(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    comando = input_data.get("tool_input", {}).get("command", "")

    for patron in PELIGROSOS:
        if patron in comando:
            return {
                # systemMessage lo lee la PERSONA, no el modelo.
                "systemMessage": f"Hook bloqueó un comando destructivo: {comando}",
                "hookSpecificOutput": {
                    "hookEventName": input_data["hook_event_name"],
                    "permissionDecision": "deny",
                    # permissionDecisionReason SÍ lo lee el MODELO: le llega como
                    # resultado de la herramienta y guía su siguiente intento.
                    # Escríbelo como una instrucción, no como un portazo.
                    "permissionDecisionReason": (
                        f"El comando contiene '{patron}', prohibido por política. "
                        "Si necesitas limpiar, mueve los archivos a ./papelera/."
                    ),
                },
            }

    # Objeto vacío = sin opinión, que siga el flujo normal de permisos.
    return {}


# ─── 9C · Guardar un registro de todo lo que hace ─────────────────────────
# Evento PostToolUse, sin matcher (todas las herramientas). Se registra así:
#   hooks={"PostToolUse": [HookMatcher(hooks=[HOOK])]}
# Léelo después con:  cat auditoria.jsonl | jq

BITACORA = pathlib.Path("./auditoria.jsonl")


def _escribir(registro: dict[str, Any]) -> None:
    """Escritura bloqueante; la sacamos del event loop con to_thread."""
    with BITACORA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


async def registrar_uso(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    registro = {
        "ts": time.time(),
        "evento": input_data["hook_event_name"],
        "session_id": input_data["session_id"],
        "tool": input_data.get("tool_name"),
        "tool_use_id": tool_use_id,          # correlaciona Pre con Post
        "agente": input_data.get("agent_id"),  # presente solo dentro de un ayudante
        "input": input_data.get("tool_input"),
    }

    # Una excepción en el hook nunca debe tumbar al agente.
    try:
        await asyncio.to_thread(_escribir, registro)
    except Exception as e:  # noqa: BLE001
        print("fallo escribiendo bitácora:", e)

    # async_ = True: el agente no espera. Solo sirve para efectos secundarios
    # (log, métricas, notificaciones): un hook async no puede bloquear ni
    # modificar nada, porque el agente ya siguió.
    # OJO: en Python el campo lleva guion bajo (async es palabra reservada).
    return {"async_": True, "asyncTimeout": 5000}


# ─── 9D · Verificar el trabajo al final ───────────────────────────────────
# Evento Stop, SIN matcher — Stop los ignora por completo. Se registra así:
#   hooks={"Stop": [HookMatcher(hooks=[HOOK])]}
# Esto es un `if`, no un modelo: verificación determinista, gratis y honesta.

ENTREGABLE = pathlib.Path("./out/reporte.md")


async def exigir_entregable(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    # stop_hook_active es True cuando ESTE hook ya bloqueó una vez en el turno.
    # Sin la guarda, un agente que no puede cumplir queda en bucle infinito.
    if input_data.get("stop_hook_active"):
        return {}

    if ENTREGABLE.exists():
        return {}  # verificación pasada: que termine

    return {
        # El turno NO termina: el modelo lee `reason` y sigue trabajando.
        "decision": "block",
        "reason": (
            f"Falta el entregable: escribe tus conclusiones en {ENTREGABLE} "
            "antes de terminar."
        ),
    }


# ─── El que usa el agente ─────────────────────────────────────────────────
# Apunta HOOK a la función que elegiste en el paso 9.
HOOK = bloquear_destructivo
