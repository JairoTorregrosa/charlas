# Un agente, cuatro proveedores

El Agent SDK arranca Claude Code como subproceso y Claude Code habla la API de Anthropic (`POST /v1/messages`). Cualquier servicio que hable ese formato sirve como cerebro. Cambian dos variables de entorno, que van en la opción `env`:

- `ANTHROPIC_BASE_URL`: a dónde mandar las llamadas. Claude Code le pega `/v1/messages` al final.
- `ANTHROPIC_AUTH_TOKEN`: la llave. Va como `Authorization: Bearer`. (`ANTHROPIC_API_KEY` va como `x-api-key`; los gateways de abajo quieren Bearer.)

Y tres de apoyo:

- `ANTHROPIC_API_KEY=""` para que no se cuele una llave del shell.
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` y `ANTHROPIC_SMALL_FAST_MODEL` iguales al modelo elegido: Claude Code usa un modelo "pequeño" para tareas internas y si no existe en el proveedor, falla.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` para que no haga llamadas extra.

`proveedores.py` arma todo eso:

```python
from proveedores import proveedor
modelo, env = proveedor("openrouter")
opciones = ClaudeAgentOptions(model=modelo, env=env, tools=["Bash"], allowed_tools=["Bash"])
```

Verificado con `claude-agent-sdk` 0.2.148 y Claude Code 2.1.251 (2026-08-29).

| Proveedor | Modelo | Costo | Notas |
|---|---|---|---|
| Claude Code (suscripción) | `claude-sonnet-5` | suscripción | El default del taller |
| OpenRouter | `minimax/minimax-m3:free` | 0 | El `total_cost_usd` del SDK es un estimado; OpenRouter marca $0 |
| OpenCode Zen | `big-pickle` | 0 | Llave con login en opencode.ai (GitHub o Google). Sin verificar de punta a punta |
| Codex (suscripción de ChatGPT) + LiteLLM | `gpt-5.6-luna`, razonamiento `high` | suscripción | Proxy local + hook `fix_system.py` |

## 1. Claude Code

Nada que configurar. El SDK usa el login de `claude`. Si en el shell hay `ANTHROPIC_API_KEY`, esa gana sobre la suscripción; bórrala.

```python
modelo, env = proveedor("claude")
```

## 2. OpenRouter (gratis)

OpenRouter expone el formato de Anthropic en `https://openrouter.ai/api/v1/messages`.

1. Llave: https://openrouter.ai/settings/keys → New Key. Ponle límite de crédito (con $2 sobra; los `:free` cuestan 0).
2. Guárdala en `taller/.env` (está en `.gitignore`):
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
3. Modelos gratis con tools (lista viva en `https://openrouter.ai/api/v1/models`, filtra por `:free`):
   - `minimax/minimax-m3:free`: rápido, usa tools bien.
   - `z-ai/glm-5.2:free`: bueno; a ratos responde `rate_limit_exceeded`.
   - `nvidia/nemotron-3-ultra-550b-a55b:free`: a ratos responde `provider_unavailable`.
4. Prueba sin SDK:
   ```bash
   curl https://openrouter.ai/api/v1/messages \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"minimax/minimax-m3:free","max_tokens":100,"messages":[{"role":"user","content":"hola"}]}'
   ```
5. En el notebook:
   ```python
   modelo, env = proveedor("openrouter")               # minimax/minimax-m3:free
   modelo, env = proveedor("openrouter", "z-ai/glm-5.2:free")
   ```

Con un gateway no hay login de claude.ai, así que tampoco hay conectores ni MCP de claude.ai (`stderr` lo avisa: `claude.ai connectors are disabled because ANTHROPIC_API_KEY or another auth source is set`). El Monitor (alphaXiv) necesita el proveedor `claude`.

## 3. OpenCode Zen (gratis)

Zen es el gateway de OpenCode. Expone el formato de Anthropic en `https://opencode.ai/zen/v1/messages` y tiene modelos a costo 0: `big-pickle`, `deepseek-v4-flash-free`, `mimo-v2.5-free`, `hy3-free`, `muse-spark-1.2-contributor-free` (lista viva en `https://opencode.ai/zen/v1/models`).

1. Llave: https://opencode.ai/auth → Continue with GitHub o Google → copia la API key.
2. En `taller/.env`:
   ```
   OPENCODE_API_KEY=...
   ```
