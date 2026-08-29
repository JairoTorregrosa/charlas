# Errores que vas a ver (y el arreglo)

Ordenado por lo que pasa en una sala con cien laptops.

## Antes de arrancar

| Síntoma | Causa | Arreglo |
|---|---|---|
| `CLINotFoundError: Claude Code not found` | El SDK lanza `claude` como subproceso y no lo encontró | Instala Claude Code; si pusiste `cli_path`, confirma la ruta |
| `Invalid API key` | Hay una `ANTHROPIC_API_KEY` mala en el entorno | `env \| grep ANTHROPIC`. Quítala para usar tu sesión de Claude Code (`claude` → `/login`) |
| `Credit balance is too low` | Una `ANTHROPIC_API_KEY` desvía las peticiones fuera de tu suscripción | Igual: quita la variable |
| `You've hit your session limit` / `weekly limit` | Cuota del plan agotada | Esperar al reset. Cambiar de modelo no ayuda (el límite es compartido) |
| `Import "claude_agent_sdk" could not be resolved` (editor) | El editor no usa el `.venv` del proyecto | Selecciona el intérprete `.venv/bin/python` |
| `uv run jupyter` → `Failed to spawn` | Renombraste la carpeta y el venv quedó con rutas viejas | `rm -rf .venv && uv sync` |
| `asyncio.run() cannot be called from a running event loop` | Estás en un notebook | Usa `await` directo en la celda |

## Durante la corrida

| Síntoma | Causa | Arreglo |
|---|---|---|
| `ResultError: Reached maximum budget ($0.40)` | Se alcanzó `max_budget_usd`. Es intencional | Atrapa la excepción si quieres seguir; sube el tope si no |
| `ResultError: ... max turns` | Se alcanzó `max_turns` | Igual. Revisa qué estaba haciendo el agente: suele ser un loop de exploración |
| `RuntimeError: aclose(): asynchronous generator is already running` | Saliste del `async for` con `return`/`break` con `include_partial_messages=True` | Guarda el `ResultMessage` en una variable y deja que el loop termine |
| `ProcessError: Command failed with exit code 1` | El CLI salió sin reportar un `result` | Quita `stderr=lambda _: None` para ver el error real |
| `CanUseToolShadowedWarning: can_use_tool will not be invoked for: Read` | Nombre pelado en `allowed_tools` | Es un aviso, no un error. Quítalo de la lista si quieres que pregunte |
| El agente hace `find /` por todo el disco | Con `system_prompt` propio no sabe su cwd | Pon la carpeta en el prompt: "Trabajas en {cwd}" |
| El agente escribe fuera de la carpeta | Igual, y sin portero | Cwd en el prompt + hook `PreToolUse` sobre `Write\|Edit` |
| `[usa] Read:` sale vacío en tu log | Imprimiste `input["command"]`; Read usa `file_path` | Ver `tools.md`: cada tool tiene su campo |
| Un MCP sale `needs-auth` en el `init` | Servidor http con OAuth; el SDK no abre navegador | Token en `headers`, o `claude mcp add` + `/mcp` → Authenticate, y `setting_sources` con `"user"` |
| Un MCP sale `pending` en el `init` | Todavía se está conectando (2 s de espera por defecto) | No es error. Sus tools aparecen cuando conecta |
| El skill no aparece en `init.skills` | `setting_sources` sin `"project"`, o el `SKILL.md` no está en `.claude/skills/<dir>/` | Ajusta y verifica en el `init` |
| El plugin no aparece en `init.plugins` | Ruta mala o con `~` | Ruta absoluta. El SDK no avisa |
| `AgentDefinition(max_turns=3)` → `TypeError` | En Python los campos van en camelCase | `maxTurns=3` |
| El sub-agente no muestra texto | Por defecto solo llegan sus `tool_use` | `forward_subagent_text=True` |
| `subtype == "success"` pero `structured_output` es `None` | El JSON no validó contra el esquema | Trátalo como falla. Simplifica el esquema |
| El costo del recibo no cuadra con la consola | `total_cost_usd` es estimado del cliente | Es para comparar corridas, no para facturar |
| El agente "sabe cosas" de ti que no le contaste | Cargó tu memoria automática de Claude Code | `env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}` |
| Aparecen tools de Gmail, Drive, Linear… | Conectores de claude.ai de tu sesión | `strict_mcp_config=True`, pasando tus servidores en `mcp_servers` (apaga también el `.mcp.json` del cwd) |
| `mcp_servers=[]` en el `init` con un `.mcp.json` en el cwd | `strict_mcp_config=True` ignora el `.mcp.json` | Quítalo, o pasa los servidores en `mcp_servers` |
| El agente termina con "Necesito tu permiso para escribir en …" | Pidió `Edit` (con `resume` lo prefiere sobre `Write`) y `Edit` no está en `allowed_tools` | Añade `"Edit"`; el hook `Write\|Edit` sigue limitando el archivo |

## Para depurar en dos pasos

1. Imprime el `init`: `model`, `tools`, `skills`, `agents`, `mcp_servers`. Ahí está el 80 % de "no cargó".
2. Quita `stderr=lambda _: None` (o pon `stderr=lambda l: print("[cli]", l)`). El CLI cuenta lo que le pasa.
