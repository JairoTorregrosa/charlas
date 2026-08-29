# Crea tu primer agente con Claude Agent SDK

Taller de 45 minutos (Platzi Conf Bogotá, 29 de agosto de 2026). Un notebook con tres agentes; cada celda suma un primitivo del SDK: system prompt, tools, stream de mensajes, skills, hooks, sub-agentes, streaming, MCP, tope de gasto, `resume` y dos agentes en paralelo.

| Agente | Archivo | Su casa | Qué hace |
|---|---|---|---|
| El Parcero Crítico | `agent_parcero.py` | `workspace_parcero/` | Clona un repo público de GitHub y lo roastea en `roast.md`. |
| Buscador de vivienda | `agent_vivienda.py` | `workspace_vivienda/` | Busca avisos reales de arriendo en Bogotá (Exa y Firecrawl por MCP) y deja una tabla en `candidatos.md`. |
| El Monitor | `agent_monitor.py` | `workspace_monitor/` | Te explica un paper en cinco preguntas (alphaXiv por MCP), en `explicacion.md`. |

Los agentes usan lo que trae el SDK (Read, Bash, WebFetch…), un skill, un ayudante y servidores MCP externos. Ninguno tiene tools propias. Cada uno escribe un solo archivo en su casa; un hook lo garantiza.

## Correr el notebook con tu suscripción de Claude

El SDK no trae el modelo: arranca Claude Code como subproceso y usa la sesión que tengas iniciada ahí. Con una cuenta Pro o Max no necesitas API key.

1. Instala [uv](https://docs.astral.sh/uv/) (trae Python 3.13 si te falta) y `git`.
2. Instala Claude Code: `npm install -g @anthropic-ai/claude-code`.
3. Inicia sesión una vez: `claude` → `/login`. Es el login de Claude Code, no el del navegador.
4. Revisa que no haya una API key en el entorno: `echo $ANTHROPIC_API_KEY` debe salir vacío. Si sale algo, `unset ANTHROPIC_API_KEY` en esa terminal (una key gana sobre la suscripción y cobra por token).
5. Clona y corre:
   ```bash
   git clone https://github.com/JairoTorregrosa/charlas.git
   cd charlas/2026-platzi-agent-sdk
   uv sync
   uv run jupyter lab demo.ipynb
   ```
6. Ejecuta las celdas en orden. La sección 0 comprueba que `claude` responde y que no hay `ANTHROPIC_API_KEY`; la celda `PROVEEDOR = "claude"` elige el cerebro de todo el notebook.

Lo que gasta es la cuota de tu plan (límite de sesión y semanal), no dinero. El `total_cost_usd` del recibo es un estimado del SDK, útil para comparar corridas. Sin suscripción, ver [Otros cerebros](#otros-cerebros).

En VS Code: abre la carpeta, elige el intérprete `.venv/bin/python` (ya viene en `.vscode/settings.json`) y corre las celdas desde ahí.

Cada agente también corre solo, desde la terminal:

```bash
uv run agent_parcero.py https://github.com/JairoTorregrosa/crea-tu-web
uv run agent_vivienda.py "Apartamento en Chapinero, máximo 2.500.000, 2 habitaciones"
uv run agent_monitor.py "Attention is all you need"
```

### El Monitor necesita alphaXiv

Es un servidor MCP con OAuth. Se registra una vez en tu Claude Code y se autentica en el navegador:

```bash
claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1 --scope user
claude     # → /mcp → alphaxiv → Authenticate
```

Los otros dos MCP del taller (Exa y Firecrawl, en `workspace_vivienda/.mcp.json`) no piden llave.

## Otros cerebros

El SDK habla la API de Anthropic; cualquier servicio que hable ese formato sirve. `proveedores.py` arma las variables de entorno y el notebook las aplica con una línea:

```python
PROVEEDOR = "openrouter"   # "claude" · "openrouter" · "opencode" · "codex"
```

| `PROVEEDOR` | Qué es | Costo | Qué hace falta |
|---|---|---|---|
| `"claude"` | Suscripción de Claude Code | suscripción | `claude` → `/login` |
| `"openrouter"` | OpenRouter, modelo `minimax/minimax-m3:free` | 0 | `OPENROUTER_API_KEY` en `.env` |
| `"opencode"` | OpenCode Zen, modelo `big-pickle` (sin verificar) | 0 | `OPENCODE_API_KEY` en `.env` |
| `"codex"` | Suscripción de ChatGPT, vía LiteLLM, modelo `gpt-5.6-luna` | suscripción | Proxy local: `litellm/start.sh` |

`cp .env.example .env` y llena la llave que uses. El paso a paso de cada uno, con el curl para probar antes de abrir el notebook, está en [`docs/proveedores.md`](docs/proveedores.md). Dos límites: los conectores MCP de claude.ai (y con ellos El Monitor) van solo con `"claude"`, y la tool nativa `WebSearch` es la búsqueda del servidor de Anthropic; por eso el Buscador de vivienda busca por MCP.

## Cómo está armado

```
2026-platzi-agent-sdk/
├── demo.ipynb              ← el notebook: el hilo completo, un primitivo por celda
├── agent_parcero.py        ← un agente = un archivo
├── agent_vivienda.py
├── agent_monitor.py
├── proveedores.py          ← el cerebro: qué modelo y qué variables de entorno
├── workspace_parcero/      ← la casa del agente: lo que ve como cwd
│   └── .claude/
│       ├── skills/roast-de-codigo/SKILL.md     ← el procedimiento
│       └── agents/inspector.md                 ← el ayudante
├── workspace_vivienda/     ← misma forma, más .mcp.json (Exa, Firecrawl)
├── workspace_monitor/      ← misma forma
├── litellm/                ← proxy para la suscripción de ChatGPT
└── docs/                   ← cheat sheets
```

- El `.py` tiene el system prompt, las opciones del SDK, los porteros (hooks) y el lector del stream.
- La carpeta `workspace_` tiene lo que una persona puede editar sin programar: el skill, el ayudante y los MCP. El agente la carga con `setting_sources=["project"]`.

## Cuánto cuesta una corrida

Medido con `claude-sonnet-5`: Parcero ≈ USD 0.31 (108 s), Vivienda ≈ USD 0.70 (91 s), Monitor ≈ USD 0.36 (75 s). El notebook completo, unos USD 3.5. Todos los agentes tienen `max_budget_usd` como tope; con una suscripción el costo es el estimado del SDK, no un cobro.

## Cheat sheets

En [`docs/`](docs/): `event_model.md` (qué llega en el stream), `options.md`, `tools.md`, `workspace.md` (skills, ayudantes, MCP), `permisos_hooks.md`, `errores.md` (síntoma → causa → arreglo) y `proveedores.md`.

## Haz el tuyo

Copia un `agent_x.py` y su `workspace_x/`. Cambia el system prompt, el skill y el ayudante. Deja los porteros y los topes.

Verificado con `claude-agent-sdk` 0.2.148 y Claude Code 2.1.251 (2026-08-29). El material se comparte tal cual, para aprender y reutilizar con atribución.
