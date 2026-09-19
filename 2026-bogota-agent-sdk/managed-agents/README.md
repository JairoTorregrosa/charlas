# Managed Agents · el mismo asistente, pero sin harness tuyo

En `python/` el loop corre en tu laptop: tú pones el proceso, las tools y los
permisos. Aquí lo pone Anthropic. Tú mandas mensajes y lees eventos.

Tres piezas:

| Pieza | Qué es |
|---|---|
| **agente** | el modelo, el system prompt, las tools, los MCP y las skills |
| **entorno** | dónde corren las sesiones: un sandbox cloud o uno tuyo |
| **sesión** | una instancia del agente corriendo, con su propio sandbox |

## Antes de empezar

Esto **no** funciona con una suscripción de claude.ai. Managed Agents pide
cuenta de Console, API key y facturación:

1. Cuenta en <https://platform.claude.com>
2. API key en <https://platform.claude.com/settings/keys>
3. Saldo en <https://platform.claude.com/settings/billing>

Si la cuenta es nueva, arranca en "Evaluation tier", con límites por debajo de
los normales y sin tabla pública. Créala y haz una llamada trivial **el día
anterior**, no en la sala.

```bash
cp .env.example .env     # y pon tu ANTHROPIC_API_KEY
uv sync
uv run python crear_agente.py     # imprime AGENT_ID y ENVIRONMENT_ID: pégalos en .env
uv run python abrir_sesion.py
uv run python ver_todo.py
uv run python ver_todo.py sesn_...   # el historial de eventos de esa sesión
```

| Archivo | Qué hace |
|---|---|
| `crear_agente.py` | `agents.create` con el system prompt y el toolset integrado, y `environments.create` |
| `abrir_sesion.py` | crea la sesión con tope de gasto, abre el stream, manda la pregunta e imprime los eventos |
| `ver_todo.py` | lista agentes, entornos y sesiones; con un id de sesión, sus eventos |
| `bandeja.py` | los cuatro correos del taller, dentro del mensaje |

## El agente del ejercicio, completo

`uv run python agente_vuelo.py` crea en tu workspace el mismo agente que actuamos con los letreros y le hace la pregunta del taller: «Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.»

| Pieza | Aquí |
|---|---|
| system prompt | el del taller |
| skill | `skills/buscar-vuelo/`, subida con la Skills API y adjunta al agente. Vive en el sandbox: el agente la abre con `read /workspace/skills/buscar-vuelo/SKILL.md` |
| tool | `hoy` (custom tool, corre en tu máquina) |
| gmail | `gmail_buscar` y `gmail_leer` (custom tools, corren en tu máquina) |
| harness | el loop corre en Anthropic |

Corrida del 19-sep-2026: abre la skill → `hoy` → `gmail_buscar(desde 2026-09-12)` → `gmail_leer(c2)` y `gmail_leer(c3)` en la misma respuesta → LATAM BOG → MDE, jue 24 sep 06:15, ABC123. **1 turno · 5 llamadas al LLM · 11 s · 2 centavos.** Es la misma secuencia del replay de las slides. La primera corrida imprime el `SKILL_ID`; ponlo en `.env` para no subir la skill otra vez.

## Cinco corridas para comparar

Todas guardan sus eventos, crudos y en orden, en `salidas/<sesión>/eventos.jsonl`. El historial también queda en el servidor: `uv run python ver_todo.py sesn_...` lo lista completo, y en Console se ve en la pestaña Events de la sesión.

| Comando | Qué muestra | Costo medido (19-sep-2026) |
|---|---|---|
| `uv run python abrir_sesion.py` | La bandeja va en el mensaje. Responde LATAM jue 24 sep 06:15 ABC123. | 2 centavos |
| `uv run python abrir_sesion.py "¿Qué día es hoy y qué versión de Python tienes? Compruébalo con bash."` | El agente usa `bash` dentro del sandbox: `date && python3 --version`. | menos de 1 centavo |
| `uv run python agente_custom_tools.py` | Custom tools: el loop corre en Anthropic y `hoy`, `gmail_buscar` y `gmail_leer` corren en tu máquina. La sesión se pausa con `requires_action` hasta que devuelves cada `user.custom_tool_result`. | 1 centavo |
| `uv run python variaciones.py solo-lectura` | Toolset con todo apagado salvo `read`, `glob`, `grep`. Le pides bash y responde que no tiene esa tool. | 1 centavo |
| `uv run python variaciones.py sin-chat` | Un pedido, escribe `/tmp/itinerario.md` en el sandbox, lo muestra y termina. | 2 centavos |
| `uv run python variaciones.py tacaño` | Tope de 1 centavo: la sesión para con `stop_reason: budget_reached` a mitad de trabajo. | 1 centavo |

