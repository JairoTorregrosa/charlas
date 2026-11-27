"""Paso 0 · Revisar que todo esté listo. No gasta créditos.

Uso: uv run pasos/0_preparacion.py
"""
import shutil
import subprocess
import sys
from importlib.metadata import version

import anthropic

from taller.config import MODELO, cliente, key_corta

OK, FALLA = "\033[92m✓\033[0m", "\033[91m✗\033[0m"


def revisar(nombre: str, prueba) -> bool:
    try:
        detalle = prueba()
        print(f"{OK} {nombre}{f': {detalle}' if detalle else ''}")
        return True
    except SystemExit as e:
        print(f"{FALLA} {nombre}: {e}")
    except anthropic.AuthenticationError:
        print(f"{FALLA} {nombre}: la API rechazó la key. Revisa que esté completa y sin espacios.")
    except anthropic.PermissionDeniedError as e:
        print(f"{FALLA} {nombre}: la org no tiene acceso ({e.message}).")
    except anthropic.APIConnectionError as e:
        print(f"{FALLA} {nombre}: no hay conexión con api.anthropic.com ({e}).")
    except Exception as e:
        print(f"{FALLA} {nombre}: {type(e).__name__}: {e}")
    return False


def main() -> int:
    print(f"Python {sys.version.split()[0]} · anthropic {version('anthropic')} · modelo {MODELO}\n")
    client = None

    def key():
        nonlocal client
        client = cliente()
        return f"usando {key_corta()} (compara con la de tu org del taller)"

    def cli(nombre: str, *args: str):
        def prueba():
            if shutil.which(nombre) is None:
                raise RuntimeError(f"no está instalado (lo necesitas para la Pista A)")
            salida = subprocess.run([nombre, *args], capture_output=True, text=True, timeout=20)
            return (salida.stdout or salida.stderr).strip().splitlines()[0]
        return prueba

    def modelo():
        ids = {m.id for m in client.models.list(limit=100)}
        if MODELO not in ids:
            raise RuntimeError(f"{MODELO} no aparece en los modelos de tu org")
        return None

    def managed_agents():
        list(client.beta.agents.list(limit=1))
        return None

    resultados = [revisar("ANTHROPIC_API_KEY en .env", key)]
    if client is not None:
        resultados += [
            revisar("La key funciona y el modelo está disponible", modelo),
            revisar("La org tiene acceso a Managed Agents", managed_agents),
        ]
    # La Pista A usa Claude Code y el CLI ant. Si faltan, puedes hacer la Pista B.
    print()
    revisar("Claude Code", cli("claude", "--version"))
    revisar("CLI ant (brew install anthropics/tap/ant)", cli("ant", "--version"))
    revisar("git", cli("git", "--version"))

    if all(resultados):
        print("\nListo para el taller.")
        return 0
    print("\nArregla lo que está en rojo antes del sábado. Si te atoras, escribe en el grupo.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
