# opciones-sdk.md — answer → exact SDK code

Every line here is verified against **TypeScript SDK 0.3.251**, **Python SDK 0.2.148**
(which bundles **Claude Code 2.1.251**). Do not write an API name that is not on this page.

Two naming traps that bite constantly:

- `ClaudeAgentOptions` uses **snake_case** (`allowed_tools`, `permission_mode`, `max_turns`).
- `AgentDefinition` and **hook return values** use **camelCase even in Python**
  (`disallowedTools`, `maxTurns`, `permissionDecision`). `AgentDefinition` is a dataclass, so
  `max_turns=3` raises `TypeError`. Hook outputs are `TypedDict`s, so a snake_case key is
  **silently ignored** — the hook just does nothing. That one is worse.

---

## Step 1 · Lenguaje

### Python

```bash
uv init && uv add claude-agent-sdk     # requires Python >= 3.10
# credencial: .env + credenciales.py/.ts (references/auth.md), no un export
uv run agente.py
```

```python
from claude_agent_sdk import query, ClaudeAgentOptions
# query is keyword-only: query(prompt=..., options=...). query("hola") is a TypeError.
async for mensaje in query(prompt="…", options=opciones):
    ...
```

### TypeScript

```bash
npm init -y && npm pkg set type=module      # requires Node >= 18
npm install @anthropic-ai/claude-agent-sdk
npm install zod@^4                          # peer dep of the SDK — v4, NOT v3
npm install --save-dev tsx @types/node
# credencial: .env + credenciales.py/.ts (references/auth.md), no un export
npx tsx agente.ts
```

```typescript
import { query, type Options } from "@anthropic-ai/claude-agent-sdk";
// one object, two keys
for await (const mensaje of query({ prompt: "…", options: opciones })) { }
```

### Style: one-shot vs live session

Decided by step 2, not asked.

| Goal | Python | TypeScript |
|---|---|---|
| One question, one answer (2A, 2B, 2C) | `query(prompt="…", options=…)` | `query({ prompt: "…", options })` |
| Several turns with memory (2D) | `async with ClaudeSDKClient(options=…) as c:` then `await c.query(p)` / `async for m in c.receive_response()` | keep the `Query` object; feed it with `q.streamInput(stream)` |

`ClaudeSDKClient` is also what `can_use_tool` needs in Python — see step 8.

---

## Step 2 · Objetivo

No option of its own; it sets `cwd`, the test prompt and the defaults. See
`arquetipos.md`.

```python
cwd="./workspace"          # Python
```
```typescript
cwd: "./workspace",        // TypeScript
```

---

## Step 3 · Modelo

| Option | Value | Price in/out per MTok |
|---|---|---|
| Sonnet 5.5 *(rec.)* | `"claude-sonnet-5-5"` | $2 / $10 |
| Haiku 5.5 | `"claude-haiku-5-5"` | $0.10 / $0.50 (prompts up to 100K tokens; $0.50 / $2.50 above) |
| Opus 5.5 | `"claude-opus-5-5"` | $4 / $20 |
| Fable 5.1 | `"claude-fable-5-1"` | $10 / $50 |

Prices and IDs verified 2026-11-02 against the claude-api skill's model table (cached 2026-10-06)
and its Sonnet 5.5 and Haiku 5.5 migration guides. Sonnet 5.5 replaced Sonnet 5 and Haiku 5.5
replaced Haiku 4.5; both older IDs are still served, so offer them only when the person names them.
Opus 5.5 and Haiku 5.5 default to `effort="medium"` when effort is omitted; Sonnet 5.5 and Fable
5.1 default to `"high"`. The sub-question always sets it explicitly.

```python
model="claude-sonnet-5-5",
effort="high",             # only if the sub-question ran; "low"|"medium"|"high"|"xhigh"|"max"
```
```typescript
model: "claude-sonnet-5-5",
effort: "high",
```

Always pin the model. Without it you inherit whatever the CLI defaults to, which depends on the
user's authentication and subscription.

---

## Step 4 · Instrucción

| Option | Python | TypeScript |
|---|---|---|
| 4A Mínimo + mis reglas *(rec.)* | `system_prompt="<reglas>"` | `systemPrompt: "<reglas>"` |
| 4B Preset + mis reglas | `system_prompt={"type": "preset", "preset": "claude_code", "append": "<reglas>"}` | `systemPrompt: { type: "preset", preset: "claude_code", append: "<reglas>" }` |
| 4C Solo el preset | `system_prompt={"type": "preset", "preset": "claude_code"}` | `systemPrompt: { type: "preset", preset: "claude_code" }` |
| 4D Mío desde cero | `system_prompt="<texto completo>"` | `systemPrompt: "<texto completo>"` |

Omitting `system_prompt` gives a **minimal** prompt, **not** the Claude Code one — that is what
the `preset` object is for. A plain string **replaces** everything.

