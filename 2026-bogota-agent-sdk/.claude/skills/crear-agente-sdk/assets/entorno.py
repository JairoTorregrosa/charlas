"""entorno.py — carga la API key desde .env antes de que arranque el SDK.

Busca `.env` en la raíz del kit y en esta carpeta. Con `ANTHROPIC_API_KEY` el
agente corre contra tu cuenta de Console (así va en producción). Sin key, el SDK
usa la sesión de Claude Code de tu máquina.

    import entorno   # primera línea de cada script
"""

import os
from pathlib import Path

AQUI = Path(__file__).parent.resolve()

for ruta in (AQUI.parent / ".env", AQUI / ".env"):
    if ruta.exists():
        for linea in ruta.read_text().splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                if valor.strip():
                    os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))

CON_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
print(f"[auth] {'API key de .env (Console)' if CON_KEY else 'sin API key en .env: uso la sesión de Claude Code'}\n")
