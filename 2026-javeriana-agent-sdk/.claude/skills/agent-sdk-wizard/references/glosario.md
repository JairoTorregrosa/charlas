# glosario.md — one line per term

For when the user asks "¿y qué es un token?" mid-wizard. Answer with the line, then go back to
the question. Do not turn the wizard into a class.

The **Se dice así** column is the plain-Spanish phrasing to use out loud; the code column is the
exact name they will see in the generated file.

| Term | One line | Se dice así | TypeScript | Python |
|---|---|---|---|---|
| **agente** | A model that uses tools inside a loop. Agent = harness + LLM | "un modelo que usa herramientas en un ciclo" | — | — |
| **harness** | The code around the model: feeds it information, runs what it asks for, decides when to stop | "el arnés: tu programa alrededor del modelo" | — | — |
| **agent loop** | Repeat "model decides → tools run → results go back" until it answers without asking for anything | "el ciclo" | — | — |
| **turno** | One full lap of the loop: the model asked for tools and those tools ran | "una vuelta del ciclo" | `maxTurns` | `max_turns` |
| **token** | The chunk of text the model counts to bill you and to fill its working memory (~4 characters) | "el pedacito de texto que se cobra" | — | — |
| **contexto** | Everything the model has in front of it right now. If it is not there, for the model it does not exist. It has a maximum size | "lo que el agente tiene delante" | — | — |
| **system prompt** | The fixed text that goes before everything and defines who the agent is; the user never sees it | "las reglas fijas del agente" | `systemPrompt` | `system_prompt` |
| **preset** | A ready-made configuration you take as-is. There is exactly one: `claude_code` | "la configuración de fábrica" | `{type:'preset',preset:'claude_code'}` | same, as a dict |
| **tool / herramienta** | A function the model can ask for by name. The model does not run it — your program does | "una función que el modelo puede pedir" | `allowedTools` | `allowed_tools` |
| **tool call** | The block where the model says "I want this tool with these arguments" | "el modelo pidió una herramienta" | `block.type === 'tool_use'` | `ToolUseBlock` |
| **schema** | The shape a piece of data must have: which fields, of which type | "la forma que debe tener el dato" | `inputSchema` (Zod) | `input_schema` (dict) |
| **MCP** | Open standard for plugging tools and data into an agent | "el estándar para conectarle herramientas" | — | — |
| **MCP in-process** | An MCP server running inside your own program — no subprocess, no network | "tus funciones, en tu mismo programa" | `createSdkMcpServer()` | `create_sdk_mcp_server()` |
| **stream** | Messages arrive bit by bit while the agent works, not all at the end | "el chorro de mensajes" | `for await (…)` | `async for …` |
| **mensaje** | One SDK event: an object with a `type` field saying what it is | "un evento del agente" | `SDKMessage` | `Message` |
| **`result`** | The message that closes the loop: cost, token usage, final text. **Not always the last one in the stream** | "el recibo" | `SDKResultMessage` | `ResultMessage` |
| **`subtype`** | How it ended: `success`, `error_max_turns`, `error_max_budget_usd`, `error_during_execution`, `error_max_structured_output_retries` | "cómo terminó" | `subtype` | `subtype` |
| **permiso** | The decision of whether an agent action runs or not | "¿corre o no corre?" | `PermissionResult` | `PermissionResultAllow` / `Deny` |
| **permission mode** | The session-wide policy for when no rule matched | "la política general" | `permissionMode` | `permission_mode` |
| **regla (rule)** | Text describing which calls match: `Bash(git commit *)`. Goes in allow / deny / ask lists | "una regla con alcance" | `disallowedTools` | `disallowed_tools` |
| **callback** | A function of yours that another program calls when something happens | "tu función, llamada por el SDK" | `canUseTool` | `can_use_tool` |
| **hook** | A callback registered at an exact moment of the loop. Can block, modify or just watch. Its `deny` beats everything | "un vigilante en un punto del ciclo" | `options.hooks` (33 events) | `hooks=…` (10 events) |
| **matcher** | The pattern that filters which tools fire your hook | "para cuáles herramientas" | `matcher` | `HookMatcher(matcher=…)` |
| **skill** | A folder with a `SKILL.md`: instructions for one task, loaded into context only when used | "un procedimiento que solo pesa cuando se usa" | `skills` | `skills` |
| **revelación progresiva** | Cheap index always loaded, expensive detail only on demand. That is why a skill costs almost nothing until it is used | "índice barato, detalle caro" | — | — |
| **frontmatter** | The `---` YAML block at the top of a `SKILL.md` with its metadata | "los metadatos de arriba" | — | — |
| **subagente** | Another instance of the agent, with a blank context, that does a subtask and returns **only its final summary** | "un ayudante con contexto en blanco" | tool `Agent` | same |
| **`parent_tool_use_id`** | The marker that says "this message came from inside a subagent". It is what builds the tree in a UI | "de qué ayudante salió" | `parent_tool_use_id` | same |
| **sesión** | The full conversation history, stored on disk as JSONL | "el historial" | `session_id` | `session_id` |
| **`cwd`** | The folder the agent sees and writes files in | "la carpeta de trabajo" | `cwd` | `cwd` |
| **setting source** | Which folders the SDK reads configuration from: `user`, `project`, `local`. Empty list = isolation | "de dónde lee su configuración" | `settingSources` | `setting_sources` |
| **`CLAUDE.md`** | Markdown file with the project's rules; loaded whole at the start of every session | "las reglas del proyecto" | (a file) | (a file) |
| **compaction** | When the context fills up, the SDK replaces old turns with a summary | "cuando se llena, resume lo viejo" | `compact_boundary` | same |
| **presupuesto** | A cap in estimated dollars; the query ends with an error when it is hit | "el tope de gasto" | `maxBudgetUsd` | `max_budget_usd` |
| **effort** | How much reasoning the model spends per response: `low`…`max`. Independent of extended thinking | "cuánto piensa antes de responder" | `effort` | `effort` |
| **sandbox** | An OS cage limiting which files and which network a command can touch. Not Claude deciding — the kernel | "una jaula del sistema operativo" | `sandbox` | `sandbox` |
| **prompt injection** | Hidden instructions inside content the agent reads (a README, a web page) that make it behave differently | "instrucciones escondidas en lo que lee" | — | — |
| **headless** | Running the agent with no interactive interface: `claude -p`, or the SDK | "sin interfaz, desde tu programa" | — | — |

## Three sentences that clear up most of the confusion

1. **`allowed_tools` approves; it does not restrict.** Tools that are not on the list are still
   available and fall through to the permission mode. To actually remove one, use a bare name in
   `disallowed_tools`, or `tools=[…]`.
2. **`query()` opens a brand-new session every time.** It remembers nothing from the previous
   call unless you pass `resume` or `continue_conversation`.
3. **A hook runs before everything else** — before deny rules, before the permission mode. That
   is why it is the only thing that holds even under `bypassPermissions`.
