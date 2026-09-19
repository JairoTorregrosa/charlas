// 04 · Un servidor MCP entero. gmail_mcp.ts publica dos tools: buscar y leer.
// Se enchufa igual que una tool suelta: una entrada más en mcpServers.
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { query } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";

const conversacion = query({
  prompt:
    "Hoy es sábado 19 de septiembre de 2026. Busca en mi correo los mensajes " +
    "de aerolíneas desde el 12 de septiembre y dime qué encontraste.",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas.",
    tools: [],
    mcpServers: { gmail: servidorGmail },

    // La clave de mcpServers es el nombre que aparece en el id de cada tool.
    allowedTools: ["mcp__gmail__buscar", "mcp__gmail__leer"],

    settingSources: [],
    strictMcpConfig: true, // sin esto entran los conectores de claude.ai y el agente iría a tu Gmail real
    maxTurns: 8,
    maxBudgetUsd: 0.10,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "system" && m.subtype === "init") {
    const estado = m.mcp_servers.map((s) => `${s.name}=${s.status}`).join(", ");
    console.log(`[init] servidores MCP: ${estado}`);
  }
  if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`-> ${b.name} ${JSON.stringify(b.input)}`);
      if (b.type === "text" && b.text.trim()) console.log(`\nAgente: ${b.text.trim()}`);
    }
  }
  if (m.type === "result" && m.subtype === "success") {
    console.log(`\nCosto: $${m.total_cost_usd.toFixed(4)}`);
  }
}
