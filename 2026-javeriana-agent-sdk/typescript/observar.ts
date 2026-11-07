// observar.ts — la bitácora del agente. Guarda TODO lo que emite el SDK y lo vuelve legible.
//
// Cada corrida deja una carpeta salidas/<fecha-hora>/ con dos archivos:
//   eventos.jsonl   cada mensaje del SDK, crudo y completo, uno por línea. Se escribe en el
//                   momento: si el agente se cae, lo que alcanzó a pasar queda.
//   transcript.md   lo mismo, para leer: qué tenía el agente antes de empezar y, llamada por
//                   llamada al LLM, qué papeles nuevos había en el contexto y qué respondió.
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { SDKMessage } from "@anthropic-ai/claude-agent-sdk";

const bloque = (s: string) => "```\n" + s.trim() + "\n```\n";
const texto = (c: unknown): string =>
  typeof c === "string" ? c
  : Array.isArray(c) ? c.map((x) => (x?.type === "text" ? x.text : JSON.stringify(x))).join("\n")
  : c == null ? "" : JSON.stringify(c);

export class Bitacora {
  readonly carpeta: string;
  private md: string[] = [];
  private pendiente: { etiqueta: string; texto: string; ref?: string }[] = [];
  private llamada: string | undefined;
  private llamadas = 0;
  private n = 0;

  constructor(salidas: string, pedido: string, systemPrompt = "") {
    const d = new Date(), p2 = (x: number) => String(x).padStart(2, "0");
    const sello = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}-${p2(d.getHours())}${p2(d.getMinutes())}${p2(d.getSeconds())}`;
    this.carpeta = join(salidas, sello);
    mkdirSync(this.carpeta, { recursive: true });
    writeFileSync(join(this.carpeta, "eventos.jsonl"), "");
    this.md.push(`# Transcript · ${sello}\n`, "## Antes de empezar\n", "**System prompt**\n",
      bloque(systemPrompt || "(el del SDK)"));
    this.pendiente.push({ etiqueta: "user message", texto: pedido });
  }

  anotar(m: SDKMessage) {
    appendFileSync(join(this.carpeta, "eventos.jsonl"),
      JSON.stringify({ n: this.n++, hora: new Date().toISOString(), ...m }) + "\n");

    if (m.type === "system" && m.subtype === "init") {
      const lista = (xs: string[]) => xs.map((x) => `\`${x}\``).join(", ") || "(ninguna)";
      this.md.push(`**Modelo** \`${m.model}\` · **permisos** \`${m.permissionMode}\`\n`,
        `**Tools** ${lista(m.tools)}\n`,
        `**MCP** ${lista(m.mcp_servers.map((s) => `${s.name} (${s.status})`))}\n`,
        `**Skills** ${lista(m.skills ?? [])}\n`);
    } else if (m.type === "user") {
      const quien = m.parent_tool_use_id ? "subagente · " : "";
      const c = m.message.content;
      for (const b of typeof c === "string" ? [{ type: "text" as const, text: c }] : c) {
        if (b.type === "tool_result") {
          this.pendiente.push({ etiqueta: `${quien}tool result${b.is_error ? " · ERROR" : ""}`,
            texto: texto(b.content), ref: b.tool_use_id });
        } else if (b.type === "text") {
          this.pendiente.push({ etiqueta: `${quien}user message`, texto: b.text });
        }
      }
    } else if (m.type === "assistant") {
      if (m.message.id !== this.llamada) { // una respuesta del LLM puede llegar en varios mensajes
        this.llamada = m.message.id;
        this.llamadas++;
        const u = m.message.usage;
        const leidos = (u?.input_tokens ?? 0) + (u?.cache_read_input_tokens ?? 0) + (u?.cache_creation_input_tokens ?? 0);
        this.md.push(`## Llamada ${this.llamadas} al LLM${m.parent_tool_use_id ? " (subagente)" : ""}\n`,
          `El LLM leyó el contexto completo: **${leidos.toLocaleString("en-US")} tokens**. Papeles nuevos desde la llamada anterior:\n`);
        for (const p of this.pendiente) {
          this.md.push(`- **${p.etiqueta}**${p.ref ? ` · id \`${p.ref.slice(-6)}\`` : ""}\n`, bloque(p.texto));
        }
        if (!this.pendiente.length) this.md.push("- (ninguno)\n");
        this.pendiente = [];
        this.md.push("**Respondió:**\n");
      }
      for (const b of m.message.content) {
        if (b.type === "tool_use") {
          this.md.push(`- **tool call** \`${b.name}\` · id \`${b.id.slice(-6)}\`\n`, bloque(JSON.stringify(b.input, null, 2)));
        } else if (b.type === "text" && b.text.trim()) {
          this.md.push("- **assistant message**\n", bloque(b.text));
        } else if (b.type === "thinking" && b.thinking.trim()) {
          this.md.push("- *pensó*\n", bloque(b.thinking));
        }
      }
    } else if (m.type === "result") {
      this.md.push("## Recibo\n",
        `\`${m.subtype}\` · ${m.num_turns} turns (num_turns del SDK) · ${this.llamadas} llamadas al LLM · ` +
          `${(m.duration_ms / 1000).toFixed(1)} s · USD ${m.total_cost_usd.toFixed(4)}\n`);
      if (m.permission_denials?.length) this.md.push(`**Negados por permisos o hooks:** ${m.permission_denials.length}\n`);
    }
  }

  cerrar() {
    writeFileSync(join(this.carpeta, "transcript.md"), this.md.join("\n"));
    console.log(`\nBITÁCORA  ${this.carpeta}/transcript.md  ·  eventos.jsonl (${this.n} eventos)`);
  }
}
