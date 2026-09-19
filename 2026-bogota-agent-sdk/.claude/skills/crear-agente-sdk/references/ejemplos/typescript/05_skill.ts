// 05 · Una skill es un archivo en disco: workspace/.claude/skills/buscar-vuelo/SKILL.md
// No hay API para registrarla. El agente la encuentra por dos opciones juntas:
// cwd (dónde mira) y settingSources: ["project"] (que lea el .claude de ahí).
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { join } from "node:path";
import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";

const hoy = tool("hoy", "Devuelve la fecha de hoy en español.", {}, async () => ({
  content: [{ type: "text" as const, text: "sábado 19 de septiembre de 2026" }],
}));
const reloj = createSdkMcpServer({ name: "reloj", tools: [hoy], alwaysLoad: true });

const conversacion = query({
  prompt: "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas.",
    cwd: join(import.meta.dirname, "workspace"),
    settingSources: ["project"], // lee workspace/.claude, no el tuyo
    skills: ["buscar-vuelo"], // enciende solo esta skill
    tools: ["Skill"], // con una lista explícita de tools hay que incluir Skill a mano
    mcpServers: { reloj, gmail: servidorGmail },
    allowedTools: ["mcp__reloj__hoy", "mcp__gmail__buscar", "mcp__gmail__leer"],
    strictMcpConfig: true, // también ignora el .mcp.json del workspace
    maxTurns: 12,
    maxBudgetUsd: 0.15,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "system" && m.subtype === "init") {
    const esta = m.skills.includes("buscar-vuelo") ? "sí" : "no";
    console.log(`[init] ¿el agente ve la skill buscar-vuelo? ${esta}\n`);
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
