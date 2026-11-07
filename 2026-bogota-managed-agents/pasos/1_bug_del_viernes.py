"""Caso 1 · El bug del viernes.

Viernes, 5 p. m. Los tests del facturador fallan y nadie sabe desde cuándo. Le
pasas el repo a un agente, te vas, y cuando vuelves hay un parche esperándote.

Qué aprendes:
- Las cuatro piezas: environment (el contenedor), agent (modelo, instrucciones,
  tools), session (una corrida en un contenedor nuevo) y events (lo que mandas y
  lo que recibes).
- Darle tu código a la sesión y bajar lo que deja en /mnt/session/outputs/.
- No confiar: el script aplica el parche en tu máquina y corre los tests aquí.

Uso: uv run pasos/1_bug_del_viernes.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from taller.config import MODELO, RAIZ, cliente
from taller.recursos import bajar_salidas, guardar_agente, guardar_entorno, resumen_costo, subir_archivo
from taller.sesion import conversar

REPO = RAIZ / "repo-facturador"
client = cliente()

entorno = guardar_entorno(client, "codigo", {
    "type": "cloud",
    # Sin networking explícito, la API deja el contenedor con internet abierto.
    # Aquí solo puede llegar a los gestores de paquetes.
    "networking": {"type": "limited", "allow_package_managers": True},
    "packages": {"pip": ["pytest"]},
})

agente = guardar_agente(client, "dev", {
    "name": "taller-dev-de-guardia",
    "model": MODELO,
    "system": (
        "Eres un desarrollador Python senior. Trabajas en una terminal Linux. "
        "Antes de cambiar código, reproduces el fallo. Haces el cambio más pequeño que "
        "lo arregla y lo compruebas corriendo los tests. Nunca cambias un test para que pase. "
        "Responde en español."
    ),
    "tools": [{
        "type": "agent_toolset_20260401",
        # Mínimo privilegio: este trabajo no necesita internet.
        "configs": [
            {"name": "web_fetch", "enabled": False},
            {"name": "web_search", "enabled": False},
        ],
    }],
})

# Los archivos del repo se suben con la Files API y quedan de solo lectura en la sesión.
archivos = [p for p in sorted(REPO.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
subidos = [subir_archivo(client, p) for p in archivos]
recursos = [
    {"type": "file", "file_id": f, "mount_path": f"facturador/{p.relative_to(REPO)}"}
    for f, p in zip(subidos, archivos)
]
origen = "/mnt/session/uploads/facturador (solo lectura: cópialo a /workspace/facturador y trabaja allá)"

PEDIDO = f"""\
Los tests del repo facturador fallan. El repo está en {origen}.
Las reglas de negocio están en su README.md.

1. Corre los tests y encuentra la causa de cada fallo.
2. Arregla el código sin tocar tests/.
3. Deja en /mnt/session/outputs/:
   - parche.diff: un diff unificado con rutas relativas a la raíz del repo
     (a/facturador/factura.py, b/facturador/factura.py), que se pueda aplicar con git apply.
   - explicacion.md: máximo 8 líneas. Qué estaba mal, por qué, y cómo lo comprobaste."""

sesion = client.beta.sessions.create(
    agent=agente, environment_id=entorno, title="caso 1 · bug del viernes", resources=recursos,
)
print(f"sesión {sesion.id}\n")

resultado = conversar(client, sesion.id, PEDIDO)
print(f"\nterminó: {resultado.motivo}")
salidas = bajar_salidas(client, sesion.id, subidos=tuple(subidos))
print(resumen_costo(client, sesion.id))
print(f"mírala paso a paso en https://platform.claude.com/sessions/{sesion.id}")

# ── Confía, pero verifica: el parche se prueba en tu máquina, no en la del agente ──
parche = next((p for p in salidas if p.name == "parche.diff"), None)
if parche is None:
    print("\nNo llegó parche.diff. Pídeselo al agente en la Console o vuelve a correr el caso.")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmp:
    copia = Path(tmp) / "facturador"
    shutil.copytree(REPO, copia, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    aplicado = subprocess.run(["git", "apply", "--verbose", str(parche)], cwd=copia, capture_output=True, text=True)
    if aplicado.returncode != 0:
        print(f"\nEl parche no aplica limpio:\n{aplicado.stderr}")
        sys.exit(1)
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=copia,
                           capture_output=True, text=True)
    print("\n── Tests en tu máquina con el parche aplicado ──")
    print(tests.stdout.strip().splitlines()[-1] if tests.stdout.strip() else tests.stderr)
    if tests.returncode == 0:
        print(f"Si te convence, aplícalo de verdad: git apply --directory=repo-facturador {parche.relative_to(RAIZ)}")
