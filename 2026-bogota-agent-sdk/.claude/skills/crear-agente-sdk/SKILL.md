---
name: crear-agente-sdk
description: Wizard que crea un agente nuevo con la Claude Agent SDK en Python o TypeScript. Pregunta paso a paso con AskUserQuestion y diagramas ASCII (idea, objetivo, lenguaje, datos, skill, guardrails), muestra un plano, genera el agente con su workspace, sus guardrails (permisos, hook, topes) y su bitácora de eventos y transcript, y lo corre una vez. Se usa cuando alguien pide crear, diseñar o hacer brainstorming de un agente ("crea un agente", "hazme un agente que...", "agente con el Agent SDK", "claude-agent-sdk", "automatiza esto con un agente", /crear-agente-sdk) o pregunta cómo elegir entre tool, MCP, skill, subagente y hook. No aplica a Claude Managed Agents, a llamadas sueltas a la Messages API ni a subagentes de Claude Code (.claude/agents).
---

# Crear un agente con la Claude Agent SDK

El SDK pone el loop. Tú decides con la persona tres cosas y las escribes: el **system prompt**, las **tools y el workspace** (tools nativas, tools propias, MCP, skills, archivos) y los **guardrails** (permisos, hooks, topes). Sirve igual para Python y para TypeScript.

Este archivo es el mapa. El detalle de cada fase vive en `references/`: abre el archivo de la fase cuando llegues a ella, completo, y no antes.

## Flujo

Copia este checklist en tu respuesta y márcalo a medida que avanzas:

```
- [ ] 1. Wizard          → lee references/wizard.md y references/diagramas.md
- [ ] 2. Plano ASCII confirmado por la persona
- [ ] 3. Construcción    → lee references/construccion.md + el ejemplo de cada pieza elegida
- [ ] 4. Corrida y validación → lee references/validacion.md
- [ ] 5. Si algo falló   → references/gotchas.md, arregla, vuelve al paso 4
- [ ] 6. Entrega con rutas, comando, recibo y plano final
```

## Qué abrir y cuándo

| Fase o pregunta | Abre |
|---|---|
| Conducir el wizard con AskUserQuestion, qué preguntar y con qué opciones | `references/wizard.md` |
| Diagramas ASCII para los `preview` y para explicar conceptos | `references/diagramas.md` |
| La persona llega sin idea o con una vaga; MCP reales con URL y auth; skill y guardrail por familia | `references/ideas.md` |
| «¿Tool, MCP, skill, subagente o hook?» | `references/conceptos.md` |
| Qué pieza usar, qué archivos generar, reglas que no se negocian | `references/construccion.md` |
| Subagentes, MCP por stdio, `resume`, correr sin humano | `references/piezas.md` |
| Correr, validar las cuatro comprobaciones y entregar | `references/validacion.md` |
| Un síntoma de error en la corrida | `references/gotchas.md` |
| System prompts, esquemas de tools y datos de ejemplo de nueve agentes pequeños | `references/ejemplos/managed_agents_ideas.py` |

Plantillas para copiar y rellenar (marcas `TODO`): `assets/agente.py`, `assets/agente.ts`, `assets/observar.py`, `assets/observar.ts`, `assets/pyproject.toml`, `assets/package.json`, `assets/tsconfig.json`, `assets/SKILL.plantilla.md`.

## Ejemplos verificados

Lee completo el archivo de la pieza que vas a escribir, en el lenguaje elegido. Copia la forma, cambia el contenido.

| Pieza | Python (`references/ejemplos/python/`) | TypeScript (`references/ejemplos/typescript/`) |
|---|---|---|
| Un prompt, un resultado | `01_query.py` | `01_query.ts` |
| Ver cada mensaje del loop | `02_stream.py` | `02_stream.ts` |
| Tool propia | `03_tool.py` | `03_tool.ts` |
| MCP externo por stdio | `04_mcp.py` + `gmail_mcp.py` | `04_mcp.ts` + `gmail_mcp.ts` |
| Skill del agente | `05_skill.py` | `05_skill.ts` |
| Permisos + hook `PreToolUse` | `06_permisos_hooks.py` | `06_permisos_hooks.ts` |
| Subagente | `07_subagente.py` | `07_subagente.ts` |
| Todo junto, con topes y bitácora | `08_agente_vuelo.py` | `08_agente_vuelo.ts` |
| Varios turnos con `resume` | `09_conversar.py` | `09_conversar.ts` |

## Lo que nunca se salta

1. **Una decisión por pregunta**, con AskUserQuestion y un diagrama ASCII en el `preview`. Sin humano o con «decide tú»: opciones recomendadas.
2. **Bitácora siempre**: cada corrida guarda todos los eventos crudos en `salidas/<fecha-hora>/eventos.jsonl` y un `transcript.md` llamada por llamada. Son agentes para aprender.
3. **Topes y aislamiento siempre**: `max_turns`, `max_budget_usd`, `strict_mcp_config`, `setting_sources` explícito, memoria automática desactivada. Nunca `bypassPermissions`.
4. **Acciones hacia afuera solo como borrador**: enviar, publicar, pagar o comprar requieren aprobación humana.
5. **No se declara terminado sin una corrida exitosa** y el transcript leído.
