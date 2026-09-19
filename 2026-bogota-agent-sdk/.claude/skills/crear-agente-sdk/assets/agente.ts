// TODO nombre — TODO qué hace, en una línea.
// Uso: npx tsx agente.ts "otra pregunta"
import { join } from "node:path";
import { createSdkMcpServer, query, tool, type HookCallback } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";
import { Bitacora } from "./observar.ts";

const PEDIDO = process.argv[2] ?? "TODO el pedido por defecto";

// SYSTEM PROMPT: quién es y qué no debe adivinar.
const SYSTEM_PROMPT =
  "TODO Eres ... Respondes en español, corto y con datos. " +
  "Usa tus tools y skills; no adivines TODO.";

// TOOL PROPIA: datos o acciones de tu código. Bórrala si no la necesitas.
const miTool = tool(
  "TODO_nombre",
  "TODO qué devuelve y cuándo pedirla.",
  { TODO_arg: z.string() },
  async (args) => ({ content: [{ type: "text" as const, text: `TODO resultado para ${args.TODO_arg}` }] }),
);
const propias = createSdkMcpServer({ name: "propias", tools: [miTool], alwaysLoad: true });

// HOOK: ve los argumentos de cada tool call antes de que corra.
const guardrail: HookCallback = async (entrada) => {
  if (entrada.hook_event_name !== "PreToolUse") return {};
  const prohibido = false; // TODO la condición sobre entrada.tool_input
  if (!prohibido) return {};
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "TODO qué debe hacer el agente en su lugar.",
    },
  };
};

console.log(`PEDIDO    ${PEDIDO}\n`);

const conversacion = query({
  prompt: PEDIDO,
  options: {
    model: "claude-sonnet-5",
    systemPrompt: SYSTEM_PROMPT,
    // WORKSPACE Y TOOLS
    cwd: join(import.meta.dirname, "workspace"),
    settingSources: ["project"], // [] si no hay skills
    skills: ["TODO-nombre-de-la-skill"],
    tools: ["Skill"], // + las nativas que el objetivo exija
    mcpServers: { propias },
    // GUARDRAILS
    allowedTools: ["Skill", "mcp__propias__TODO_nombre"],
    disallowedTools: [],
    permissionMode: "dontAsk",
    hooks: { PreToolUse: [{ matcher: "mcp__propias__TODO_nombre", hooks: [guardrail] }] },
    maxTurns: 12,
    maxBudgetUsd: 0.25,
    // AISLAMIENTO
    strictMcpConfig: true,
    env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" },
  },
});

const bitacora = new Bitacora(join(import.meta.dirname, "salidas"), PEDIDO, SYSTEM_PROMPT);
try {
  for await (const m of conversacion) {
    bitacora.anotar(m); // cada evento queda guardado, pase lo que pase
    if (m.type === "system" && m.subtype === "init") {
      console.log(`ARRANQUE  tools=${JSON.stringify(m.tools)} mcp=${JSON.stringify(m.mcp_servers)}\n`);
    }
    if (m.type === "assistant") {
      for (const b of m.message.content) {
        if (b.type === "tool_use") console.log(`-> ${b.name} ${JSON.stringify(b.input)}`);
        if (b.type === "text" && b.text.trim()) console.log(`\nAGENTE    ${b.text.trim()}`);
      }
    }
    if (m.type === "result") {
      console.log(
        `\n[${m.subtype}] ${m.num_turns} turns · ${(m.duration_ms / 1000).toFixed(1)} s · ` +
          `USD ${m.total_cost_usd.toFixed(4)}`,
      );
    }
  }
} catch (e) {
  console.log(`\n[corte] ${e}`); // tocar un tope lanza excepción: es a propósito
} finally {
  bitacora.cerrar();
}
