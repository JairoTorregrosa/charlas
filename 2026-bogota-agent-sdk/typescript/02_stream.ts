// 02 · El stream: query() devuelve mensajes, no un string. Aquí se etiqueta cada uno.
// La tool hoy() se explica en 03; acá solo sirve para que haya algo que mirar.
import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";

const hoy = tool("hoy", "Devuelve la fecha de hoy.", {}, async () => ({
  content: [{ type: "text" as const, text: "sábado 19 de septiembre de 2026" }],
}));
const reloj = createSdkMcpServer({ name: "reloj", tools: [hoy], alwaysLoad: true });

const conversacion = query({
  prompt: "¿Qué día es hoy? Respóndeme en una línea.",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas: la fecha la da la tool hoy().",
    tools: [],
    mcpServers: { reloj },
    allowedTools: ["mcp__reloj__hoy"],
    settingSources: [],
    strictMcpConfig: true,
    maxTurns: 4,
    maxBudgetUsd: 0.05,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "system" && m.subtype === "init") {
    console.log(`[init]        modelo ${m.model} · tools: ${m.tools.join(", ") || "ninguna"}`);
  } else if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "text" && b.text.trim()) console.log(`[el LLM dice] ${b.text.trim()}`);
      if (b.type === "tool_use") console.log(`[tool call]   ${b.name} ${JSON.stringify(b.input)}`);
    }
  } else if (m.type === "user") {
    const bloques = Array.isArray(m.message.content) ? m.message.content : [];
    for (const b of bloques) {
      if (b.type === "tool_result") console.log(`[tool result] ${JSON.stringify(b.content)}`);
    }
  } else if (m.type === "result" && m.subtype === "success") {
    // num_turns cuenta vueltas del loop (modelo → tools → modelo), no turnos de
    // conversación: una sola pregunta tuya puede dar varias vueltas.
    console.log(
      `[recibo]      $${m.total_cost_usd.toFixed(4)} · ${m.duration_ms} ms · num_turns=${m.num_turns}`,
    );
  }
}
