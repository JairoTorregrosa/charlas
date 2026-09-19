// 08 · El asistente de viaje completo: tool propia + MCP + skill + topes + bitácora.
// Cada corrida deja salidas/<fecha-hora>/eventos.jsonl y transcript.md (llamada por llamada).
// Uso: npm run 08 -- "tu pregunta"   (sin pregunta usa la del taller)
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { join } from "node:path";
import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";
import { Bitacora } from "./observar.ts";

const PREGUNTA =
  process.argv[2] ?? "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.";

const hoy = tool("hoy", "Devuelve la fecha de hoy en español.", {}, async () => ({
  content: [{ type: "text" as const, text: "sábado 19 de septiembre de 2026" }],
}));
const reloj = createSdkMcpServer({ name: "reloj", tools: [hoy], alwaysLoad: true });

console.log(`Tú: ${PREGUNTA}\n`);

const SYSTEM_PROMPT =
  "Eres un asistente personal. Respondes en español, corto y con datos. " +
  "Usa tus tools y skills; no adivines fechas ni reservas.";

const conversacion = query({
  prompt: PREGUNTA,
  options: {
    model: "claude-sonnet-5",
    systemPrompt: SYSTEM_PROMPT,
    cwd: join(import.meta.dirname, "workspace"),
    settingSources: ["project"],
    skills: ["buscar-vuelo"],
    tools: ["Skill"],
    mcpServers: { reloj, gmail: servidorGmail },
    allowedTools: ["mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
    strictMcpConfig: true,
    maxTurns: 15, // tope de turns del loop
    maxBudgetUsd: 0.25, // tope de gasto: al llegar, el agente para
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

const bitacora = new Bitacora(join(import.meta.dirname, "salidas"), PREGUNTA, SYSTEM_PROMPT);
for await (const m of conversacion) {
  bitacora.anotar(m);
  if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`-> ${b.name} ${JSON.stringify(b.input)}`);
      if (b.type === "text" && b.text.trim()) console.log(`\nAgente: ${b.text.trim()}`);
    }
  }
  if (m.type === "result") {
    console.log(
      `\n[${m.subtype}] ${m.num_turns} turns · ${(m.duration_ms / 1000).toFixed(1)} s · ` +
        `$${m.total_cost_usd.toFixed(4)}`,
    );
  }
}

bitacora.cerrar();
