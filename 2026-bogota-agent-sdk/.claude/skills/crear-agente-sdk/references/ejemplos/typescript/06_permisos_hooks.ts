// 06 · Quién deja pasar qué. Tres porteros distintos:
//   tools           -> qué tools EXISTEN
//   allowedTools    -> qué se aprueba sin preguntar
//   disallowedTools -> qué se niega siempre
//   permissionMode  -> la política general cuando no hay regla
// Y encima de todos, los hooks: código tuyo que corre antes de cada llamada.
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { query } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";

const conversacion = query({
  prompt:
    "Hoy es 19 de septiembre de 2026. Busca mis correos desde el 12 de septiembre, " +
    "léelos TODOS uno por uno empezando por c1, incluidos los de publicidad, y " +
    "después dime cuál es mi próximo vuelo.",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas.",
    tools: [],
    mcpServers: { gmail: servidorGmail },
    allowedTools: ["mcp__gmail__buscar", "mcp__gmail__leer"],
    disallowedTools: ["Bash", "Write", "Edit"], // negadas aunque alguien las encienda
    permissionMode: "default",

    hooks: {
      PreToolUse: [
        {
          matcher: "mcp__gmail__leer", // solo se dispara en esa tool
          hooks: [
            async (entrada) => {
              const datos = (entrada as { tool_input?: { id?: string } }).tool_input ?? {};
              if (datos.id !== "c1") return {}; // {} = no opino, que sigan los demás porteros
              const motivo = "El correo c1 es publicidad. No lo leas y sigue con los demás.";
              console.log(`[hook] niega leer c1 -> ${motivo}`);
              return {
                hookSpecificOutput: {
                  hookEventName: "PreToolUse",
                  permissionDecision: "deny",
                  permissionDecisionReason: motivo, // el LLM lee este texto y se reacomoda
                },
              };
            },
          ],
        },
      ],
    },

    settingSources: [],
    strictMcpConfig: true,
    maxTurns: 12,
    maxBudgetUsd: 0.15,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "assistant") {
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`-> ${b.name} ${JSON.stringify(b.input)}`);
      if (b.type === "text" && b.text.trim()) console.log(`\nAgente: ${b.text.trim()}`);
    }
  }
  if (m.type === "result" && m.subtype === "success") {
    console.log(`\nNegadas: ${m.permission_denials.length} · Costo: $${m.total_cost_usd.toFixed(4)}`);
  }
}
