# El workspace: lo que el agente carga de su carpeta

Con `cwd=<carpeta>` y `setting_sources=["project"]`, el SDK lee `<carpeta>/.claude/` y `<carpeta>/.mcp.json`. La carpeta **es** la configuración. Lo que una persona puede editar sin programar va aquí; lo que es código va en el `.py`.

```
workspace_<nombre>/
├── .claude/
│   ├── skills/<skill>/SKILL.md      procedimientos
│   ├── agents/<ayudante>.md         sub-agentes
│   └── settings.json                reglas de permisos (opcional)
├── .mcp.json                        servidores MCP externos (opcional)
├── CLAUDE.md                        instrucciones del proyecto (opcional; en el taller no se usa)
└── <lo que el agente escribe>
```

## Skill: `.claude/skills/<nombre>/SKILL.md`

```markdown
---
name: roast-de-codigo
description: Criterio y formato para un roast. Úsalo cuando te pidan "roast" o "qué tan malo es este repo".
---

# Título

Cuerpo en markdown: criterio, formato, ejemplos, qué hacer si falta algo.
```

- `description` es lo que el modelo lee para decidir cuándo usarlo. Junto con `when_to_use` se corta a 1.536 caracteres en el listado.
- El **comando** `/nombre` sale del **nombre del directorio**, no del campo `name`.
- Otros campos: `when_to_use`, `argument-hint`, `arguments` (nombres para `$arg`), `user-invocable: false` (solo el modelo), `allowed-tools` (reglas que se aprueban mientras corre el skill).
- Tres niveles de costo: el listado (nombre + descripción, siempre) → el `SKILL.md` completo (solo al usarlo) → archivos vecinos (`reference.md`, `scripts/`) solo si el modelo los lee. Nómbralos en el `SKILL.md` o no sabrá que existen.
- Un skill invocado se queda pegado en la conversación; escríbelo como instrucciones permanentes, no como pasos de un solo uso. Menos de 500 líneas.

## Sub-agente: `.claude/agents/<nombre>.md`

```markdown
---
name: inspector
description: Revisa UN archivo y devuelve sus 3 peores líneas. Úsalo para revisar varios en paralelo.
tools: Read, Grep
model: haiku
---

El system prompt del ayudante, en markdown.
```

- `description`: cuándo usarlo (lo lee el padre). `tools`: lista blanca; lo que no está, no existe. `model`: `haiku` / `sonnet` / `opus` / `inherit` o id completo.
- Otros campos: `disallowedTools`, `skills` (se precargan), `maxTurns`, `effort`, `memory` (`user`/`project`/`local`), `mcpServers`, `background`.
- El padre lo lanza con la tool `Agent` (`subagent_type: "inspector"`). Lo único que viaja del padre al hijo es el `prompt` de esa llamada; el hijo **no** ve el historial del padre. Lo único que vuelve es el mensaje final del hijo.
- El mismo sub-agente se puede definir por código con `agents={"inspector": AgentDefinition(...)}`. Si hay dos con el mismo nombre, gana el de código.

## Servidores MCP: `.mcp.json`

```json
{
  "mcpServers": {
    "exa": { "type": "http", "url": "https://mcp.exa.ai/mcp" },
    "alphaxiv": { "type": "http", "url": "https://api.alphaxiv.org/mcp/v1",
                  "headers": { "Authorization": "Bearer ${ALPHAXIV_API_KEY}" } },
    "archivos": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"] }
  }
}
```

- `stdio`: `command` + `args` (+ `env`). La doc del servidor te da un comando.
- `http` (o `sse`): `type` + `url` (+ `headers`). La doc te da una URL.
- `${VAR}` se expande desde el entorno del proceso `claude` (el `env` de las opciones cuenta).
- **OAuth**: el SDK no abre navegador. Un servidor http que lo exige sale `needs-auth`. Dos salidas: pasar un token en `headers`, o registrarlo en tu Claude Code y autenticar una vez ahí (`claude mcp add --transport http nombre URL --scope user` → `claude` → `/mcp` → Authenticate); luego el SDK lo carga con `setting_sources` que incluya `"user"`.
- Verifica en el `init`: `data["mcp_servers"]` con `status` `connected` / `pending` / `needs-auth`.

## `.claude/settings.json` (opcional)

```json
{ "permissions": { "allow": ["Read", "Grep"], "deny": ["Bash(rm:*)"], "ask": ["Write"] } }
```

Reglas `deny` y `ask` ganan sobre el `permission_mode`. En el taller preferimos hooks en el `.py`, porque se ven en la demo.

## `setting_sources`, en una tabla

| Valor | Qué carga |
|---|---|
| `"project"` | `.claude/` del cwd (y hacia arriba hasta la raíz del repo), `.mcp.json`, `CLAUDE.md` |
| `"user"` | `~/.claude/` (skills y agents personales), servidores de `claude mcp add --scope user` |
| `"local"` | `.claude/settings.local.json`, `CLAUDE.local.md` |
| `[]` | Nada del disco. Reproducible |

Lo que **no** controla: la memoria automática de tu Claude Code (apágala con `env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}`) y los conectores MCP de claude.ai (`strict_mcp_config=True` los apaga, junto con el `.mcp.json`; pasa entonces tus servidores en `mcp_servers`).
