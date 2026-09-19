// 07 · Un subagente: otro agente con su propio contexto, sus tools y su prompt.
// El principal no tiene acceso al correo. Delega, y solo recibe el resumen.
// Cada mensaje que viene de adentro trae parent_tool_use_id con el id de la delegación.
import "./entorno.ts"; // carga ANTHROPIC_API_KEY de .env
import { query } from "@anthropic-ai/claude-agent-sdk";
import { servidorGmail } from "./gmail_mcp.ts";

const conversacion = query({
  prompt:
    "Hoy es 19 de septiembre de 2026. Averigua cuándo es mi próximo vuelo delegando " +
    "en el subagente lector-de-correos, con run_in_background en false, y espera su " +
    "respuesta antes de contestarme.",
  options: {
    model: "claude-sonnet-5",
    systemPrompt:
      "Eres un asistente personal. Respondes en español, corto y con datos. " +
      "Usa tus tools y skills; no adivines fechas ni reservas.",
    tools: ["Task"], // el principal solo puede delegar (en el init la tool se llama Task)
    mcpServers: { gmail: servidorGmail },
    // Los permisos NO se heredan del bloque agents: van aquí, en el permiso global.
    allowedTools: ["mcp__gmail__buscar", "mcp__gmail__leer"],

    agents: {
      "lector-de-correos": {
        description: "Lee el correo del usuario y devuelve solo los datos duros del vuelo.",
        prompt:
          "Eres un lector de correos y respondes en español. Busca desde el 12 de " +
          "septiembre de 2026, lee los " +
          "candidatos e ignora publicidad, encuestas y hoteles. Devuelve en dos líneas: " +
          "ruta, día, hora y código de reserva del vuelo futuro más cercano.",
        tools: ["mcp__gmail__buscar", "mcp__gmail__leer"],
        mcpServers: ["gmail"], // hereda el servidor por nombre
        model: "sonnet",
        background: false, // el principal espera la respuesta en vez de seguir
        maxTurns: 10,
      },
    },

    forwardSubagentText: true, // sin esto no se ve lo que dice el subagente
    settingSources: [],
    strictMcpConfig: true,
    maxTurns: 12,
    maxBudgetUsd: 0.20,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

for await (const m of conversacion) {
  if (m.type === "assistant") {
    const quien = m.parent_tool_use_id ? `  [subagente ${m.parent_tool_use_id.slice(-6)}]` : "[principal]";
    for (const b of m.message.content) {
      if (b.type === "tool_use") console.log(`${quien} -> ${b.name}`);
      if (b.type === "text" && b.text.trim()) console.log(`${quien} ${b.text.trim()}`);
    }
  }
  if (m.type === "result" && m.subtype === "success") {
    console.log(`\nCosto total (incluye el subagente): $${m.total_cost_usd.toFixed(4)}`);
  }
}
