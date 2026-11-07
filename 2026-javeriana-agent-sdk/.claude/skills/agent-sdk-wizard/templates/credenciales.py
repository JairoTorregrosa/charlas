# credenciales.py — elige UNA forma de autenticar y apaga las demás.
#
# Generado por la skill agent-sdk-wizard. No lo edites: cambia .env.
#
# Por qué existe: Claude Code (que el SDK lleva adentro) acepta varias
# credenciales a la vez y gana la de mayor prioridad, en silencio:
#     ANTHROPIC_API_KEY  >  CLAUDE_CODE_OAUTH_TOKEN  >  ANTHROPIC_PROFILE  >  tu login de claude.ai
# Si dejas eso al azar, el agente puede gastar tu plan Pro/Max en vez de los
# créditos. Aquí .env dice cuál se usa (AGENTE_AUTH) y las otras se borran
# del proceso del agente. Si falta algo, el agente NO arranca.

import json
import os
import sys
import time
from pathlib import Path

MODOS = {
    "ant": "ANTHROPIC_PROFILE",               # A · login con `ant auth login` (créditos de la org)
    "api_key": "ANTHROPIC_API_KEY",           # B · API key de platform.claude.com
    "suscripcion": "CLAUDE_CODE_OAUTH_TOKEN",  # C · tu plan Pro/Max (`claude setup-token`)
}


def _leer_env(ruta: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def _carpetas_de_ant(env: dict[str, str]) -> list[Path]:
    # Dónde guarda `ant` sus perfiles. Si .env (o tu shell) nombra una carpeta,
    # SOLO esa cuenta: buscar en otra podría usar otra cuenta con el mismo perfil.
    explicita = env.get("ANTHROPIC_CONFIG_DIR") or os.environ.get("ANTHROPIC_CONFIG_DIR")
    if explicita:
        return [Path(explicita)]
    candidatas: list[str | None] = []
    if os.environ.get("XDG_CONFIG_HOME"):
        candidatas.append(str(Path(os.environ["XDG_CONFIG_HOME"]) / "anthropic"))
    candidatas.append(str(Path.home() / ".config" / "anthropic"))
    if os.environ.get("APPDATA"):  # Windows
        candidatas.append(str(Path(os.environ["APPDATA"]) / "anthropic"))
    return [Path(c) for c in candidatas if c]


def _parar(mensaje: str) -> None:
    sys.exit(f"[auth] {mensaje}")


def preparar_credenciales() -> str:
    """Deja en el entorno UNA credencial y devuelve el modo. Nunca imprime secretos."""
    env = _leer_env(Path(__file__).with_name(".env"))
    # Todo sale de .env, nada de tu shell: así no se cuela otra cuenta.
    modo = env.get("AGENTE_AUTH", "")
    if modo not in MODOS:
        _parar("Falta AGENTE_AUTH en .env (ant | api_key | suscripcion). "
               "Copia .env.example a .env y llénalo, o corre otra vez el paso 0 del wizard.")

    variable = MODOS[modo]
    valor = env.get(variable, "")
    if not valor:
        _parar(f"AGENTE_AUTH={modo} pero falta {variable} en .env.")

    for otra in MODOS.values():  # apaga las otras dos
        if otra != variable:
            os.environ.pop(otra, None)
    os.environ[variable] = valor

    if modo == "ant":
        # Un perfil que no existe se ignora EN SILENCIO y paga tu login de claude.ai.
        # Por eso aquí se exige que el archivo del perfil exista.
        for carpeta in _carpetas_de_ant(env):
            archivo = carpeta / "credentials" / f"{valor}.json"
            if archivo.exists():
                datos = json.loads(archivo.read_text(encoding="utf-8"))
                # Vencido y sin refresh_token = no se puede renovar: cada llamada fallaría.
                vencido = isinstance(datos.get("expires_at"), (int, float)) and datos["expires_at"] < time.time()
                if vencido and not datos.get("refresh_token"):
                    _parar(f"El perfil «{valor}» de ant tiene la sesión vencida y no se puede "
                           f"renovar. Corre `ant auth login --profile {valor}` (o usa otro perfil "
                           "de `ant profile list`).")
                os.environ["ANTHROPIC_CONFIG_DIR"] = str(carpeta)
                print(f"[auth] ant · perfil «{valor}» (paga la organización de ese login)")
                return modo
        _parar(f"No encuentro el perfil «{valor}» de ant. Corre `ant auth login` y luego "
               "`ant auth status`: copia el nombre del perfil a ANTHROPIC_PROFILE en .env "
               "(y su «Config dir» a ANTHROPIC_CONFIG_DIR si no es ~/.config/anthropic).")

    if modo == "api_key":
        print("[auth] API key de .env (paga la organización dueña de la key)")
    else:
        print("[auth] suscripción Pro/Max (cuenta contra los límites de tu plan, no usa créditos)")
    return modo
