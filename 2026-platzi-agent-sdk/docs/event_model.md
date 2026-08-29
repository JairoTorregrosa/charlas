# Modelo de eventos del Agent SDK (Python)

Todo lo que `query()` te entrega, y en qué orden. Verificado con `claude-agent-sdk` 0.2.148 y Claude Code 2.1.251.

## La forma general

```
init  →  [assistant (pide tool)  →  user (tool_result)] × N  →  assistant (habla)  →  result
```

- Cada ida y vuelta con una herramienta es una **vuelta** (`num_turns` en el recibo).
- Con `include_partial_messages=True`, entre medio llegan `StreamEvent` con los pedazos de texto.
- El `init` **no siempre es el primero**: un `RateLimitEvent` puede adelantarse.

## Las 7 clases (`claude_agent_sdk.types.Message`)

| Clase | Cuándo | Campos que importan |
|---|---|---|
| `SystemMessage` | Arranque y avisos del harness | `subtype`, `data` (dict crudo) |
| `AssistantMessage` | El modelo habla o pide una herramienta | `content` (bloques), `model`, `parent_tool_use_id`, `stop_reason`, `usage` |
| `UserMessage` | Vuelve el resultado de una herramienta (o tu mensaje, en streaming input) | `content` (str o bloques), `parent_tool_use_id`, `tool_use_result` |
| `ResultMessage` | Último. Uno por `query()` | `subtype`, `num_turns`, `total_cost_usd`, `duration_ms`, `usage`, `model_usage`, `result`, `structured_output`, `session_id`, `is_error` |
| `StreamEvent` | Solo con `include_partial_messages=True` | `event` (dict crudo de la API), `parent_tool_use_id` (siempre `None`) |
| `RateLimitEvent` | Aviso de cuota | `rate_limit_info` |
| `ConversationResetMessage` | Tras `/clear` | ninguno |

En TypeScript son 39 tipos distintos; en Python todo lo que no es una de estas 7 cae en `SystemMessage` con un `subtype`.

## `SystemMessage` con `subtype="init"`

Llega una vez. `data` trae lo que cargó el agente:

- `model`, `cwd`, `session_id`, `permissionMode`, `claude_code_version`, `apiKeySource` (`"none"` = sesión de Claude Code)
- `tools`: lista de nombres (built-in + `mcp__servidor__tool`)
- `skills`: nombres de skills descubiertos (`plugin:nombre` si vienen de plugin)
- `agents`: sub-agentes disponibles
- `mcp_servers`: `[{name, status}]` con `status` = `connected` · `pending` · `needs-auth` · `failed`
- `slash_commands`, `plugins`, `output_style`

Regla: verifica aquí lo que crees que cargaste. Un plugin con ruta mala o un MCP sin auth **no fallan**: simplemente no aparecen o salen `needs-auth`.

## Bloques dentro de `AssistantMessage.content`

| Bloque | Campos | Qué es |
|---|---|---|
| `TextBlock` | `text` | El modelo habla |
| `ToolUseBlock` | `id`, `name`, `input` (dict) | El modelo pide una herramienta. `id` es el hilo que une la petición con su resultado |
| `ThinkingBlock` | `thinking`, `signature` | Razonamiento (si el modelo lo expone) |

El campo que resume cada `input`: `command` (Bash) · `file_path` (Read, Write, Edit) · `pattern` (Glob, Grep) · `query` (WebSearch) · `url` (WebFetch) · `skill` (Skill) · `description` + `subagent_type` (Agent). Tabla completa en `tools.md`.

## Bloques dentro de `UserMessage.content`

| Bloque | Campos | Qué es |
|---|---|---|
| `ToolResultBlock` | `tool_use_id`, `content` (str o lista), `is_error` | La herramienta respondió. `tool_use_id` = el `id` del `ToolUseBlock` que la pidió |
| `TextBlock` | `text` | Tu mensaje, en streaming input |

`is_error=True` no rompe nada: el modelo lee el error y decide qué hacer. Un `deny` de un hook llega por aquí, con el motivo como texto.

## `ResultMessage.subtype`

