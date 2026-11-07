// hooks.ts — el vigilante del paso 9.
//
// Un hook es código TUYO que corre en TU proceso, en un momento exacto del
// ciclo del agente. Corre ANTES que todo lo demás: antes de las reglas de
// permiso y antes del modo. Por eso es lo único que aguanta incluso con
// permissionMode: "bypassPermissions".
//
// Este archivo trae los tres de la skill. Deja el que elegiste, borra los
// otros dos, y al final apunta HOOK a la función que quedó.

import { appendFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import type {
  HookCallback,
  PreToolUseHookInput,
  PostToolUseHookInput,
  StopHookInput,
} from "@anthropic-ai/claude-agent-sdk";

// ─── 9B · Bloquear comandos peligrosos ────────────────────────────────────
// Evento PreToolUse, matcher "Bash". Se registra así:
//   hooks: { PreToolUse: [{ matcher: "Bash", hooks: [HOOK] }] }

const PELIGROSOS = ["rm -rf", "rm -fr", "mkfs", "dd if=", ":(){"];

export const bloquearDestructivo: HookCallback = async (input) => {
  const pre = input as PreToolUseHookInput;
  // tool_input llega como unknown: hay que hacer cast.
  const toolInput = (pre.tool_input ?? {}) as Record<string, unknown>;
  const comando = (toolInput.command as string) ?? "";

  const patron = PELIGROSOS.find((p) => comando.includes(p));
  if (patron) {
    return {
      // systemMessage lo lee la PERSONA, no el modelo.
      systemMessage: `Hook bloqueó un comando destructivo: ${comando}`,
      hookSpecificOutput: {
        hookEventName: pre.hook_event_name,
        permissionDecision: "deny",
        // permissionDecisionReason SÍ lo lee el MODELO: le llega como resultado
        // de la herramienta y guía su siguiente intento. Escríbelo como una
        // instrucción, no como un portazo.
        permissionDecisionReason:
          `El comando contiene '${patron}', prohibido por política. ` +
          "Si necesitas limpiar, mueve los archivos a ./papelera/.",
      },
    };
  }

  // Objeto vacío = sin opinión, que siga el flujo normal de permisos.
  return {};
};

// ─── 9C · Guardar un registro de todo lo que hace ─────────────────────────
// Evento PostToolUse, sin matcher (todas las herramientas). Se registra así:
//   hooks: { PostToolUse: [{ hooks: [HOOK] }] }
// Léelo después con:  cat auditoria.jsonl | jq

const BITACORA = "./auditoria.jsonl";

export const registrarUso: HookCallback = async (input, toolUseID) => {
  const evt = input as PostToolUseHookInput;
  const registro = {
    ts: Date.now(),
    evento: evt.hook_event_name,
    sessionId: evt.session_id,
    tool: evt.tool_name,
    toolUseId: toolUseID, // correlaciona Pre con Post
    agente: evt.agent_id, // presente solo dentro de un ayudante
    input: evt.tool_input,
  };

  // Una excepción en el hook nunca debe tumbar al agente.
  appendFile(BITACORA, JSON.stringify(registro) + "\n").catch((e) =>
    console.error("fallo escribiendo bitácora:", e),
  );

  // async: true → el agente sigue sin esperar. Solo sirve para efectos
  // secundarios (log, métricas, notificaciones): un hook async no puede
  // bloquear ni modificar nada, porque el agente ya siguió.
  return { async: true, asyncTimeout: 5000 };
};

// ─── 9D · Verificar el trabajo al final ───────────────────────────────────
// Evento Stop, SIN matcher — Stop los ignora por completo. Se registra así:
//   hooks: { Stop: [{ hooks: [HOOK] }] }
// Esto es un `if`, no un modelo: verificación determinista, gratis y honesta.

const ENTREGABLE = "./out/reporte.md";

export const exigirEntregable: HookCallback = async (input) => {
  const stop = input as StopHookInput;

  // stop_hook_active es true cuando ESTE hook ya bloqueó una vez en el turno.
  // Sin la guarda, un agente que no puede cumplir queda en bucle infinito.
  if (stop.stop_hook_active) return {};

  if (existsSync(ENTREGABLE)) return {}; // verificación pasada: que termine

  return {
    // El turno NO termina: el modelo lee `reason` y sigue trabajando.
    decision: "block",
    reason:
      `Falta el entregable: escribe tus conclusiones en ${ENTREGABLE} ` +
      "antes de terminar.",
  };
};

// ─── El que usa el agente ─────────────────────────────────────────────────
// Apunta HOOK a la función que elegiste en el paso 9.
export const HOOK = bloquearDestructivo;