3. Prueba sin SDK:
   ```bash
   curl https://opencode.ai/zen/v1/messages \
     -H "Authorization: Bearer $OPENCODE_API_KEY" -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"big-pickle","max_tokens":100,"messages":[{"role":"user","content":"hola"}]}'
   ```
   Si devuelve 401, cambia el header por `x-api-key: $OPENCODE_API_KEY` y en `proveedores.py` usa `ANTHROPIC_API_KEY` en vez de `ANTHROPIC_AUTH_TOKEN` para este proveedor.
4. En el notebook:
   ```python
   modelo, env = proveedor("opencode")                 # big-pickle
   ```

Sin llave el endpoint responde `Internal server error`: no hay modo anónimo.

## 4. Suscripción de ChatGPT (Codex) + LiteLLM

El backend de Codex habla Responses API; LiteLLM traduce desde el formato de Anthropic. La suscripción entra con el login OAuth de Codex.

1. Instalar (evita 1.82.7 y 1.82.8, que salieron con malware):
   ```bash
   uv tool install "litellm[proxy]==1.98.0"
   ```
2. Tokens. LiteLLM guarda su login en `~/.config/litellm/chatgpt/auth.json` con la forma `{access_token, refresh_token, id_token, expires_at, account_id}`. Dos caminos:
   - Login propio: arranca el proxy, manda una petición, y en el log sale `Visit https://auth0.openai.com/codex/device` con un código. Entras y pegas el código.
   - Reusar el de Codex CLI: `~/.codex/auth.json` tiene los mismos tokens bajo `tokens`; se copian a la forma plana. Si LiteLLM refresca el token, Codex CLI puede pedir `codex login` otra vez.
3. Config en `litellm/config.yaml`:
   ```yaml
   model_list:
     - model_name: gpt-5.6-luna
       model_info:
         mode: responses          # obligatorio: el backend de Codex solo expone /responses
       litellm_params:
         model: chatgpt/gpt-5.6-luna
         reasoning_effort: high
         drop_params: true
   general_settings:
     master_key: sk-taller-local
   litellm_settings:
     callbacks: fix_system.proxy_handler_instance
   ```
   Modelos disponibles con cuenta de ChatGPT: `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, los tres con razonamiento `high`. Otros nombres devuelven "model is not supported when using Codex with a ChatGPT account".
4. `litellm/fix_system.py`, un hook de LiteLLM. El backend de ChatGPT rechaza los mensajes con `role: system`. Claude Code manda el `system` como lista de bloques (LiteLLM lo convierte en un mensaje `system`; como texto va a `instructions`) y un mensaje `system` con `<total_tokens>` dentro de `messages`. El hook aplana el primero a texto y mueve el segundo al `system`.
5. Arrancar:
   ```bash
   litellm/start.sh          # puerto 4000, llave sk-taller-local
   ```
6. Prueba sin SDK (con `stream: true`; sin stream LiteLLM devuelve "Unknown items in responses API response"):
   ```bash
   curl -N http://127.0.0.1:4000/v1/messages \
     -H "Authorization: Bearer sk-taller-local" -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"gpt-5.6-luna","max_tokens":200,"stream":true,"messages":[{"role":"user","content":"hola"}]}'
   ```
7. En el notebook:
   ```python
   modelo, env = proveedor("codex")                    # gpt-5.6-luna, razonamiento high
   modelo, env = proveedor("codex", "gpt-5.6-sol")     # o gpt-5.6-terra
   ```

Detalles:

- LiteLLM antepone las instrucciones de Codex ("You are Codex, based on GPT-5...") a tu system prompt; es el peaje del backend. Tu system prompt va después.
- El puente devuelve `stop_reason: end_turn` aunque haya `tool_use`. Claude Code ejecuta la tool igual.
- `CHATGPT_USER_AGENT` en `start.sh` imita el de Codex CLI, como recomienda la doc de LiteLLM.

## Qué viaja y qué no

Con cualquiera de los cuatro, el resto del taller es igual: `cwd`, `tools`, `allowed_tools`, hooks, skills, sub-agentes, `resume`. Dos cosas dependen del proveedor:

- Los conectores MCP de claude.ai van con el login de claude.ai. Los MCP de `.mcp.json` y de `claude mcp add` van con todos.
- `WebSearch` es la búsqueda del servidor de Anthropic. Con otro proveedor la tool sigue en el `init`, pero el resultado lo escribe el propio modelo: "no tengo buscador" o links a Google. `WebFetch` descarga en local y va con todos.

El Buscador de vivienda busca con dos MCP sin llave (`workspace_vivienda/.mcp.json`: Exa en `https://mcp.exa.ai/mcp` y Firecrawl en `https://mcp.firecrawl.dev/v2/mcp`) y lleva `disallowed_tools=["WebSearch"]`. Corre con cualquiera de los cuatro proveedores.