Python-only: `system_prompt={"type": "file", "path": "prompt.md"}` loads it from a file (useful
when the prompt is long enough to bump into the argv size limit).

---

## Step 5 · Herramientas

| Option | `allowed_tools` / `allowedTools` |
|---|---|
| 5A Solo leer *(rec.)* | `["Read", "Glob", "Grep"]` |
| 5B Leer y escribir | `["Read", "Glob", "Grep", "Edit", "Write"]` |
| 5C Todo + terminal | `["Read", "Glob", "Grep", "Edit", "Write", "Bash"]` |
| 5D Mis funciones | `["mcp__<servidor>__<tool>"]` (or `["mcp__<servidor>__*"]`) |

`allowed_tools` **auto-approves; it does not restrict.** Tools not on the list stay available
and fall through to the permission mode. To actually remove a tool, use `disallowed_tools` with
a bare name (`"Bash"` takes it out of the context entirely) or set `tools=[…]`.

### 5D · Own functions — Python

```python
from typing import Any
from claude_agent_sdk import tool, create_sdk_mcp_server

# name, description, input_schema. Every key of a dict-schema is REQUIRED.
# Use Annotated[str, "…"] to give a field a description Claude can read.
@tool(
    "buscar_cliente",
    "Busca un cliente por su identificador y devuelve nombre, ciudad y saldo.",
    {"cliente_id": str},
)
async def buscar_cliente(args: dict[str, Any]) -> dict[str, Any]:
    # TODO: replace with the real lookup
    return {"content": [{"type": "text", "text": f"cliente {args['cliente_id']}: …"}]}

mi_servidor = create_sdk_mcp_server(
    name="mi_servidor", version="1.0.0", tools=[buscar_cliente]
)

opciones = ClaudeAgentOptions(
    # The DICT KEY is what builds the tool name: mcp__mi_servidor__buscar_cliente
    mcp_servers={"mi_servidor": mi_servidor},
    allowed_tools=["mcp__mi_servidor__buscar_cliente"],
)
```

### 5D · Own functions — TypeScript

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// zod v4 — the SDK 0.3.251 declares zod@^4.0.0 as its peer dependency.
// Installing zod@^3 makes `npm install` fail with ERESOLVE.
const buscarCliente = tool(
  "buscar_cliente",
  "Busca un cliente por su identificador y devuelve nombre, ciudad y saldo.",
  { cliente_id: z.string().describe("Identificador del cliente, p. ej. C-4471") },
  async (args) => {
    // TODO: replace with the real lookup
    return { content: [{ type: "text", text: `cliente ${args.cliente_id}: …` }] };
  },
);

const miServidor = createSdkMcpServer({
  name: "mi_servidor", version: "1.0.0", tools: [buscarCliente],
});

const opciones: Options = {
  mcpServers: { mi_servidor: miServidor },
  allowedTools: ["mcp__mi_servidor__buscar_cliente"],
};
```

Handler return shape (`CallToolResult`): `content` is required and is what Claude reads.
`is_error` (Python) / `isError` (TS) marks the call as failed so Claude reacts.

Rules that make a tool actually get used well (from the tool-writing guide):

- Name the resource and the action: `buscar_pedidos`, not `buscar`.
- Name parameters for what they are: `cliente_id`, not `cliente`.
- Return signal, not dumps. Resolve UUIDs to names — it measurably reduces hallucination.
- Cap the result size by default, and say inside the result that you truncated.
- Error messages are prompt: say what to do differently, not just what broke.

### 5-bis · External MCP server

```python
mcp_servers={
    "mi_servidor": mi_servidor,                                    # in-process
    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
    # or by URL:  {"type": "http", "url": "https://…", "headers": {"Authorization": "Bearer …"}}
},
allowed_tools=["mcp__mi_servidor__buscar_cliente", "mcp__github__*"],
strict_mcp_config=True,   # ignore .mcp.json, user settings, plugins and claude.ai connectors
```

Transports: `stdio` (a command), `http`, `sse`, `sdk` (in-process). The programmatic
`mcp_servers` option accepts `"http"` — **not** `"streamable-http"`, which only works in
`.mcp.json` files.

---

## Step 6 · Skills

```python
setting_sources=["project"],   # without this the skill is never discovered
skills=["resumen-csv"],        # only this one enabled; "all" = every discovered skill
allowed_tools=["Read", "Bash"],
```
```typescript
settingSources: ["project"],
skills: ["resumen-csv"],
allowedTools: ["Read", "Bash"],
```

`cwd` must be at or above the directory holding `.claude/skills/`. Setting `skills` makes the
SDK add the `Skill` tool to `allowedTools` — but if you also pass an explicit `tools` list, put
`"Skill"` in it by hand.

A generated `SKILL.md` (see `templates/skill.md.tmpl`) needs only `name` and `description`.
`${CLAUDE_SKILL_DIR}` expands to the skill's own folder, which is how the body can point at its
own scripts regardless of where the agent's working directory is.

**Say this out loud to the user:** in the SDK, a skill's `allowed-tools` frontmatter
pre-approves tools for that turn — it does **not** restrict anything. Tools it does not list
stay available.

---

## Step 7 · Subagentes

```python
from claude_agent_sdk import AgentDefinition

