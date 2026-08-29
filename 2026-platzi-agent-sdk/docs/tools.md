# Herramientas: las que trae el SDK

Sin escribir una línea, el agente ya tiene manos. Cada una tiene un `input` con campos fijos; el que resume la acción es el que imprimes en un log o revisas en un hook.

## Las que se usan en el taller

| Tool | Campo que resume | Otros campos | Qué hace | Pide permiso |
|---|---|---|---|---|
| `Bash` | `command` | `description`, `timeout`, `run_in_background` | Corre un comando en el cwd | Sí, salvo `allowed_tools` |
| `Read` | `file_path` | `offset`, `limit` | Lee un archivo (ruta absoluta) | No, dentro del cwd |
| `Write` | `file_path` | `content` | Crea o reemplaza un archivo | Sí |
| `Edit` | `file_path` | `old_string`, `new_string`, `replace_all` | Reemplaza texto exacto | Sí |
| `Glob` | `pattern` | `path` | Busca archivos por nombre | No |
| `Grep` | `pattern` | `path`, `glob`, `output_mode` | Busca texto dentro de archivos | No |
| `WebSearch` | `query` | `allowed_domains`, `blocked_domains` | Busca en internet desde el servidor de Anthropic (solo con Claude) | No |
| `WebFetch` | `url` | `prompt` | Lee una página y responde sobre ella | No |
| `Skill` | `skill` | `args` | Carga un skill completo al contexto | Con `skills` fijado, se aprueba solo |
| `Agent` | `description` | `prompt`, `subagent_type`, `run_in_background` | Lanza un sub-agente | Sí, salvo `allowed_tools` |
| `ToolSearch` | `query` | `max_results` | El modelo busca tools diferidas (aparece solo) | No |

Otras que existen: `NotebookEdit` (`notebook_path`), `TodoWrite` (`todos`), `TaskCreate`/`TaskUpdate`/`TaskList`, `AskUserQuestion` (`questions`), `EnterPlanMode`/`ExitPlanMode`, `Monitor`, `CronCreate`, `ListMcpResourcesTool`/`ReadMcpResourceTool`.

## Tres listas que se confunden

- `allowed_tools`: **aprueba** sin preguntar. No quita nada.
- `disallowed_tools`: **prohíbe**. Con nombre pelado, la tool desaparece del contexto.
- `tools`: **el set base**. `[]` = el modelo no tiene manos. Lista = solo esas (acuérdate de `"Skill"` y `"Agent"`).

## Sintaxis de las reglas (vale en las tres listas y en `settings.json`)

```
Bash                       toda la tool
Bash(git clone:*)          comandos que empiezan por "git clone"
Bash(ls)                   exactamente "ls"
Read(./.env)               un archivo concreto
Write(./roast.md)          un archivo concreto
mcp__alphaxiv              todo un servidor MCP
mcp__alphaxiv__*           igual
mcp__alphaxiv__get_paper   una tool del servidor
Skill(roast-de-codigo)     un skill
```

Un nombre pelado en `allowed_tools` (`"Bash"`) hace sombra a `can_use_tool` para esa tool. Un especificador (`"Bash(ls:*)"`) no.

## Tools MCP: cómo se llaman

`mcp__<servidor>__<tool>`. El `<servidor>` es la clave del dict en `mcp_servers`, el nombre en `.mcp.json`, o el nombre que diste en `claude mcp add`. Los conectores de claude.ai se llaman `mcp__claude_ai_<Nombre>__<tool>`.

## Lo que ve el modelo cuando una tool falla

Un `UserMessage` con `ToolResultBlock(is_error=True, content="...")`. No se cae: lee el texto y decide. Por eso la razón de un `deny` es un prompt, no un log.
