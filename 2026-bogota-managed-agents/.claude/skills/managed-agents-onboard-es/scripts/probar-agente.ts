// Runs one test session for an agent and saves what it produced.
//   bun scripts/probar-agente.ts tests/<nombre>.json   (desde la raíz del proyecto, junto a claude-lock.json)
// The spec names the agent directory, the kickoff events, and optional vaults and resources.
// Paused calls are denied (nobody is watching a test), and custom tools get answers from
// tests/fixtures/<agent>.ts when that file exists. Every session has a USD 20 budget.
import Anthropic from "@anthropic-ai/sdk";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";

interface Spec {
  agent: string; // directory under agents/
  title: string;
  vault_ids?: string[];
  resources?: unknown[];
  events: unknown[];
}

const specPath = process.argv[2];
if (!specPath) throw new Error("usage: bun scripts/test-agent.ts tests/<name>.json");
const spec: Spec = JSON.parse(readFileSync(specPath, "utf8"));
const lock = JSON.parse(readFileSync("claude-lock.json", "utf8")).resources;
const idOf = (path: string): string => {
  const id = lock[path]?.id;
  if (!id) throw new Error(`${path} is not in claude-lock.json`);
  return id;
};

// Memory stores can be named by their file path in the spec, like in a deployment file.
const resources = (spec.resources ?? []).map((r) =>
  typeof r === "string" ? { type: "memory_store", memory_store_id: idOf(r) } : r,
);

const fixturePath = `tests/fixtures/${spec.agent}.ts`;
const fixture: { answer?: (name: string, input: any) => string } = existsSync(fixturePath)
  ? await import(`../${fixturePath}`)
  : {};

const client = new Anthropic();
const session = await client.beta.sessions.create({
  agent: idOf(`./agents/${spec.agent}/agent.md`),
  environment_id: idOf(`./agents/${spec.agent}/environment.yaml`),
  title: spec.title,
  vault_ids: spec.vault_ids ?? [],
  resources: resources as any,
  budget: { type: "limit", max_list_cost: { amount: "2000", currency: "USD" } },
});
const outDir = `tests/out/${spec.agent}/${session.id}`;
mkdirSync(outDir, { recursive: true });
console.log(`[${spec.agent}] ${session.id} https://platform.claude.com/workspaces/default/sessions/${session.id}`);

const stream = await client.beta.sessions.events.stream(session.id);
await client.beta.sessions.events.send(session.id, { events: spec.events as any });

const log: string[] = [];
for await (const event of stream) {
  switch (event.type) {
    case "agent.message":
      for (const block of event.content) if (block.type === "text") log.push(block.text);
      break;
    case "agent.custom_tool_use": {
      const result = fixture.answer ? fixture.answer(event.name, event.input) : "Not available in this test.";
      log.push(`>> ${event.name} ${JSON.stringify(event.input)}`);
      await client.beta.sessions.events.send(session.id, {
        events: [{ type: "user.custom_tool_result", custom_tool_use_id: event.id, content: [{ type: "text", text: result }] }],
      });
      break;
    }
    case "agent.tool_use":
    case "agent.mcp_tool_use":
      if (event.evaluated_permission === "ask") {
        log.push(`>> denied paused call ${event.name}`);
        await client.beta.sessions.events.send(session.id, {
          events: [{ type: "user.tool_confirmation", tool_use_id: event.id, result: "deny", deny_message: "Unattended test: no approvals." }],
        });
      }
      break;
    case "span.outcome_evaluation_end":
      log.push(`== outcome iteration ${event.iteration}: ${event.result} - ${event.explanation}`);
      break;
    case "session.error":
      log.push(`!! session.error ${JSON.stringify(event)}`);
      break;
  }
  if (event.type === "session.status_terminated") break;
  if (event.type === "session.status_idle" && event.stop_reason.type !== "requires_action") {
    log.push(`== idle: ${event.stop_reason.type}`);
    break;
  }
}

const final = await client.beta.sessions.retrieve(session.id);
// Output files are indexed a few seconds after the session goes idle.
await new Promise((r) => setTimeout(r, 15_000));
const files = await client.beta.files.list({ scope_id: session.id, betas: ["managed-agents-2026-04-01"] });
for (const f of files.data) {
  const resp = await client.beta.files.download(f.id);
  writeFileSync(`${outDir}/${f.filename}`, Buffer.from(await resp.arrayBuffer()));
}
const cost = Number(final.usage?.list_cost?.amount ?? 0) / 100;
writeFileSync(`${outDir}/transcript.md`, log.join("\n\n"));
writeFileSync(`${outDir}/result.json`, JSON.stringify({ session: session.id, status: final.status, cost_usd: cost, outcomes: final.outcome_evaluations, files: files.data.map((f) => f.filename) }, null, 2));
console.log(`[${spec.agent}] done: ${final.status}, USD ${cost.toFixed(2)}, files: ${files.data.map((f) => f.filename).join(", ") || "none"}`);
