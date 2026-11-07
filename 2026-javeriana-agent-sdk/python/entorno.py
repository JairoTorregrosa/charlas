"""entorno.py — deja lista la autenticación antes de que arranque el SDK.

Tres caminos, en este orden de preferencia para el taller:

  1. ant auth login        (recomendado) el SDK usa tu sesión de platform.claude.com
                           y gasta los créditos del taller. No creas ninguna key.
  2. ANTHROPIC_API_KEY     una key de platform.claude.com/settings/keys en .env
  3. CLAUDE_CODE_OAUTH_TOKEN  tu suscripción Pro/Max (claude setup-token), solo uso personal

Si hay una key o un token en el entorno, ganan sobre la sesión de ant.

    import entorno   # primera línea de cada script
"""

import os
from pathlib import Path

AQUI = Path(__file__).parent.resolve()

for ruta in (AQUI.parent / ".env", AQUI / ".env"):
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                if valor.strip():
                    os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def _perfil_ant():
    """Perfil activo de `ant auth login`, o None. Mac/Linux: ~/.config/anthropic · Windows: %APPDATA%\\anthropic."""
    candidatos = [os.environ.get("ANTHROPIC_CONFIG_DIR"), Path.home() / ".config" / "anthropic"]
    if os.environ.get("APPDATA"):
        candidatos.append(Path(os.environ["APPDATA"]) / "anthropic")
    for c in filter(None, candidatos):
        activo = Path(c) / "active_config"
        nombre = activo.read_text(encoding="utf-8").strip() if activo.exists() else "default"
        if (Path(c) / "credentials" / f"{nombre}.json").exists():
            return nombre
    return None


if os.environ.get("ANTHROPIC_API_KEY"):
    AUTH = "API key de .env (platform.claude.com)"
elif os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
    AUTH = "token de tu suscripción (claude setup-token)"
elif _perfil_ant():
    # Explícito, para que gane sobre un login de claude.ai (Pro/Max) en Claude Code:
    # sin esto, quien tenga Claude Code logueado gasta su plan y no los créditos.
    os.environ.setdefault("ANTHROPIC_PROFILE", _perfil_ant())
    AUTH = f"sesión de ant, perfil «{os.environ['ANTHROPIC_PROFILE']}» · créditos de platform.claude.com"
else:
    AUTH = "sin key ni sesión de ant: si falla con «Not logged in», corre  ant auth login"
print(f"[auth] {AUTH}\n")