La secuencia de eventos de un tool call propio: `span.model_request_start` → `agent.custom_tool_use` → `span.model_request_end` → `session.status_idle (requires_action)` → tu `user.custom_tool_result` → `session.status_running`. Es el mismo loop del taller, con el harness en la nube y el ejecutor en tu código.

## Ocho agentes, uno por familia de ideas

`uv run python ideas.py` crea nueve agentes y conversa con cada uno. El primero es `viajes`, el hilo del taller, con cuatro turnos (próximo vuelo, hotel, borrador para pedir el regreso, itinerario). Los otros ocho van de a tres turnos: asistente personal, revisor de código, analista de datos, finanzas personales, SDR de prospección, contenido de marca, monitor de noticias y revisor de contratos. Cada uno trae su system prompt y dos o tres custom tools con datos de ejemplo que corren en tu máquina. `uv run python ideas.py ventas datos` corre solo algunos.

En cada conversación el tercer turno, o el segundo, empuja un guardrail: «invierte lo que me sobre en cripto», «envíalo ya y marca el lead como ganado», «agrega un 30 % de descuento». Los tres se negaron: el primero por el system prompt, el segundo porque la tool de enviar no existe, el tercero porque la guía de marca que leyó lo prohíbe.

Cada sesión deja `salidas/<sesión>/eventos.jsonl` y `transcript.md` turno por turno. Costo medido el 19-sep-2026: entre 1 y 3 centavos por conversación de tres turnos, 18 centavos las ocho.



- **El MCP es remoto.** Managed Agents se conecta a servidores MCP por URL
  (HTTP). El `gmail_mcp.py` de `python/` es un proceso local por stdio, así que
  aquí no sirve: la bandeja va dentro del mensaje.
- **Las tools vienen de fábrica.** `agent_toolset_20260401` trae `bash`, `read`,
  `write`, `edit`, `glob`, `grep`, `web_fetch` y `web_search`. Se apagan una a
  una con `configs`.
- **Se paga aparte el tiempo.** Tokens a tarifa del modelo, más **$0.08 por hora
  de sesión**, y solo mientras la sesión está `running`. En `idle` no corre el
  reloj. Una sesión que termina queda **`idle`**, no `terminated`.
- **Pon tope siempre.** `budget` es un techo duro por sesión. El monto va en
  **centavos, como string**, y solo en USD. Al llegar, la sesión pasa a `idle`
  con `stop_reason: budget_reached`.
- **Abre el stream antes de mandar el mensaje.** Solo llegan los eventos
  emitidos después de abrir el stream.
- **No hay ZDR ni BAA de HIPAA** en Managed Agents.

## Lo mismo desde la terminal, con `ant`

El CLI oficial de la plataforma. En macOS:

```bash
brew install anthropics/tap/ant
ant auth login          # o exporta ANTHROPIC_API_KEY
```

| Script | Equivalente con `ant` |
|---|---|
| `crear_agente.py` | `ant beta:agents create --name "…" --model claude-sonnet-5 --system "…"` |
| | `ant beta:environments create --name taller-bogota` |
| `abrir_sesion.py` | `ant beta:sessions create --agent ag_… --environment-id env_…` |
| | `ant beta:sessions:events stream --session-id sesn_…` |
| | `ant beta:sessions:events send --session-id sesn_… --event '{"type":"user.message",…}'` |
| `ver_todo.py` | `ant beta:agents list` · `ant beta:environments list` · `ant beta:sessions list` |
| | `ant beta:sessions:events list --session-id sesn_…` |

Usa `--help` en cualquier subcomando: `ant beta:sessions create --help`.

También hay un modo declarativo, `ant apply archivo.md`, que reconcilia lo que
existe en la plataforma con lo que dice tu archivo y deja constancia en
`claude-lock.json`:

```markdown
---
name: Asistente de viaje
model: claude-sonnet-5
tools:
  - type: agent_toolset_20260401
---

Eres un asistente personal. Respondes en español, corto y con datos.
```

**Ojo con la autenticación del CLI.** `ant auth login` deja un perfil OAuth con
el que responden `ant beta:agents list` y `ant beta:sessions list`, pero
`ant beta:environments list` devuelve **401 authentication_error**. Para los
entornos hace falta la API key de Console: `ANTHROPIC_API_KEY` en el entorno o
en el `.env`. Verificado el 2026-09-18 con `ant` 1.30.0.

Y dentro de Claude Code existe un onboarding guiado: `/claude-api managed-agents-onboard`.

## Doc

- <https://platform.claude.com/docs/en/managed-agents/overview>
- <https://platform.claude.com/docs/en/managed-agents/quickstart>
- Console: <https://platform.claude.com/workspaces/default/agent-quickstart/>
