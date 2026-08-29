# Permisos y hooks: quién decide si una herramienta corre

Cuando el modelo pide una tool, el SDK pasa por seis porteros **en este orden** y se detiene en el primero que resuelve.

```
tool_use
   │
   ▼
1. hooks PreToolUse        deny → BLOQUEADA        (tu código; corre siempre primero)
   │
   ▼
2. reglas deny             casa → BLOQUEADA        (disallowed_tools, settings.json; gana hasta en bypass)
   │
   ▼
3. reglas ask              casa → va a can_use_tool
   │
   ▼
4. permission_mode         bypassPermissions → EJECUTA · acceptEdits (archivos) → EJECUTA · plan → can_use_tool
   │
   ▼
5. reglas allow            casa → EJECUTA          (allowed_tools, settings.json)
   │
   ▼
6. can_use_tool            allow → EJECUTA · deny → BLOQUEADA · (en dontAsk no se llama: BLOQUEADA)
```

El modo es una política y el hook es un portero. El portero revisa antes de que se mire la lista.

## Modos

| `permission_mode` | Qué aprueba solo |
|---|---|
| `"default"` | Lecturas dentro del cwd. Lo demás cae a reglas y a `can_use_tool` |
| `"acceptEdits"` | Además, operaciones de archivo dentro del cwd |
| `"plan"` | Nada que escriba; manda ediciones y comandos a `can_use_tool` |
| `"dontAsk"` | Solo lo que esté en `allowed_tools`; lo demás se **niega** sin preguntar |
| `"bypassPermissions"` | Todo, salvo reglas `deny` y borrados críticos. Solo en carpetas desechables |

## Hook `PreToolUse`: la forma

```python
from claude_agent_sdk import HookMatcher

async def portero(input_data, tool_use_id, context):
    tool = input_data["tool_name"]            # "Bash", "Write", ...
    args = input_data["tool_input"]           # el input de la tool
    if todo_bien:
        return {}                             # sin opinión: sigue al portero 2
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",     # "allow" · "deny" · "ask"
            "permissionDecisionReason": "Motivo. Lo lee el MODELO como resultado de la tool.",
        },
        "systemMessage": "Opcional. Lo lee la persona, no el modelo.",
    }

hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[portero]),
                      HookMatcher(matcher="Write|Edit", hooks=[otro])]}
```

- `matcher` es el nombre de la tool (o varios con `|`). `None` = todas.
- Un `deny` no tumba al agente: el motivo vuelve como `tool_result` y el modelo busca otro camino. Escribe el motivo como instrucción ("usa Read en vez de cat"), no como log.
- `permissionDecision: "allow"` salta el resto de los porteros; `"ask"` fuerza `can_use_tool`.
- También puedes devolver `updatedInput` para cambiar los argumentos antes de que corra.

## Los otros hooks (dónde más engancha tu código)

| Hook | Cuándo | Para qué |
|---|---|---|
| `PreToolUse` | Antes de cada tool | Bloquear, cambiar argumentos, registrar |
| `PostToolUse` | Después, con `tool_output` | Auditar, añadir contexto (`additionalContext`), cambiar la salida |
| `PostToolUseFailure` | La tool falló | Reaccionar al error |
| `UserPromptSubmit` | Llega un prompt | Reescribirlo (`updatedPrompt`), añadir contexto |
| `Stop` | El agente va a parar | Verificar (correr tests) y pedirle que siga (`continue_`) |
| `SubagentStart` / `SubagentStop` | Un hijo arranca / termina | Observar; `additionalContext` al arrancar |
| `PreCompact` | Antes de comprimir el contexto | Archivar la transcripción |
| `PermissionRequest` | Se va a preguntar | Decidir desde código |

Solo en TS: `SessionStart`, `SessionEnd`, `Notification`, `MessageDisplay`, `PostToolBatch`, `TaskCreated`, `TaskCompleted`.

## `can_use_tool`: la persona en el loop

```python
async def can_use_tool(nombre, input_, contexto):
    r = input(f"¿Dejo pasar {nombre} {input_}? (s/n) ")
    if r == "s":
        return {"behavior": "allow", "updatedInput": input_}
    return {"behavior": "deny", "message": "La persona dijo que no. Propón otra cosa."}
```

- Solo se llama si nadie decidió antes. Un nombre pelado en `allowed_tools` lo hace invisible para esa tool (el SDK avisa con un warning).
- En Python exige **streaming input**: el prompt como generador async, más un hook `PreToolUse` vacío para mantener el canal abierto. En TS funciona con un `str`.
- Para lógica que aplique a **todas** las llamadas, usa un hook, no el callback.

## Lo que hacemos en el taller

Un hook por agente que deja escribir **un solo archivo** (`roast.md`, `candidatos.md`, `explicacion.md`), y en el Parcero otro que deja a Bash solo `git clone` y lecturas. Con eso, un agente con acceso completo al sistema de archivos no puede dañar nada fuera de su casa.