| subtype | Qué pasó | Después |
|---|---|---|
| `success` | Terminó bien | `result` trae el texto final; `structured_output` el JSON si pediste `output_format` |
| `error_max_turns` | Se acabaron las vueltas (`max_turns`) | `query()` **lanza excepción** después de entregar este mensaje |
| `error_max_budget_usd` | Se alcanzó el tope (`max_budget_usd`) | Igual: lanza excepción |
| `error_during_execution` | El proceso se cayó | Costos pueden venir en cero; lanza excepción |
| `error_max_structured_output_retries` | No logró un JSON válido | Lanza excepción |

Regla: `success` **y** `structured_output` presente = éxito real con salida estructurada. Solo `success` no basta.

## `StreamEvent.event["type"]` (el orden dentro de un mensaje del modelo)

```
message_start
content_block_start        (text | tool_use)
content_block_delta  × N   delta.type = "text_delta" (texto) | "input_json_delta" (los args de la tool)
content_block_stop
message_delta              stop_reason + usage
message_stop
```

Para pintar texto letra por letra: `event["delta"]["type"] == "text_delta"` → `event["delta"]["text"]`.

## Sub-agentes: quién habla

- El padre pide `Agent` con `input = {description, prompt, subagent_type}`. El `id` de ese `ToolUseBlock` es el hilo.
- Todo mensaje que venga de adentro trae `parent_tool_use_id = ese id`.
- Por defecto solo llegan los `tool_use` / `tool_result` del hijo. Para ver su texto: `forward_subagent_text=True`.
- El `UserMessage` con `tool_result.tool_use_id == ese id` cierra el hilo: es la respuesta final del hijo.
- `StreamEvent` nunca viene de un hijo.

## Los otros `SystemMessage.subtype`

| subtype | Cuándo | Campos en `data` |
|---|---|---|
| `compact_boundary` | El contexto se comprimió | `compact_metadata: {trigger, pre_tokens, post_tokens}` |
| `status` | Cambio de estado | `status: "compacting" \| "requesting" \| None` |
| `permission_denied` | Un portero dijo no | `tool_name`, `tool_use_id`, `decision_reason`, `message` |
| `hook_started` / `hook_progress` / `hook_response` | Tus hooks corriendo (solo con `include_hook_events=True`) | `hook_name`, `hook_event`, `outcome`, `output` |
| `task_started` / `task_progress` / `task_updated` / `task_notification` | Sub-agentes o tareas en segundo plano | `task_id`, `status`, `summary`, `subagent_type` |
| `background_tasks_changed` | Cambió la lista de tareas de fondo | `tasks[]` |
| `session_state_changed` | `idle` · `running` · `requires_action` | `state` |
| `commands_changed` | Se descubrieron skills o comandos nuevos | `commands[]` |
| `api_retry` | Reintento contra la API | `attempt`, `max_attempts`, `backoff_ms` |
| `model_refusal_fallback` / `model_refusal_no_fallback` | El modelo rehusó y hubo (o no) fallback | `direction` |
| `auth_status`, `informational`, `thinking_tokens`, `memory_recall`, `files_persisted`, `tool_use_summary`, `mirror_error`, `plugin_install`, `worker_shutting_down`, `local_command_output` | Diagnóstico | varios |

## Cómo leerlo en una celda (patrón mínimo)

```python
async for m in query(prompt=..., options=...):
    if isinstance(m, SystemMessage) and m.subtype == "init":
        ...                              # qué cargó
    elif isinstance(m, AssistantMessage):
        for b in m.content:              # TextBlock | ToolUseBlock
            ...
    elif isinstance(m, UserMessage) and isinstance(m.content, list):
        for b in m.content:              # ToolResultBlock
            ...
    elif isinstance(m, ResultMessage):
        recibo = m                       # no hagas return aquí: deja que el loop termine
```

Dos trampas: no salgas del `async for` con `return`/`break` cuando hay `include_partial_messages=True` (el generador se queja al cerrar); y atrapa la excepción que `query()` lanza tras un `result` de error si quieres seguir vivo.
