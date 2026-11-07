"""Constantes del taller y el cliente de la API."""
import hashlib
import os
from pathlib import Path

import anthropic

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"

BETA = "managed-agents-2026-04-01"


def _cargar_env() -> None:
    """Lee .env. Lo que está en .env le gana al entorno.

    Mucha gente ya tiene ANTHROPIC_API_KEY exportada en ~/.zshrc con la key del
    trabajo. Si el entorno ganara, el taller se cobraría a esa org sin avisar.
    """
    archivo = RAIZ / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text().splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:
            os.environ[clave.strip()] = valor


_cargar_env()

# Sonnet rinde los créditos del taller. Para comparar, cámbialo con TALLER_MODELO en .env.
MODELO = os.environ.get("TALLER_MODELO", "claude-sonnet-5-5")


def huella_key() -> str:
    """Identifica la key sin guardarla: cada key tiene su propio archivo de estado."""
    return hashlib.sha256(os.environ.get("ANTHROPIC_API_KEY", "").encode()).hexdigest()[:10]


def key_corta() -> str:
    """Los últimos 4 caracteres de la key, para saber cuál se está usando."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return f"sk-ant-…{key[-4:]}" if key else "sin key"


def _cliente_ant(perfil: str) -> anthropic.Anthropic:
    """Usa la sesión de `ant auth login` en vez de una API key (para quien ensaya sin key)."""
    import json
    import subprocess

    salida = subprocess.run(["ant", "auth", "print-credentials", "--profile", perfil],
                            capture_output=True, text=True, check=True)
    token = json.loads(salida.stdout)["access_token"]

    def con_oauth(request) -> None:
        betas = request.headers.get("anthropic-beta")
        request.headers["anthropic-beta"] = ",".join(filter(None, [betas, "oauth-2025-04-20"]))

    return anthropic.Anthropic(
        auth_token=token, http_client=anthropic.DefaultHttpxClient(event_hooks={"request": [con_oauth]})
    )


def cliente() -> anthropic.Anthropic:
    perfil = os.environ.get("TALLER_ANT_PROFILE", "")
    if perfil and not os.environ.get("ANTHROPIC_API_KEY"):
        return _cliente_ant(perfil)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SystemExit("Falta ANTHROPIC_API_KEY. Cópiala en .env (mira .env.example).")
    if key.startswith("apikey_"):
        raise SystemExit(
            "Eso es el ID de la key, no la key. La key empieza por sk-ant- y solo se "
            "muestra una vez al crearla en platform.claude.com/settings/keys."
        )
    return anthropic.Anthropic(api_key=key)
