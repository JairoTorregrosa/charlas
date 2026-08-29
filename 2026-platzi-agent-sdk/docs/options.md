# `ClaudeAgentOptions`: las que importan

Las ~20 opciones que se usan de verdad, con su default y su trampa. Python primero; el nombre TS va entre paréntesis cuando cambia.

## Identidad y presupuesto

| Opción | Default | Qué hace | Trampa |
|---|---|---|---|
| `model` | el de tu CLI | `"claude-sonnet-5"`, `"claude-haiku-4-5-20251001"`, `"claude-opus-5"` o alias `"sonnet"`/`"haiku"` | Fíjalo siempre: el default depende de tu login |
| `system_prompt` (`systemPrompt`) | mínimo (solo uso de tools) | `str`, o `{"type": "preset", "preset": "claude_code", "append": "..."}` | Con un `str` propio el modelo **no sabe su cwd**: díselo en el prompt |
| `max_turns` (`maxTurns`) | sin tope | Vueltas máximas del loop | Al llegar: `result` con `error_max_turns` **y** excepción |
| `max_budget_usd` (`maxBudgetUsd`) | sin tope | Corta al superar ese costo estimado | Igual: `error_max_budget_usd` + excepción. Ponlo siempre |
| `effort` | default del modelo | `"low"` · `"medium"` · `"high"` · `"xhigh"` · `"max"` | `"low"` para sub-agentes y tareas simples |

## Dónde vive y qué carga

| Opción | Default | Qué hace | Trampa |
|---|---|---|---|
| `cwd` | el del proceso | La carpeta del agente. Las tools de archivos trabajan ahí | Debe existir |
| `add_dirs` (`additionalDirectories`) | `[]` | Carpetas extra que puede leer y escribir | Sin esto, fuera del cwd pide permiso |
| `setting_sources` (`settingSources`) | **todas** (`user`, `project`, `local`) | Qué configuración de disco lee: `project` = `.claude/` del cwd (skills, agents, `.mcp.json`, `settings.json`, `CLAUDE.md`); `user` = `~/.claude/` y lo que registraste con `claude mcp add --scope user` | `[]` apaga todo. En Python, fijar `skills` cambia el default a `["user","project"]` |
| `skills` | sin filtro | `"all"` o lista de nombres exactos (`"plugin:nombre"` si es de plugin) | Filtra lo que el modelo ve; los archivos siguen en disco |
| `plugins` | `[]` | `[{"type": "local", "path": "/abs/ruta"}]` | No expande `~`. Ruta mala = silencio |
| `env` | hereda | Variables para el subproceso `claude`. En Python **se fusiona** con tu entorno; en TS **lo reemplaza** (pon `...process.env`) | `CLAUDE_CODE_DISABLE_AUTO_MEMORY="1"` para que no cargue tu memoria |

## Herramientas

| Opción | Default | Qué hace | Trampa |
|---|---|---|---|
| `allowed_tools` (`allowedTools`) | `[]` | Se aprueban **sin preguntar**. Acepta `"Bash"`, `"Bash(git clone:*)"`, `"mcp__srv__*"` | **No restringe**: solo aprueba. Un nombre pelado hace que `can_use_tool` no se llame para esa tool |
| `disallowed_tools` (`disallowedTools`) | `[]` | Prohíbe. Nombre pelado la saca del contexto | Gana incluso en `bypassPermissions` |
| `tools` | preset `claude_code` | El **set base**. `[]` = ninguna. Lista = solo esas | Si lo usas, incluye `"Skill"` y `"Agent"` a mano |
| `mcp_servers` (`mcpServers`) | `{}` | Servidores MCP por código: `{"nombre": {"type": "http", "url": ...}}` o stdio `{"command": ..., "args": [...]}` | Sus tools se llaman `mcp__nombre__tool`. El `.mcp.json` del cwd se carga aparte, vía `setting_sources` |
| `strict_mcp_config` (`strictMcpConfig`) | `False` | Ignora `.mcp.json`, settings y conectores de claude.ai: solo lo que pasaste en `mcp_servers` | Apaga también el `.mcp.json` del cwd |
| `agents` | `None` | Sub-agentes por código: `{"nombre": AgentDefinition(description=..., prompt=..., tools=[...], model="haiku")}` | En Python los campos de `AgentDefinition` van en **camelCase** (`disallowedTools`, `maxTurns`). El equivalente en disco es `.claude/agents/nombre.md` |

## Permisos y control

| Opción | Default | Qué hace | Trampa |
|---|---|---|---|
| `permission_mode` (`permissionMode`) | `"default"` | `"default"` · `"acceptEdits"` (aprueba archivos) · `"plan"` · `"dontAsk"` (lo no aprobado se niega) · `"bypassPermissions"` (todo, salvo deny) | Ver el orden de evaluación en `permisos_hooks.md` |
| `hooks` | `None` | `{"PreToolUse": [HookMatcher(matcher="Bash", hooks=[fn])]}` | El hook corre **antes** que el modo y las reglas |
| `can_use_tool` (`canUseTool`) | `None` | Tu función `(nombre, input, ctx) -> {"behavior": "allow"/"deny", ...}` cuando nada más decidió | En Python exige streaming input (prompt como generador) y un hook `PreToolUse` vacío; en TS funciona con `str` |
| `include_partial_messages` (`includePartialMessages`) | `False` | Emite `StreamEvent` (texto letra a letra) | No hagas `return` dentro del `async for` |
| `forward_subagent_text` (`forwardSubagentText`) | `False` | Reenvía el texto de los sub-agentes | Sin esto solo ves sus `tool_use` |
| `include_hook_events` (`includeHookEvents`) | `False` | Emite `hook_started` / `hook_response` | Para depurar porteros |

## Sesiones y salida

| Opción | Default | Qué hace | Trampa |
|---|---|---|---|
| `resume` | `None` | `session_id` de una conversación anterior: la sigue | El id viene en `ResultMessage.session_id` y en `init` |
| `fork_session` (`forkSession`) | `False` | Al retomar, bifurca a un id nuevo | Para "qué pasa si…" sin tocar la original |
| `continue_conversation` (`continue`) | `False` | Retoma la más reciente del cwd | Frágil en demos |
| `output_format` (`outputFormat`) | `None` | `{"type": "json_schema", "schema": {...}}` → `ResultMessage.structured_output` | Verifica `subtype == "success"` **y** que `structured_output` no sea `None` |
| `stderr` | `sys.stderr` | Callback con la salida de error del CLI | `lambda _: None` para una demo limpia; quítalo para depurar |

## El bloque que usamos en el taller

```python
ClaudeAgentOptions(
    model="claude-sonnet-5",
    system_prompt=SYSTEM_PROMPT.format(cwd=WORKSPACE),
    cwd=str(WORKSPACE),
    setting_sources=["project"],            # .claude/skills y .claude/agents de su casa
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Agent"],
    hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[solo_un_archivo])]},
    max_turns=30,
    max_budget_usd=0.60,
    env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
    stderr=lambda _: None,
)
```
