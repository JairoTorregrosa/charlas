// 03 · Una tool propia. tool() describe la función, createSdkMcpServer la publica.
// El nombre que ve el agente es mcp__{servidor}__{tool}: aquí mcp__reloj__hoy.
import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";

// El tercer argumento es el esquema de entrada en zod. Aquí no recibe nada.
const hoy = tool(
  "hoy",
  "Devuelve la fecha de hoy en español.",
  {},
  async () => ({
    content: [{ type: "text" as const, text: "sábado 19 de septiembre de 2026" }],
  }),
);

// alwaysLoad evita el paso previo de ToolSearch: el agente ve la tool completa desde el init.
const reloj = createSdkMcpServer({ name: "reloj", tools: [hoy], alwaysLoad: true });

const conversacion = query({
  prompt: "¿Qué fecha es hoy y qué día de la semana cae?",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas.",

    // tools decide QUÉ EXISTE: [] apaga todas las tools de Claude Code
    // (Read, Bash, Edit...). Las del servidor MCP siguen existiendo.
    tools: [],
    mcpServers: { reloj },

    // allowedTools decide QUÉ SE APRUEBA SIN PREGUNTAR. Sin esta línea el
    // agente pediría permiso y, sin nadie que responda, la llamada se cae.
    allowedTools: ["mcp__reloj__hoy"],

    settingSources: [],
    strictMcpConfig: true,
    maxTurns: 4,
    maxBudgetUsd: 0.05,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`-> llama ${b.name}`);
      if (b.type === "text" && b.text.trim()) console.log(`Agente: ${b.text.trim()}`);
    }
  }
  if (m.type === "result" && m.subtype === "success") {
    console.log(`\nCosto: $${m.total_cost_usd.toFixed(4)}`);
  }
}
