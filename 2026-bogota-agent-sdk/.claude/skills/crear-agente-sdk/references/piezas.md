# Piezas opcionales

Ejemplos corridos y verificados: `python/0N_*.py` y `typescript/0N_*.ts` del kit (SDK Python 0.2.157, TypeScript 0.3.269).

## MCP externo por stdio

```python
mcp_servers={"gmail": {"command": sys.executable, "args": [str(AQUI / "gmail_mcp.py")]}}
allowed_tools=["mcp__gmail__buscar", "mcp__gmail__leer"]
```
```ts
mcpServers: { gmail: { command: "npx", args: ["tsx", join(import.meta.dirname, "gmail_mcp.ts")] } }
```
Ejemplo: `04_mcp`.

## Subagente

Python (`07_subagente.py`):
```python
from claude_agent_sdk import AgentDefinition
LECTOR = AgentDefinition(
    description="Cuándo usarlo. El principal decide con esta línea.",
    prompt="Qué hace y qué devuelve. Pide una salida corta y con formato.",
    tools=["mcp__gmail__buscar", "mcp__gmail__leer"],
    model="haiku",
    maxTurns=8,          # camelCase también en Python
    background=False,    # el principal espera la respuesta
)
ClaudeAgentOptions(agents={"lector": LECTOR}, tools=["Agent"], allowed_tools=[...las tools del subagente...])
```
TypeScript (`07_subagente.ts`): mismo bloque dentro de `agents`, con `tools: ["Task"]` en el principal y `forwardSubagentText: true` para ver su texto.

- Las tools **nativas** del subagente (`Read`, `Glob`…) tienen que estar también en el `tools` del principal; si no, el SDK se niega a crearlo («would be spawned with zero tools»). Las tools MCP no lo necesitan: llegan por `mcp_servers`.
- En la prueba del 19-sep-2026, un `Read` nativo dentro de un subagente quedó negado aun con `dontAsk` y `allowed_tools` correctos, y el mismo `Read` funcionó en el principal. Para un primer agente, deja la lectura de archivos en el principal y usa subagentes con tools MCP o propias, como en `07_subagente`.
- Un subagente multiplica llamadas y costo (en las pruebas, de USD 0,06 a USD 0,36 cuando algo falla). Con subagente sube los topes a `max_turns=20` y `max_budget_usd=0.50`, y si el principal tiene `Task`/`Agent` sin que tú definas `agents`, puede delegar en agentes de fábrica del CLI (`Explore`, `general-purpose`): declara `Task` solo cuando definas los tuyos.
- Los permisos no se heredan del bloque `agents`: `tools` del subagente da disponibilidad; la aprobación sale del `allowed_tools` global.
- Los subagentes corren en background por defecto.
- Cada mensaje de adentro trae `parent_tool_use_id`.
- En la lista del `init` la tool puede salir como `Task`; en los `tool_use` sale como `Agent`.

## Conversación de varios turnos

Guarda `session_id` del `ResultMessage` y pásalo como `resume` en el siguiente `query()`. Sin `resume` cada `query()` empieza con el tablero vacío. Ejemplo: `09_conversar`.

## Correr sin humano

`permission_mode="dontAsk"` + `allowed_tools` exacto + topes. Sirve igual en cron, CI o un webhook. Con API key: `ANTHROPIC_API_KEY` en el entorno del proceso.
