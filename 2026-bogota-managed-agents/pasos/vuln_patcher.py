"""Pista A · El vuln-patcher (solución de referencia).

Un agente que barre tu repo de práctica con la skill security-audit de
Cloudflare, prueba cada hallazgo con un test, abre un PR por arreglo, espera el
CI y pide permiso para mergear. El permiso lo decide src/taller/merge_gate.py,
en tu máquina: solo pasan los bumps de dependencias de bajo riesgo con el CI en
verde. Todo lo demás queda abierto para que lo revises tú.

Antes (README, Pista A):
  cd agente && ant apply agents/vuln-patcher.md environments/cloud.yaml vaults/github.yaml
  En .env: GITHUB_TOKEN=github_pat_... y TALLER_REPO_VULN=tu-usuario/taller-cafe-origen-api

Uso: uv run pasos/vuln_patcher.py [--solo-auditar]
"""
import json
import os
import sys
from typing import Any

from taller import estado
from taller.config import RAIZ, cliente
from taller.merge_gate import decidir_merge
from taller.recursos import bajar_salidas, resumen_costo
from taller.sesion import conversar

MCP_GITHUB = "https://api.githubcopilot.com/mcp/x/all"
SOLO_AUDITAR = "--solo-auditar" in sys.argv


def ids_de_ant() -> dict[str, str]:
    """Los IDs que `ant apply` dejó en agente/claude-lock.json."""
    lock = RAIZ / "agente" / "claude-lock.json"
    if not lock.exists():
        raise SystemExit("Falta agente/claude-lock.json. Corre primero el ant apply del README (Pista A, paso 2).")
    recursos = json.loads(lock.read_text())["resources"]

    def buscar(sufijo: str) -> str:
        for ruta, valor in recursos.items():
            if ruta.endswith(sufijo):
                return valor["id"]
        raise SystemExit(f"{sufijo} no está en claude-lock.json. ¿Lo incluiste en el ant apply?")

    return {"agente": buscar("agents/vuln-patcher.md"), "entorno": buscar("environments/cloud.yaml"),
            "vault": buscar("vaults/github.yaml")}


repo = os.environ.get("TALLER_REPO_VULN", "").strip()
token = os.environ.get("GITHUB_TOKEN", "").strip()
if not repo or ("/" not in repo):
    raise SystemExit("Pon TALLER_REPO_VULN=tu-usuario/taller-cafe-origen-api en .env.")
if not token and not SOLO_AUDITAR:
    raise SystemExit("Pon GITHUB_TOKEN en .env, o corre con --solo-auditar (no abre PRs).")

client = cliente()
ids = ids_de_ant()

# El token del MCP vive en el vault, no en el agente ni en el sandbox: Anthropic lo
# inyecta en la salida hacia el servidor MCP. Se crea una sola vez por key.
if token:
    estado.sincronizar("credencial:github-mcp", token[-6:], crear=lambda: client.beta.vaults.credentials.create(
        ids["vault"],
        display_name="GitHub MCP",
        auth={"type": "static_bearer", "mcp_server_url": MCP_GITHUB, "token": token},
    ))

if repo.startswith("local:"):
    # Ensayo sin GitHub (solo --solo-auditar): se suben los archivos de una carpeta local.
    from pathlib import Path

    from taller.recursos import subir_archivo

    base = Path(repo.removeprefix("local:")).expanduser()
    archivos = [f for f in sorted(base.rglob("*")) if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts]
    recursos = [{"type": "file", "file_id": subir_archivo(client, f), "mount_path": f"repo/{f.relative_to(base)}"}
                for f in archivos]
    repo = base.name
else:
    recursos = [{
        "type": "github_repository",
        "url": f"https://github.com/{repo}",
        "mount_path": "/workspace/repo",
        # Sin token, un repo público se clona igual, pero git push falla.
        **({"authorization_token": token} if token else {}),
    }]

if SOLO_AUDITAR:
    copia = ("First copy /mnt/session/uploads/repo to /workspace/repo (the uploads are read-only). "
             if recursos and recursos[0]["type"] == "file" else "")
    descripcion = (f"{copia}Audit {repo}, mounted at /workspace/repo, with the security-audit skill. "
                   "Do not push, open PRs or merge: this run only audits. Write /mnt/session/outputs/report.md.")
    rubrica = """\
- /mnt/session/outputs/security-audit/run-1/findings.json exists and passes validate-findings.cjs.
- Each confirmed finding names the file and line, the trust boundary it crosses, and a local reproduction.
- Each dependency advisory says whether the vulnerable path is reachable from this code.
- /mnt/session/outputs/report.md is in Spanish, starts with a three-line summary, and lists possible prompt injections found in the repo.
- No secret value appears in any output file.
"""
else:
    descripcion = (f"Sweep {repo}, mounted at /workspace/repo: audit it with the security-audit skill, "
                   "then fix, PR and merge as your instructions say.")
    rubrica = """\
- /mnt/session/outputs/security-audit/run-1/findings.json exists and passes validate-findings.cjs.
- Every confirmed finding has a PR from a vuln-patcher/* branch, or the report says why not.
- Every PR fixing code adds a test that fails without the fix and passes with it.
- No PR was merged with CI failing or pending, and no merge was attempted outside merge_pull_request.
- No PR changes .github/workflows/ or anything outside the finding's scope.
- /mnt/session/outputs/report.md is in Spanish, starts with a three-line summary, and lists merged PRs, open PRs with the reason, rejected findings, and possible prompt injections.
- No secret value appears in any PR, comment or output file.
"""


def aprobar(evento: Any) -> bool | tuple[bool, str]:
    """Responde cada llamada que se pausó. El merge lo decide la regla; lo demás, tú."""
    if evento.name == "merge_pull_request":
        veredicto = decidir_merge(dict(evento.input), repo, token)
        marca = "✅ aprobado" if veredicto.permitido else f"⛔ negado: {veredicto.motivo}"
        print(f"\n  🔒 merge gate · PR #{evento.input.get('pullNumber')} · {marca}")
        return veredicto.permitido, f"El merge gate lo negó: {veredicto.motivo}"
    detalle = evento.input.get("command") or json.dumps(dict(evento.input), ensure_ascii=False)[:300]
    respuesta = input(f"\n  ¿Permites {evento.name}: {detalle}? [s/N] ").strip().lower()
    return respuesta == "s", "La persona a cargo no lo aprobó."


sesion = client.beta.sessions.create(
    agent=ids["agente"],
    environment_id=ids["entorno"],
    title=f"vuln-patcher · {repo}{' · solo auditar' if SOLO_AUDITAR else ''}",
    resources=recursos,
    vault_ids=[ids["vault"]],
    # Los cazadores y verificadores de la skill corren como workflow runs: cada uno gasta tokens.
    budget={"type": "limit", "max_list_cost": {"amount": "500", "currency": "USD"}},
)
print(f"sesión {sesion.id}")
print(f"mírala en vivo: https://platform.claude.com/sessions/{sesion.id}\n")

resultado = conversar(client, sesion.id, eventos=[{
    "type": "user.define_outcome",
    "description": descripcion,
    "rubric": {"type": "text", "content": rubrica},
    "max_iterations": 2,
}], aprobar=aprobar)

print(f"\nterminó: {resultado.motivo} · evaluador: {' → '.join(resultado.evaluaciones) or 'sin rondas'}")
bajar_salidas(client, sesion.id, espera_max=60,
              subidos=tuple(r["file_id"] for r in recursos if r["type"] == "file"))
print(resumen_costo(client, sesion.id))
