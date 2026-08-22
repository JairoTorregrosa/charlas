# 2026 · Construye tu primer agente de AI con Claude

Charla de apertura del *Bogotá | Claude Workshop | AI Agents for business analytics competition* (Claude Community Bogotá, oficinas de Quick, 22 de agosto de 2026). Una hora: qué es un agente, cómo piensa por dentro, las tres palancas (system prompt, tools, contexto) y dónde corre hoy con el stack de Claude.

## Qué hay aquí

| Carpeta | Qué es |
|---|---|
| [`slides/`](slides/) | El deck (HTML puro, 23 slides, modo presentador con notas). `python3 -m http.server 3030 --directory slides` |
| [`slides/demo/`](slides/demo/) | Las demos: `agent.py` (el loop en ~100 líneas, Messages API), `managed.py` (Managed Agents), `CLAUDE.md` (contexto para Claude Code), `contabilidad.csv` (sintético) y el `RUNBOOK.md` con los comandos exactos |
| [`notebooks/`](notebooks/) | Cuatro notebooks ejecutados, una palanca por celda: Messages API, Claude Agent SDK, `claude -p`, Managed Agents. Mismo CSV, mismo modelo (`claude-sonnet-5`), salidas reales |

## La pregunta que resuelven todos
> ¿Cómo cambió el margen por proyecto de junio a julio, y por qué?

Sobre `contabilidad.csv` (PUC colombiano, `;` y decimal con coma): ingresos en cuentas 4, costos en 6 y 7. La historia plantada: el proyecto 2210 sube ~10 pp, el 1045 baja ~22 pp (nómina), el 3322 queda plano.

## Correr
- Deck: `python3 -m http.server 3030 --directory slides` → http://localhost:3030/ (`?presenter=1` para las notas).
- Demos y notebooks: `export ANTHROPIC_API_KEY=...` (y `MANAGED_ENV_ID=env_...` para Managed Agents, se crea en la Console). Notebooks: `cd notebooks && uv sync && uv run jupyter lab`.

Comunidad: grupo de WhatsApp *Claude Code Colombia* (QR en la última slide).
