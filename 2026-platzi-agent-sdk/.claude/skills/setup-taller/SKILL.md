---
name: setup-taller
description: Deja el taller "Crea tu primer agente con Claude Agent SDK" listo para correr en la máquina del usuario y comprueba que el notebook funciona. Úsalo cuando pidan "prepara el taller", "setup del taller", "déjame listo el notebook", "revisa que demo.ipynb corra", "no me corre el taller", "configura el proveedor", o antes de un workshop. Corre un chequeo (uv, git, Claude Code, login, API keys, SDK, MCP, una llamada real) y arregla lo que se pueda; lo que requiere login o llaves lo pide al usuario. No es para escribir agentes nuevos (eso es `crear-agente`).
---

# setup-taller: dejar el notebook corriendo

Trabajas en la carpeta del taller (la que tiene `demo.ipynb`, `proveedores.py` y `docs/`). El objetivo es que `uv run jupyter lab demo.ipynb` corra de punta a punta con el cerebro que el usuario eligió. Nada de explicar el SDK: comprobar, arreglar, volver a comprobar.

## 1. Pregunta con qué cerebro

Una sola `AskUserQuestion`, header `Cerebro`, opciones en este orden:

1. `Suscripción de Claude (Recomendado)`: Pro o Max, `claude` → `/login`. Sin llaves.
2. `OpenRouter gratis`: modelo `minimax/minimax-m3:free`, llave gratis.
3. `ChatGPT (Codex) vía LiteLLM`: suscripción de ChatGPT, proxy local.
4. `OpenCode Zen gratis`: sin verificar de punta a punta.

Guarda la respuesta como `PROVEEDOR` (`claude`, `openrouter`, `codex`, `opencode`). Si el usuario ya lo dijo en el prompt, no preguntes.

## 2. Corre el chequeo

```bash
uv run python .claude/skills/setup-taller/scripts/check.py --proveedor <PROVEEDOR>
```

Si `uv` no existe, ese es el primer arreglo (sección 3) y el chequeo se repite después. El script imprime una línea por punto: `[ok]`, `[falta]` con su arreglo, o `[aviso]`. Termina con código 1 si falta algo.

Puntos que revisa: `uv`, `git`, `claude` (versión), login de Claude Code, variables `ANTHROPIC_*` en el entorno, `claude-agent-sdk` instalado, `.env` con la llave del proveedor, una llamada real al modelo (barata: 1 vuelta, sin tools), los MCP de `workspace_vivienda/.mcp.json` (Exa, Firecrawl) y el MCP alphaXiv del Monitor.

## 3. Arregla, en este orden

Haz tú lo que sea un comando. Pide al usuario lo que sea un login o una llave. Antes de instalar algo en su máquina, dilo en una línea y espera el sí.

| `[falta]` | Quién | Arreglo |
|---|---|---|
| `uv` | tú | macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh`. Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`. Abre una terminal nueva o `source ~/.zshrc`. |
| `git` | tú | macOS: `xcode-select --install`. Linux: `sudo apt install git`. Windows: `winget install Git.Git`. |
| `claude` | tú | `npm install -g @anthropic-ai/claude-code` (necesita Node 18+; si no hay Node, `brew install node` o https://nodejs.org). |
| login de Claude Code | usuario | Que corra `claude auth login` en su terminal (abre el navegador). Solo con `PROVEEDOR=claude`. |
| `ANTHROPIC_API_KEY` en el entorno | usuario | `unset ANTHROPIC_API_KEY` en la terminal donde va a abrir Jupyter, y quitarla del `.zshrc`/`.bashrc` si está ahí. Con una key puesta, el SDK cobra por la API en vez de usar la suscripción. Solo con `PROVEEDOR=claude`. |
| `claude-agent-sdk` | tú | `uv sync` en la carpeta del taller. Si el error es `Failed to spawn`, `rm -rf .venv && uv sync`. |
| llave del proveedor | usuario | `cp .env.example .env` y que pegue la llave: OpenRouter en https://openrouter.ai/settings/keys, OpenCode Zen en https://opencode.ai/auth. Tú no pegas llaves. |
| proxy LiteLLM (`codex`) | tú + usuario | `uv tool install "litellm[proxy]==1.98.0"`, luego `litellm/start.sh` en una terminal aparte. La primera petición imprime en el log del proxy `Visit https://auth0.openai.com/codex/device` con un código: el usuario entra y lo pega. Detalle en `docs/proveedores.md` §4. |
| llamada real falla | depende | Lee el mensaje. `Invalid API key` o `Credit balance is too low` = hay una key en el entorno; `401` con gateway = llave mala o header equivocado (`docs/proveedores.md`); `CLINotFoundError` = falta `claude`. La tabla completa está en `docs/errores.md`. |
| MCP Exa/Firecrawl `failed` | red | Son servidores públicos sin llave. Si fallan, suele ser red o límite diario; el notebook corre igual salvo la sección 4. Díselo. |
| alphaXiv no registrado o `needs-auth` | tú + usuario | `claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1 --scope user`; luego el usuario abre `claude`, escribe `/mcp`, elige `alphaxiv` y `Authenticate`. Solo afecta a la sección 5 (El Monitor); el resto corre sin esto. |

Después de cada arreglo, vuelve a correr el chequeo. Para cuando todo esté `[ok]` o el único `[falta]` sea algo que el usuario decidió dejar (por ejemplo alphaXiv).

## 4. Prueba el notebook

Con el chequeo en verde, corre la prueba más barata que ejercita el notebook de verdad:

```bash
uv run python .claude/skills/setup-taller/scripts/check.py --proveedor <PROVEEDOR> --notebook
```

Ejecuta la sección 0 y la celda 3.1 de `demo.ipynb` (una vuelta, sin tools) con el `PROVEEDOR` elegido y muestra la respuesta del modelo. Si el usuario quiere ver un agente completo antes del taller, ofrece `uv run agent_parcero.py` (≈ USD 0.30 con Claude; clona un repo público y escribe `workspace_parcero/roast.md`). No lo corras sin que diga que sí.

## 5. Cierra con la lista

Tres bloques, sin explicaciones largas:

- Lo que quedó listo, en una línea por punto.
- Lo que queda pendiente y quién lo hace (login, llave, alphaXiv).
- El comando para arrancar: `uv run jupyter lab demo.ipynb`, y que en la celda de la sección 0 `PROVEEDOR` debe decir el que eligió.

## Reglas

- No pongas llaves ni tokens en archivos ni en la conversación; el usuario los pega en `.env`.
- No cambies `demo.ipynb` ni los `agent_*.py`. Si algo del código falla, repórtalo con el error completo.
- No corras el notebook entero: cuesta unos USD 3.5 y tarda diez minutos. La prueba de la sección 4 basta.
- Si el usuario no tiene ninguno de los cuatro cerebros, el camino más corto es OpenRouter: llave gratis en dos minutos.
