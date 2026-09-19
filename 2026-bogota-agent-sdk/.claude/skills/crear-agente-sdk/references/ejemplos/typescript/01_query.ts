// 01 · query(): entra un prompt, sale una respuesta. El programa termina solo.
// Sin ninguna tool. El agente no puede mirar tu correo, y lo dice.
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { query } from "@anthropic-ai/claude-agent-sdk";

const SISTEMA =
  "Eres un asistente personal. Respondes en español, corto y con datos. " +
  "Usa tus tools y skills; no adivines fechas ni reservas.";

const PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.";

console.log(`Tú: ${PREGUNTA}\n`);

const conversacion = query({
  prompt: PREGUNTA,
  options: {
    model: "claude-sonnet-5",
    systemPrompt: SISTEMA,
    tools: [], // ninguna tool disponible: el agente solo puede hablar
    settingSources: [], // no lee ~/.claude ni el .claude del proyecto
    strictMcpConfig: true, // no entran los conectores de claude.ai
    maxTurns: 2,
    maxBudgetUsd: 0.05,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

// El stream se recorre entero: salir con break se deja mensajes sin leer.
for await (const mensaje of conversacion) {
  if (mensaje.type === "assistant") {
    for (const bloque of mensaje.message.content) {
      if (bloque.type === "text") console.log(`Agente: ${bloque.text}`);
    }
  }
  if (mensaje.type === "result" && mensaje.subtype === "success") {
    console.log(`\nCosto: $${mensaje.total_cost_usd.toFixed(4)}`);
  }
}