agents={
    "revisor": AgentDefinition(
        description="Revisa un análisis buscando errores de cálculo. Úsalo tras cada informe.",
        prompt="Eres un revisor. Solo lees. Responde en máximo 5 viñetas: qué está mal y dónde.",
        tools=["Read", "Grep", "Glob"],   # allowlist: what is not here does not exist for it
        model="haiku",                    # 'fable'|'opus'|'sonnet'|'haiku'|'inherit'|full id
    ),
},
allowed_tools=["Read", "Glob", "Grep", "Agent"],   # "Agent" auto-approves launching subagents
```
```typescript
agents: {
  revisor: {
    description: "Revisa un análisis buscando errores de cálculo. Úsalo tras cada informe.",
    prompt: "Eres un revisor. Solo lees. Responde en máximo 5 viñetas: qué está mal y dónde.",
    tools: ["Read", "Grep", "Glob"],
    model: "haiku",
  },
},
allowedTools: ["Read", "Glob", "Grep", "Agent"],
```

`AgentDefinition` fields that exist in **both** SDKs: `description`, `prompt`, `tools`,
`disallowedTools`, `model`, `skills`, `memory`, `mcpServers`, `initialPrompt`, `maxTurns`,
`background`, `effort`, `permissionMode`. **All camelCase, in Python too.**

Without `"Agent"` in `allowed_tools`, launching a subagent falls through to the permission
callback, or is denied.

Telling parent messages from subagent messages in the stream:

```python
padre = getattr(mensaje, "parent_tool_use_id", None)
prefijo = "   ↳ " if padre else ""     # indented = it came from inside a subagent
```
```typescript
const prefijo = "parent_tool_use_id" in mensaje && mensaje.parent_tool_use_id ? "   ↳ " : "";
```

Set `forward_subagent_text=True` / `forwardSubagentText: true` to see the subagent's *text*, not
only its tool calls.

Cost: `usage` counts the main loop only; `model_usage` / `modelUsage` counts the whole tree,
subagents included. `max_budget_usd` does count subagent spend.

---

## Step 8 · Permisos

Evaluation order, in this exact sequence:
**hooks → deny rules → ask rules → permission mode → allow rules → `can_use_tool`.**
Deny rules win even under `bypassPermissions`.

| Option | Python | TypeScript |
|---|---|---|
| 8A Solo lo que listé *(rec.)* | `permission_mode="default"` + `allowed_tools=[…]` | same, camelCase |
| 8B Edita sin preguntar | `permission_mode="acceptEdits"` | `permissionMode: "acceptEdits"` |
| 8C Humano en el loop | `can_use_tool=<callback>` + the streaming trick below | `canUseTool: async (name, input, ctx) => …` |
| 8D Sin frenos | `permission_mode="bypassPermissions"` | `permissionMode: "bypassPermissions"` **and** `allowDangerouslySkipPermissions: true` |

All six modes: `default`, `acceptEdits`, `plan`, `dontAsk`, `auto`, `bypassPermissions`.
`bypassPermissions` cannot run as root on Unix.

Scoped deny rules are the real fence, and they hold in every mode:

```python
disallowed_tools=["Bash(rm *)", "Edit(//secrets/**)"],
# a bare name ("Bash") removes the tool from the context;
# a scoped rule leaves it visible and denies only what matches.
# A LEADING DOUBLE SLASH means an absolute path; a single slash anchors at cwd.
```

### 8C · Human in the loop — Python

Python's `can_use_tool` **requires streaming input**. With a plain string prompt the SDK closes
the input stream before it can ever call the callback. The documented workaround is an empty
`PreToolUse` hook that keeps it open:

```python
from claude_agent_sdk import (
    ClaudeAgentOptions, HookMatcher, PermissionResultAllow, PermissionResultDeny,
    ToolPermissionContext, query,
)

SEGURAS = {"Read", "Glob", "Grep"}

async def can_use_tool(tool_name: str, input_data: dict, context: ToolPermissionContext):
    if tool_name in SEGURAS:
        return PermissionResultAllow(updated_input=input_data)
    print(f"\n[{tool_name}] {input_data}")
    if input("  ¿Permitir? (s/n): ").strip().lower() == "s":
        return PermissionResultAllow(updated_input=input_data)
    return PermissionResultDeny(
        message="No autorizado. Propón una alternativa sin escribir en disco."
    )

