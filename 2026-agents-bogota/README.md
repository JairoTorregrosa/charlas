<!-- ficha:inicio · lo escribe scripts/catalogo.py desde charlas.toml · no lo edites a mano -->
# Construye tu primer agente de AI con Claude

<a href="Construye-tu-primer-agente-Bogota-2026.pdf"><img src="portada.jpg" alt="Portada del deck «Construye tu primer agente de AI con Claude»" width="100%"></a>

<table>
<tr><td>📅 <b>Cuándo</b></td><td>22 de agosto de 2026</td></tr>
<tr><td>📍 <b>Dónde</b></td><td>Oficinas de Quick · Bogotá</td></tr>
<tr><td>🎤 <b>Formato</b></td><td>Charla · 1 h</td></tr>
<tr><td>🎟️ <b>Evento</b></td><td><a href="https://luma.com/claude-imxl">Claude Community Bogotá · hackathon de analítica con Quick</a> · Luma</td></tr>
<tr><td>📑 <b>Deck</b></td><td><a href="Construye-tu-primer-agente-Bogota-2026.pdf">23 slides en PDF</a> · <a href="https://github.com/JairoTorregrosa/charlas/raw/main/2026-agents-bogota/Construye-tu-primer-agente-Bogota-2026.pdf">descargar</a></td></tr>
<tr><td>🧪 <b>Demo</b></td><td><a href="demo">demo/</a> · <a href="notebooks">notebooks/</a> · <a href="hackathon">hackathon/</a></td></tr>
</table>

<details>
<summary>👀 Las 23 slides de un vistazo</summary>

<a href="Construye-tu-primer-agente-Bogota-2026.pdf"><img src="vistazo.jpg" alt="Las 23 slides del deck en miniatura" width="100%"></a>

</details>

<sub><a href="../README.md">← Todas las charlas</a> · anterior: <a href="../2026-hapgj/">Crea tu Web con IA</a> · siguiente: <a href="../2026-casanare-marley/">Mi agente personal: la IA que crece contigo</a></sub>
<!-- ficha:fin -->

Charla de apertura del hackathon de analítica con Quick. Una pregunta y un CSV, de principio a fin:

> ¿Cómo cambió el margen por proyecto de junio a julio, y por qué?

## Tres palancas, una por versión

| Versión | Palanca que entra | Qué responde el agente |
|---|---|---|
| v1 | **system prompt** · objetivo, reglas y formato de salida | Con método. Sin datos, sin cifra. |
| v2 | **tool** · `calcular_margen(proyecto, mes)` | La cifra y el cálculo. |
| v3 | **skill** · `margen-por-proyecto`, con cuándo usarla, pasos y reglas | Cifra, cálculo y causa. |

## El mismo loop, en tres lugares

| | Claude Code | Agent SDK | Managed Agents |
|---|---|---|---|
| corre en | tu computador | tu aplicación | Anthropic |
| system prompt | `CLAUDE.md` + `--append-system-prompt` | `system_prompt=` | `system=` |
| tools | integradas + MCP | `@tool` + MCP | toolset + MCP |
| skills | `.claude/skills/` | `skills=` | skills adjuntas |

## Qué hay aquí

| Carpeta | Qué es |
|---|---|
| [`demo/`](demo/) | Las demos de la charla: `agent.py` (el loop en ~100 líneas, Messages API), `managed.py` (Managed Agents), `CLAUDE.md` (contexto para Claude Code), `contabilidad.csv` (sintético) y el [`RUNBOOK.md`](demo/RUNBOOK.md) con los comandos exactos. |
| [`notebooks/`](notebooks/) | Cuatro notebooks ejecutados, una palanca por celda: Messages API, Claude Agent SDK, `claude -p` y Managed Agents. Mismo CSV, mismo modelo (`claude-sonnet-5`), salidas reales. |
| [`hackathon/`](hackathon/) | El reto tal como lo recibieron los equipos: las 7 preguntas, las convenciones contables, cómo se entregaba y cómo se puntuaba. |

`contabilidad.csv` usa el PUC colombiano, `;` y decimal con coma: ingresos en cuentas 4, costos en 6 y 7. La historia plantada: el proyecto 2210 sube ~10 pp, el 1045 baja ~22 pp (nómina) y el 3322 queda plano.

## Córrelo

```
export ANTHROPIC_API_KEY=...
export MANAGED_ENV_ID=env_...      # solo para Managed Agents; se crea en la Console
cd notebooks && uv sync && uv run jupyter lab
```

> El leaderboard del hackathon (`quick-golden-bench.vercel.app`) ya no está en línea. Las instrucciones de entrega quedan como registro.

Comunidad: grupo de WhatsApp *Claude Code Colombia* (QR en la última slide).
