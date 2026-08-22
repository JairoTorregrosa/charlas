# Notebooks · una palanca por celda

Cuatro notebooks, la misma pregunta (*¿Cómo cambió el margen por proyecto de junio a julio, y por qué?*), el mismo CSV sintético (`workspace/contabilidad.csv`) y el mismo modelo (`claude-sonnet-5`). Cada celda añade una palanca: empieza el modelo solo y termina un MVP. Las salidas guardadas son ejecuciones reales.

| Notebook | Superficie | Escalera |
|---|---|---|
| `00-messages-api.ipynb` | Messages API | solo el modelo → + system prompt → + una tool (sin loop) → + loop |
| `01-agent-sdk.ipynb` | Claude Agent SDK (Python) | + system prompt → + Bash → + Read/Glob/Grep → + WebSearch → + skill → + CLAUDE.md → tool propia + salida JSON + presupuesto |
| `02-claude-code-cli.ipynb` | `claude -p` (flags) | la misma escalera en flags → `--output-format json` |
| `03-managed-agents.ipynb` | Managed Agents | solo el modelo → + system → + bash y archivo montado → + toolset + skill → custom tool del cliente → archivar |

Equivalencia con `pi`: `-nt` ≈ sin tools · `-ns` ≈ sin skills · `-ne` ≈ sin MCP · `-nc` ≈ sin CLAUDE.md (cada notebook lo dice con sus nombres).

## Correr
```
export ANTHROPIC_API_KEY=...
export MANAGED_ENV_ID=env_...      # solo 03 (Console → Managed Agents → Environments)
cd notebooks
uv sync && uv run jupyter lab
```
`02` y el SDK de `01` usan el `claude` instalado en la máquina (Claude Code ≥ 2.1). Los notebooks `01` y `02` borran y reescriben `workspace/CLAUDE.md` (está en `.gitignore`): la escalera empieza sin contexto de proyecto.

## Workspace
- `workspace/contabilidad.csv`: sintético, mismo que `slides/demo/`. Historia: proyecto 2210 sube ~10 pp, 1045 baja ~22 pp, 3322 plano.
- `workspace/.claude/skills/margen-por-proyecto/SKILL.md`: reglas contables + método. Es la palanca "skill" en los tres entornos (en Managed Agents se sube con `client.skills.create`).
- `workspace/out/`: lo que escriben las tools propias (ignorado por git).
