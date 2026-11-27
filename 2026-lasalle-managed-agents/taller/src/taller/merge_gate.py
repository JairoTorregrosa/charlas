"""La regla de auto-merge de bajo riesgo, en código y no en el prompt.

El agente pide `merge_pull_request` y la sesión se pausa (always_ask). Este
módulo decide. Si la regla viviera en el system prompt, una instrucción
inyectada en el repo (un README, un issue, un comentario) podría saltársela.

Se aprueba solo si se cumple todo:
- el PR está abierto, viene de una rama vuln-patcher/* del mismo repo;
- solo toca archivos de dependencias, fuera de .github/;
- cambia 40 líneas o menos;
- ningún salto de versión es major (ni minor en 0.x);
- expectedHeadSha es el commit actual del PR, y todos los checks del CI pasaron.
"""
import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

PREFIJO_RAMA = "vuln-patcher/"
MAX_LINEAS = 40
ARCHIVOS_DEPENDENCIAS = {
    "requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock",
    "package.json", "package-lock.json", "bun.lock", "pnpm-lock.yaml", "yarn.lock",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
}
CONCLUSIONES_OK = {"success", "neutral", "skipped"}

_VERSION = re.compile(r'(?:version\s*=\s*|"version"\s*:\s*|"[^"]+"\s*:\s*|[=@~^<>]=?\s*)"?(\d+\.\d+[0-9A-Za-z.+-]*)')


@dataclass
class Veredicto:
    permitido: bool
    motivo: str = ""


def _no(motivo: str) -> Veredicto:
    return Veredicto(False, motivo)


def _mayor_menor(version: str) -> tuple[int, int] | None:
    m = re.match(r"(\d+)\.(\d+)", version)
    return (int(m[1]), int(m[2])) if m else None


def salto_rompe(de: str, a: str) -> bool:
    """Rompe si cambia el major, o el minor estando en 0.x (semver)."""
    x, y = _mayor_menor(de), _mayor_menor(a)
    if x is None or y is None:
        return True
    return x[0] != y[0] or (x[0] == 0 and x[1] != y[1])


def saltos_que_rompen(parche: str) -> list[str]:
    """Empareja cada versión quitada con la siguiente agregada en el mismo hunk."""
    rompen, quitadas = [], []
    for linea in parche.splitlines():
        if linea.startswith("@@"):
            quitadas.clear()
            continue
        m = _VERSION.search(linea[1:])
        if not m:
            continue
        if linea.startswith("-"):
            quitadas.append(m[1])
        elif linea.startswith("+") and quitadas:
            de = quitadas.pop(0)
            if salto_rompe(de, m[1]):
                rompen.append(f"{de} -> {m[1]}")
    return rompen


def evaluar_pr(pr: dict[str, Any], archivos: list[dict[str, Any]]) -> Veredicto:
    if pr["state"] != "open" or pr.get("draft"):
        return _no("el PR no está abierto y listo")
    if pr["head"]["repo"]["full_name"] != pr["base"]["repo"]["full_name"]:
        return _no("el PR viene de un fork")
    if not pr["head"]["ref"].startswith(PREFIJO_RAMA):
        return _no(f"la rama no es {PREFIJO_RAMA}*")
    if not archivos:
        return _no("el PR no cambia archivos")
    otros = [a["filename"] for a in archivos
             if a["filename"].rsplit("/", 1)[-1] not in ARCHIVOS_DEPENDENCIAS or a["filename"].startswith(".github/")]
    if otros:
        return _no(f"toca código, no solo dependencias: {', '.join(otros)}")
    lineas = sum(a["additions"] + a["deletions"] for a in archivos)
    if lineas > MAX_LINEAS:
        return _no(f"cambia {lineas} líneas (máximo {MAX_LINEAS})")
    for a in archivos:
        if "patch" not in a:
            return _no(f"no hay diff para {a['filename']}")
        rompen = saltos_que_rompen(a["patch"])
        if rompen:
            return _no(f"salto que rompe compatibilidad en {a['filename']}: {', '.join(rompen)}")
    return Veredicto(True)


def evaluar_checks(checks: list[dict[str, Any]]) -> Veredicto:
    if not checks:
        return _no("el commit no tiene checks de CI")
    corriendo = [c for c in checks if c["status"] != "completed"]
    if corriendo:
        return _no(f"{len(corriendo)} check(s) siguen corriendo")
    fallaron = [c["name"] for c in checks if c.get("conclusion") not in CONCLUSIONES_OK]
    if fallaron:
        return _no(f"no pasaron: {', '.join(fallaron)}")
    return Veredicto(True)


def _github(ruta: str, token: str) -> Any:
    pedido = urllib.request.Request(f"https://api.github.com{ruta}", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(pedido, timeout=20) as r:
        return json.load(r)


def decidir_merge(entrada: dict[str, Any], repo_permitido: str, token: str) -> Veredicto:
    """Decide una llamada a merge_pull_request. Solo lee de GitHub."""
    owner, repo, numero = entrada.get("owner"), entrada.get("repo"), entrada.get("pullNumber")
    sha = entrada.get("expectedHeadSha")
    if not isinstance(owner, str) or not isinstance(repo, str) or not isinstance(numero, int):
        return _no("a la llamada le falta owner, repo o pullNumber")
    if f"{owner}/{repo}".lower() != repo_permitido.lower():
        return _no(f"{owner}/{repo} no es el repo de este barrido")
    # Con el SHA fijo, GitHub rechaza el merge si llega un commit después de esta revisión.
    if not isinstance(sha, str):
        return _no("la llamada tiene que traer expectedHeadSha")
    pr = _github(f"/repos/{owner}/{repo}/pulls/{numero}", token)
    if pr["head"]["sha"] != sha:
        return _no("expectedHeadSha no es el commit actual del PR")
    archivos = _github(f"/repos/{owner}/{repo}/pulls/{numero}/files?per_page=100", token)
    veredicto = evaluar_pr(pr, archivos)
    if not veredicto.permitido:
        return veredicto
    checks = _github(f"/repos/{owner}/{repo}/commits/{sha}/check-runs?per_page=100", token)["check_runs"]
    return evaluar_checks(checks)
