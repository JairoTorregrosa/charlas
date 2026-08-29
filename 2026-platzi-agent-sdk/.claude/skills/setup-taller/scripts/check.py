"""Chequeo del taller: imprime [ok] / [falta] / [aviso] por punto y termina con 1 si falta algo.

    uv run python .claude/skills/setup-taller/scripts/check.py --proveedor claude
    uv run python .claude/skills/setup-taller/scripts/check.py --proveedor openrouter --notebook

Corre desde la carpeta del taller (la que tiene demo.ipynb).
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path.cwd()
FALTAS = 0


def ok(msg):
    print(f"[ok]     {msg}")


def falta(msg, arreglo):
    global FALTAS
    FALTAS += 1
    print(f"[falta]  {msg}\n         arreglo: {arreglo}")


def aviso(msg):
    print(f"[aviso]  {msg}")


def version(cmd):
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0]
    except Exception as e:  # noqa: BLE001
        return f"{cmd[0]} responde con error: {e}"


def herramientas():
    for cmd, arreglo in [
        (["uv", "--version"], "instala uv: https://docs.astral.sh/uv/"),
        (["git", "--version"], "instala git"),
        (["node", "--version"], "instala Node 18+ (https://nodejs.org o `brew install node`); lo necesita Claude Code"),
        (["claude", "--version"], "npm install -g @anthropic-ai/claude-code"),
    ]:
        v = version(cmd)
        if v:
            ok(f"{cmd[0]}: {v}")
        else:
            falta(f"{cmd[0]} no está en el PATH", arreglo)
    v = version(["uv", "run", "jupyter", "--version"]) if shutil.which("uv") and (RAIZ / ".venv").exists() else None
    if v:
        ok("jupyter (en .venv)")
    else:
        aviso("jupyter aún no está en .venv; lo instala `uv sync`")


def login(proveedor):
    if not shutil.which("claude"):
        return
    try:
        r = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        d = {}
    if d.get("loggedIn"):
        ok(f"login de Claude Code: {d.get('authMethod', '?')}")
    elif proveedor == "claude":
        falta("Claude Code sin sesión", "el usuario corre `claude auth login` (abre el navegador)")
    else:
        aviso("Claude Code sin sesión; con este proveedor no hace falta")


def entorno(proveedor):
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
        if os.environ.get(var):
            if proveedor == "claude":
                falta(f"{var} está en el entorno: gana sobre la suscripción", f"`unset {var}` en esta terminal y quítala del .zshrc/.bashrc")
            else:
                aviso(f"{var} está en el entorno; proveedores.py la sobreescribe al correr")
    if proveedor == "claude" and not any(os.environ.get(v) for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")):
        ok("sin variables ANTHROPIC_* en el entorno")


def sdk():
    try:
        import claude_agent_sdk  # noqa: F401
        from importlib.metadata import version as v
        ok(f"claude-agent-sdk {v('claude-agent-sdk')}")
        return True
    except Exception:  # noqa: BLE001
        falta("claude-agent-sdk no importa", "`uv sync` en la carpeta del taller (y correr este script con `uv run python ...`)")
        return False


def llave(proveedor):
    if proveedor not in ("openrouter", "opencode"):
        return True
    var = {"openrouter": "OPENROUTER_API_KEY", "opencode": "OPENCODE_API_KEY"}[proveedor]
    env = RAIZ / ".env"
    valor = os.environ.get(var, "")
    if env.exists():
        for linea in env.read_text().splitlines():
            if linea.startswith(var + "="):
                valor = linea.split("=", 1)[1].strip()
    if valor:
        ok(f"{var} en .env")
        return True
    falta(f"{var} vacía", f"`cp .env.example .env` y pegar la llave (ver docs/proveedores.md)")
    return False


def proxy(proveedor):
    if proveedor != "codex":
        return True
    v = version(["litellm", "--version"])
    if v:
        ok(f"litellm: {v}")
    else:
        falta("litellm no está en el PATH", "`uv tool install \"litellm[proxy]==1.98.0\"`")
    import urllib.request

    try:
        urllib.request.urlopen("http://127.0.0.1:4000/health/liveliness", timeout=3)
        ok("proxy LiteLLM en :4000")
        return True
    except Exception:  # noqa: BLE001
        falta("proxy LiteLLM no responde en :4000", "`uv tool install \"litellm[proxy]==1.98.0\"` y `litellm/start.sh` en otra terminal (docs/proveedores.md §4)")
        return False


async def llamada(proveedor):
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, SystemMessage, query

    sys.path.insert(0, str(RAIZ))
    from proveedores import proveedor as prov

    modelo, env = prov(proveedor, "claude-haiku-4-5-20251001" if proveedor == "claude" else None)
    init = None
    recibo = None
    errores = []
    try:
        async for m in query(
            prompt="Responde solo: listo.",
            options=ClaudeAgentOptions(model=modelo, env=env, tools=[], setting_sources=[], strict_mcp_config=True, max_turns=1, stderr=lambda s: errores.append(s)),
        ):
            if isinstance(m, SystemMessage) and m.subtype == "init":
                init = m.data
            elif isinstance(m, ResultMessage):
                recibo = m
    except Exception as e:  # noqa: BLE001
        falta(f"la llamada al modelo falló: {str(e).splitlines()[0][:160]}", "ver docs/errores.md; el detalle está en el mensaje")
        for linea in errores[-3:]:
            print("         cli:", linea[:160])
        return False
    if recibo and recibo.subtype == "success":
        fuente = init.get("apiKeySource", "?") if init else "?"
        ok(f"llamada real con {proveedor} ({modelo}): {recibo.num_turns} vuelta, apiKeySource={fuente}")
        if proveedor == "claude" and fuente != "none":
            aviso(f"apiKeySource={fuente}: no está usando la suscripción")
        return True
    falta(f"la llamada terminó con {recibo.subtype if recibo else 'sin recibo'}", "ver docs/errores.md")
    return False


async def mcps(proveedor):
    from claude_agent_sdk import ClaudeAgentOptions, SystemMessage, query

    sys.path.insert(0, str(RAIZ))
    from proveedores import proveedor as prov

    modelo, env = prov(proveedor, "claude-haiku-4-5-20251001" if proveedor == "claude" else None)
    ws = RAIZ / "workspace_vivienda"
    estados = {}
    try:
        async for m in query(
            prompt="Responde solo: listo.",
            options=ClaudeAgentOptions(model=modelo, env=env, cwd=str(ws), tools=[], setting_sources=["project"], max_turns=1, stderr=lambda _: None),
        ):
            if isinstance(m, SystemMessage) and m.subtype == "init":
                estados = {s["name"]: s["status"] for s in m.data.get("mcp_servers", [])}
    except Exception as e:  # noqa: BLE001
        aviso(f"no se pudo leer el estado de los MCP: {str(e)[:120]}")
        return
    for nombre in ("exa", "firecrawl"):
        st = estados.get(nombre, "ausente")
        if st in ("connected", "pending"):
            ok(f"MCP {nombre}: {st}")
        else:
            falta(f"MCP {nombre}: {st}", "son públicos y sin llave; revisa la red. Solo afecta a la sección 4 del notebook")


async def alphaxiv_sdk(proveedor):
    """Devuelve {nombre: status} de los MCP cuyo nombre contenga 'alphaxiv' (registro de usuario o conector de claude.ai)."""
    from claude_agent_sdk import ClaudeAgentOptions, SystemMessage, query

    sys.path.insert(0, str(RAIZ))
    from proveedores import proveedor as prov

    modelo, env = prov(proveedor, "claude-haiku-4-5-20251001" if proveedor == "claude" else None)
    estados = {}
    try:
        async for m in query(
            prompt="Responde solo: listo.",
            options=ClaudeAgentOptions(model=modelo, env=env, tools=[], setting_sources=["user"], max_turns=1, stderr=lambda _: None),
        ):
            if isinstance(m, SystemMessage) and m.subtype == "init":
                estados = {s["name"]: s["status"] for s in m.data.get("mcp_servers", []) if "alphaxiv" in s["name"].lower()}
    except Exception:  # noqa: BLE001
        return None
    return estados


def alphaxiv(estados=None):
    if estados:
        if any(st == "connected" for st in estados.values()):
            ok("MCP alphaXiv: " + ", ".join(f"{n}={st}" for n, st in estados.items()))
            return
        aviso("MCP alphaXiv visto pero sin conectar: " + ", ".join(f"{n}={st}" for n, st in estados.items()))
    if not shutil.which("claude"):
        return
    r = subprocess.run(["claude", "mcp", "get", "alphaxiv"], capture_output=True, text=True, timeout=30)
    salida = (r.stdout + r.stderr).lower()
    if "needs auth" in salida:
        falta("alphaXiv registrado pero sin autenticar", "el usuario abre `claude`, escribe `/mcp`, elige alphaxiv → Authenticate. Solo afecta a la sección 5 (El Monitor)")
    elif "url:" in salida and "alphaxiv" in salida:
        ok("MCP alphaxiv registrado")
    else:
        falta("alphaXiv no registrado", "`claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1 --scope user` y luego `/mcp` → Authenticate. Solo afecta a la sección 5")


async def notebook(proveedor):
    nb = json.loads((RAIZ / "demo.ipynb").read_text())
    celdas = {c.get("id"): "".join(c["source"]) for c in nb["cells"]}
    codigo = [c for c in nb["cells"] if c["cell_type"] == "code"]
    # sección 0 (chequeo + proveedor) y 3.1 (una vuelta, sin tools)
    fuente = "\n".join(["".join(codigo[0]["source"]), "".join(codigo[1]["source"]).replace('PROVEEDOR = "claude"', f'PROVEEDOR = "{proveedor}"'), "".join(codigo[2]["source"])])
    cuerpo = "async def _celdas():\n" + "\n".join("    " + l for l in fuente.splitlines()) + "\n"
    ns = {}
    os.chdir(RAIZ)
    sys.path.insert(0, str(RAIZ))
    print("\n--- demo.ipynb: sección 0 + celda 3.1 ---")
    exec(cuerpo, ns)
    await ns["_celdas"]()
    print("--- fin ---\n")
    ok("sección 0 y celda 3.1 del notebook corren")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proveedor", default="claude", choices=["claude", "openrouter", "opencode", "codex"])
    ap.add_argument("--notebook", action="store_true", help="ejecuta también la sección 0 y la celda 3.1 de demo.ipynb")
    a = ap.parse_args()

    if not (RAIZ / "demo.ipynb").exists():
        print("Corre este script desde la carpeta del taller (la que tiene demo.ipynb).")
        sys.exit(2)

    print(f"Chequeo del taller · proveedor: {a.proveedor}\n")
    herramientas()
    login(a.proveedor)
    entorno(a.proveedor)
    hay_sdk = sdk()
    hay_llave = llave(a.proveedor)
    hay_proxy = proxy(a.proveedor)
    estados_alphaxiv = None
    if hay_sdk and hay_llave and hay_proxy and shutil.which("claude"):
        if asyncio.run(llamada(a.proveedor)):
            asyncio.run(mcps(a.proveedor))
            estados_alphaxiv = asyncio.run(alphaxiv_sdk(a.proveedor))
            if a.notebook:
                asyncio.run(notebook(a.proveedor))
    else:
        aviso("sin llamada real: primero lo de arriba")
    alphaxiv(estados_alphaxiv)
    print()
    if FALTAS:
        print(f"{FALTAS} punto(s) por arreglar.")
        sys.exit(1)
    print("Todo listo: uv run jupyter lab demo.ipynb")


if __name__ == "__main__":
    main()
