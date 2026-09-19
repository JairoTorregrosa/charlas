// 09 · El contraste. Cada query() arranca una sesión nueva: el agente no recuerda
// nada del turno anterior. Conversar hay que pedirlo: se guarda el session_id y
// se pasa en resume. (La otra vía es streaming input: un AsyncIterable de mensajes.)
import { query, type Options } from "@anthropic-ai/claude-agent-sdk";

const BASE: Options = {
  model: "claude-sonnet-5",
  systemPrompt:
    "Eres un asistente personal. Respondes en español, corto y con datos. " +
    "Usa tus tools y skills; no adivines fechas ni reservas.",
  tools: [],
  settingSources: [],
  strictMcpConfig: true,
  maxTurns: 2,
  maxBudgetUsd: 0.05,
  env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
};

async function turno(pregunta: string, resume?: string) {
  console.log(`\nTú: ${pregunta}`);
  let sesion = "";
  for await (const m of query({ prompt: pregunta, options: { ...BASE, resume } })) {
    if (m.type === "system" && m.subtype === "init") sesion = m.session_id;
    if (m.type === "assistant") {
      for (const b of m.message.content) {
        if (b.type === "text" && b.text.trim()) console.log(`Agente: ${b.text.trim()}`);
      }
    }
  }
  return sesion;
}

// Turno 1: le damos un dato.
const sesion = await turno(
  "Mi próximo vuelo es BOG → MDE el jueves 24 de septiembre de 2026 a las 06:15, reserva ABC123.",
);
console.log(`\n(session_id: ${sesion})`);

// Turno 2 sin resume: sesión nueva, memoria en blanco.
await turno("¿A qué hora sale mi vuelo y cuál es el código de reserva?");

// Turno 2 con resume: misma sesión, se acuerda.
await turno("¿A qué hora sale mi vuelo y cuál es el código de reserva?", sesion);
