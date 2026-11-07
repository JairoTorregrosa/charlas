// 10 · Salida estructurada: el agente entrega datos, no un párrafo.
// Mismo agente del 08 con una sola diferencia: outputFormat con un JSON Schema.
// El SDK valida la respuesta y la deja en result.structured_output, ya como objeto.
// Uso: npm run 10
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { join } from "node:path";
import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";

const PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.";

const hoy = tool("hoy", "Devuelve la fecha de hoy en español.", {}, async () => ({
  content: [{ type: "text" as const, text: "sábado 7 de noviembre de 2026" }],
}));
const reloj = createSdkMcpServer({ name: "reloj", tools: [hoy], alwaysLoad: true });

const texto = { type: ["string", "null"] };
const VUELO = {
  type: "object",
  properties: {
    encontrado: { type: "boolean" },
    aerolinea: texto,
    origen: { ...texto, description: "código IATA, p. ej. BOG" },
    destino: { ...texto, description: "código IATA, p. ej. MDE" },
    fecha: { ...texto, description: "AAAA-MM-DD" },
    hora: { ...texto, description: "HH:MM, 24 horas" },
    reserva: texto,
  },
  required: ["encontrado", "aerolinea", "origen", "destino", "fecha", "hora", "reserva"],
  additionalProperties: false,
};

console.log(`Tú: ${PREGUNTA}\n`);

for await (const m of query({
  prompt: PREGUNTA,
  options: {
    model: "claude-sonnet-5-5",
    systemPrompt:
      "Eres un asistente personal que lee el correo del usuario. Usa tus tools y skills; " +
      "no adivines fechas ni reservas. Si no encuentras un vuelo futuro, deja encontrado=false " +
      "y los demás campos en null.",
    cwd: join(import.meta.dirname, "workspace"),
    settingSources: ["project"],
    skills: ["buscar-vuelo"],
    tools: ["Skill"],
    mcpServers: { reloj, gmail: servidorGmail },
    allowedTools: ["mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
    strictMcpConfig: true,
    outputFormat: { type: "json_schema", schema: VUELO }, // ← la pieza nueva
    maxTurns: 15,
    maxBudgetUsd: 0.25,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
})) {
  if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`-> ${b.name} ${JSON.stringify(b.input)}`);
    }
  }
  if (m.type === "result") {
    console.log(`\n[${m.subtype}] ${m.num_turns} turns · $${m.total_cost_usd.toFixed(4)}`);
    if (m.subtype === "success" && m.structured_output) {
      console.log("\nJSON VALIDADO (result.structured_output)");
      console.log(JSON.stringify(m.structured_output, null, 2));
    }
  }
}