async def hook_dummy(input_data, tool_use_id, context):
    return {"continue_": True}      # keeps the input stream open. That is its whole job.

async def prompt_stream():
    yield {"type": "user", "message": {"role": "user", "content": "…"}}

opciones = ClaudeAgentOptions(
    can_use_tool=can_use_tool,
    hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[hook_dummy])]},
    permission_mode="default",
)
async for m in query(prompt=prompt_stream(), options=opciones):
    ...
```

### 8C · Human in the loop — TypeScript

No workaround needed:

```typescript
import * as readline from "node:readline/promises";
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

const opciones: Options = {
  permissionMode: "default",
  canUseTool: async (toolName, input, { suggestions = [] }) => {
    if (["Read", "Glob", "Grep"].includes(toolName))
      return { behavior: "allow", updatedInput: input };
    console.log(`\n[${toolName}]`, JSON.stringify(input, null, 2));
    const r = await rl.question("  ¿Permitir? (s/n): ");
    if (r.trim().toLowerCase() === "s")
      return { behavior: "allow", updatedInput: input, updatedPermissions: suggestions };
    return { behavior: "deny", message: "No autorizado. Propón otra vía." };
  },
};
// remember rl.close() at the end
```

**Rule when step 8 is 8C: `allowed_tools` goes empty.** A tool listed there by bare name is
auto-approved *before* the callback runs, so the callback never sees it — the whole point of the
step disappears. Let `can_use_tool` be the only gate, and keep the step-5 answer as the
allowlist *inside* the callback (the `SEGURAS` set above). Both SDKs warn about this
(`CLAUDE_SDK_CAN_USE_TOOL_SHADOWED` / `CanUseToolShadowedWarning`). Use scoped rules, or move
the logic to a `PreToolUse` hook, which runs before everything.

---

## Step 9 · Hooks

Python has **10** hook events; TypeScript has **33**. All three options below use events that
exist in both: `PreToolUse`, `PostToolUse`, `Stop`.

```python
from claude_agent_sdk import HookMatcher
hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[bloquear])]},
```
```typescript
hooks: { PreToolUse: [{ matcher: "Bash", hooks: [bloquear] }] },
```

Ready-made functions: `templates/hooks.py` and `templates/hooks.ts`.

| Option | Event | Matcher | Returns |
|---|---|---|---|
| 9B Bloquear peligrosos | `PreToolUse` | `"Bash"` | `hookSpecificOutput.permissionDecision = "deny"` + `permissionDecisionReason` |
| 9C Registro de todo | `PostToolUse` | none (all tools) | `{"async_": True, "asyncTimeout": 5000}` — side effect only, does not block |
| 9D Verificar al final | `Stop` | **none — `Stop` ignores matchers** | `{"decision": "block", "reason": "…"}` |

Four things that will burn you:

1. **Hook output keys are camelCase in Python too** (`hookSpecificOutput`, `permissionDecision`,
   `permissionDecisionReason`, `continue_` being the one exception). They are `TypedDict`s: a
   snake_case key does not raise — it is silently ignored and the hook does nothing.
2. **`permissionDecisionReason` is read by the model**; `systemMessage` is read by the human.
   Write the reason as an actionable instruction ("mueve a ./papelera/ en su lugar") and the
   model will take the alternative instead of retrying the same thing.
3. **A `Stop` hook needs the `stop_hook_active` guard.** Without it, an agent that cannot satisfy
   the check loops forever.
4. **Matchers**: plain names are exact (`Bash`, `Edit|Write`). Anything with another character is
   an unanchored JavaScript regex — `Edit.*` also matches `NotebookEdit`, and `mcp__memory`
   matches nothing at all (you want `mcp__memory__.*`).

Returning `{}` means "no opinion, carry on".

---

## Loop limits — always present, never asked

```python
max_turns=25,
max_budget_usd=0.15,
```
```typescript
maxTurns: 25,
maxBudgetUsd: 0.15,
```

`ResultMessage.subtype` tells you how it ended: `success`, `error_max_turns`,
`error_max_budget_usd`, `error_during_execution`, `error_max_structured_output_retries`. Only
`success` carries `result`. All of them carry `total_cost_usd`, `usage`, `num_turns` and
`session_id` — in Python the first three are typed optional, so check for `None` before
formatting them.

`total_cost_usd` is a **client-side estimate**, not billing truth.

## Isolation — when the agent should not read the user's config

```python
setting_sources=[],        # no CLAUDE.md, no ~/.claude, no project skills or agents
strict_mcp_config=True,    # only the MCP servers passed here
```

Omitting `setting_sources` loads `user` + `project` + `local`. That is why an agent sometimes
reads a `CLAUDE.md` nobody put there on purpose. Step 6 needs `["project"]`; everything else in
this wizard is happier with `[]`.
