"""Un mismo agente, cuatro proveedores.

El Agent SDK habla el formato de la API de Anthropic. Cualquier servicio que
hable ese formato sirve: se le dice al proceso de Claude Code a dónde ir
(`ANTHROPIC_BASE_URL`) y con qué llave (`ANTHROPIC_AUTH_TOKEN`). Eso viaja en
la opción `env`.

Uso en el notebook:

    from proveedores import proveedor
    modelo, env = proveedor("openrouter")
    opciones = ClaudeAgentOptions(model=modelo, env=env, ...)

Ver `docs/proveedores.md` para el paso a paso de cada uno.
"""

import os
from pathlib import Path

# .env está al lado de este archivo; lo leemos sin dependencias.
for linea in (Path(__file__).parent / ".env").read_text().splitlines() if (Path(__file__).parent / ".env").exists() else []:
    if "=" in linea and not linea.startswith("#"):
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

SIN_RUIDO = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
}


def _gateway(url, llave, modelo):
    return modelo, {
        **SIN_RUIDO,
        "ANTHROPIC_BASE_URL": url,
        "ANTHROPIC_AUTH_TOKEN": llave,
        "ANTHROPIC_API_KEY": "",
        # Claude Code usa un modelo "pequeño" para tareas internas; que sea el mismo.
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": modelo,
        "ANTHROPIC_SMALL_FAST_MODEL": modelo,
    }


def proveedor(nombre, modelo=None):
    """Devuelve (modelo, env) listos para ClaudeAgentOptions."""
    if nombre == "claude":
        # La suscripción de Claude Code. No hay que pasar nada.
        return modelo or "claude-sonnet-5", dict(SIN_RUIDO)

    if nombre == "openrouter":
        # Gratis y con tools: minimax/minimax-m3:free. Otros: z-ai/glm-5.2:free (a veces con rate limit).
        return _gateway("https://openrouter.ai/api", os.environ["OPENROUTER_API_KEY"], modelo or "minimax/minimax-m3:free")

    if nombre == "opencode":
        # OpenCode Zen. La llave sale de https://opencode.ai/auth (login con GitHub o Google).
        return _gateway("https://opencode.ai/zen", os.environ["OPENCODE_API_KEY"], modelo or "big-pickle")

    if nombre == "codex":
        # Suscripción de ChatGPT a través de LiteLLM. Requiere el proxy: `litellm/start.sh`.
        # Solo gpt-5.6-luna, gpt-5.6-sol o gpt-5.6-terra (razonamiento high, ver litellm/config.yaml).
        return _gateway("http://127.0.0.1:4000", "sk-taller-local", modelo or "gpt-5.6-luna")

    raise ValueError(f"proveedor desconocido: {nombre}")
