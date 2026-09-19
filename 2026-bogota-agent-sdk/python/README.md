# Python · el asistente de viaje, un primitivo por archivo

Nueve archivos con el mismo hilo. Siempre la misma pregunta:

> Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.

En el 01 el modelo contesta que no puede. En el 08 contesta el vuelo de LATAM
del jueves 24 de septiembre a las 06:15, BOG → MDE, reserva ABC123. Entre medias
le vas dando las piezas, una por archivo.

## Correr

```bash
uv sync
uv run python 01_query.py
```

No hace falta API key: el SDK lanza el Claude Code que trae adentro y usa tu
sesión. Si tienes una `ANTHROPIC_API_KEY` en el entorno, esas corridas se van a
facturar a esa key.

El notebook:

```bash
uv run jupyter lab notebook.ipynb
```

## El recorrido

| Archivo | Primitivo | Qué mirar |
|---|---|---|
| `01_query.py` | `query()` | Corre y termina. Un agente no necesita chat. Sin tools, no puede. |
| `02_stream.py` | el stream | Cada mensaje con su etiqueta: arranque, tool call, tool result, texto, recibo. |
| `03_tool.py` | tool propia | `@tool` + `create_sdk_mcp_server`. La diferencia entre `tools` y `allowed_tools`. |
| `04_mcp.py` | MCP | `gmail_mcp.py` corre aparte por stdio. `strict_mcp_config` y por qué salva la demo. |
| `05_skill.py` | skill | El procedimiento en markdown, en `workspace/.claude/skills/`. Se carga cuando se usa. |
| `06_permisos_hooks.py` | permisos y hooks | Las listas filtran por nombre; el hook ve los argumentos. El `deny` no tumba al agente. |
| `07_subagente.py` | subagente | Contexto aparte, un solo resultado de vuelta, `parent_tool_use_id` en sus mensajes. |
| `08_agente_vuelo.py` | todo junto | Topes de turnos y de dinero. Traza completa en `salidas/traza.jsonl`. |
| `09_conversar.py` | `ClaudeSDKClient` | El contraste: conversar es una función más y hay que pedirla. |

Archivos de apoyo: `mostrar.py` (el impresor, para que la salida se vea igual en
todas las laptops) y `gmail_mcp.py` (el servidor MCP falso con los 4 correos).

`08_agente_vuelo.py` acepta otra pregunta:

```bash
uv run python 08_agente_vuelo.py "¿Tengo algo reservado para el fin de semana?"
```

## La bandeja

Cuatro correos y tres trampas. Solo uno es la respuesta.

| id | De | Asunto | Recibido | Qué es |
|---|---|---|---|---|
| c1 | Avianca | ¡Vuela a Cartagena desde $189.900! | 2026-09-15 | promoción |
| c2 | Wingo | Tu vuelo BOG → CTG | 2026-09-13 | vuelo que ya pasó |
| c3 | LATAM | Confirmación de reserva | 2026-09-16 | **la respuesta** |
| c4 | Booking.com | Tu reserva en Medellín | 2026-09-17 | hotel, no vuelo |

La tool `hoy()` devuelve siempre "sábado 19 de septiembre de 2026". Fija a
propósito: la demo da lo mismo el día del taller y seis meses después.

## Aislar la corrida de tu Claude Code

Tres opciones que van en todos los ejemplos, por una razón concreta:

| Opción | Sin ella |
|---|---|
| `strict_mcp_config=True` | Entran los conectores de tu cuenta claude.ai y el agente intenta tu Gmail de verdad. También apaga el `.mcp.json` de la carpeta, así que los servidores van inline en `mcp_servers`. |
| `setting_sources=[]` o `["project"]` | Carga tus skills y tu `CLAUDE.md` personales. Con `["project"]` lee solo el `.claude/` del `cwd`. |
| `env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}` | El agente "sabe cosas" de ti que nadie le contó. |

En el ARRANQUE vas a seguir viendo los skills que trae Claude Code de fábrica
(`deep-research`, `dataviz`, …). Son del CLI empaquetado, no tuyos; `skills=[…]`
es lo que decide cuáles puede invocar el agente.

## Cuando algo falle

| Síntoma | Qué pasó |
|---|---|
| `Invalid API key` / `Credit balance is too low` | Hay una `ANTHROPIC_API_KEY` en el entorno. Quítala para usar tu sesión. |
| `asyncio.run() cannot be called from a running event loop` | Estás en el notebook. Ahí se usa `await`, no `asyncio.run`. |
| `RuntimeError: aclose(): asynchronous generator is already running` | Saliste del `async for` con `break` o `return`. Deja que el stream termine. |
| `ResultError: Reached maximum budget` | Se cumplió `max_budget_usd`. Es intencional: hay mensaje de error **y** excepción. |
| El skill no sale en el ARRANQUE | Falta `setting_sources=["project"]` o el `SKILL.md` no está en `.claude/skills/<dir>/`. |
| Aparece una llamada a `ToolSearch` antes de tu tool | Normal. La búsqueda de tools viene encendida y carga el esquema cuando hace falta. |
| El agente ignora `allowed_tools` | `allowed_tools` no restringe: solo aprueba. Para prohibir, `disallowed_tools`. |

Para depurar, quita `stderr=lambda _: None` y mira lo que cuenta el CLI.
