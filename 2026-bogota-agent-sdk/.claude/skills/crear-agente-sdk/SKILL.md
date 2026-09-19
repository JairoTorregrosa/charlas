---
name: crear-agente-sdk
description: Wizard para crear un agente nuevo con la Claude Agent SDK, en Python o en TypeScript. Pregunta paso a paso con AskUserQuestion y diagramas ASCII (idea, objetivo, lenguaje, datos, skill, guardrails), propone un plano y lo construye. Úsala cuando pidan "crea un agente", "hazme un agente que...", "agente con el Agent SDK", "claude-agent-sdk", "automatiza esto con un agente" o /crear-agente-sdk. Genera el archivo del agente, su carpeta de trabajo con skills, sus tools, sus guardrails (permisos, hook, topes) y lo corre una vez. No la uses para Claude Managed Agents, para llamadas sueltas a la Messages API ni para configurar subagentes de Claude Code (.claude/agents).
---

# Crear un agente con la Claude Agent SDK

Tú no escribes el loop: lo pone el SDK. Escribes tres cosas, y este wizard las decide contigo una por una.

| Pieza | Qué es | Dónde queda |
|---|---|---|
| System prompt | quién es el agente y qué no debe adivinar | constante en el archivo del agente |
| Tools y workspace | tools nativas, tools propias, MCP, skills y archivos | opciones del `query()` y `workspace/` junto al agente |
| Guardrails | permisos, hooks y topes | opciones del `query()` |

## 1. Wizard: siete pasos, uno por pregunta

Conduce la creación como un wizard. En cada paso usa la tool **AskUserQuestion**: una pregunta, de dos a cuatro opciones, la recomendada primero con «(Recomendado)», y un `preview` con un diagrama ASCII que muestre cómo queda el agente con esa opción. Los diagramas base están en `references/diagramas.md`: adáptalos con los nombres reales del agente de la persona. Antes de cada pregunta escribe una o dos líneas que expliquen qué se decide y por qué importa; después de cada respuesta confirma en una línea lo que quedó.

Salta los pasos que el pedido ya responde. Si la persona dice «decide tú» o estás corriendo sin humano (`claude -p`), elige la opción recomendada en todos y sigue. Si AskUserQuestion no está disponible, haz la misma pregunta en texto con las opciones numeradas y el diagrama en un bloque de código.

| Paso | Pregunta | Opciones típicas | Diagrama |
|---|---|---|---|
| 0 · Idea | ¿Qué agente quieres? Solo si llega sin idea o con una vaga («de ventas», «automatizar mi trabajo») | 3–4 primeros agentes pequeños tomados de `references/ideas.md`, de la familia más cercana | Arquitecturas por familia |
| 1 · Objetivo | ¿Cuál de estas frases describe lo que debe resolver? | 2–3 redacciones del objetivo en una frase, de la más pequeña a la más ambiciosa. Recomienda la pequeña | El loop, con su pedido y su resultado |
| 2 · Lenguaje | ¿Python o TypeScript? No preguntes si la carpeta ya tiene `pyproject.toml` o `package.json` | Python (uv) · TypeScript (Node o bun) | — (usa `preview` con las 8 primeras líneas del agente en cada lenguaje) |
| 3 · Cómo corre | ¿Una vez y sale, o conversación? | Una vez y sale (Recomendado) · Conversación con `resume` | «cómo corre» |
| 4 · Datos y acciones | ¿De dónde salen los datos? (multiSelect) | Archivos locales de ejemplo (Recomendado) · Tool propia · MCP externo · Web | «de dónde salen los datos» |
| 5 · Procedimiento | ¿El agente debe seguir siempre los mismos pasos? | Sí, con una skill (Recomendado) · No, que decida | «procedimiento» |
| 6 · Guardrails | ¿Qué no debe hacer nunca? (multiSelect) | Solo lectura (Recomendado) · Acciones hacia afuera solo como borrador · Bloquear por argumentos con un hook · Lista blanca de dominios | «guardrails» |
| 7 · Subagente | Solo si el trabajo llena el contexto de material que el principal no necesita | Sin subagente (Recomendado) · Con subagente | «subagente, sí o no» |

Cierra el wizard con un **plano** antes de escribir código: un diagrama ASCII del agente final con sus tools, su skill y sus guardrails reales, y la lista de archivos que vas a crear. Pide confirmación con una última AskUserQuestion: «Construirlo así (Recomendado)» · «Cambiar algo».

Si el objetivo se resuelve con pasos fijos y conocidos, dilo en el paso 1: eso es un script o un workflow, y un agente sale más caro y menos predecible. Sigue solo si la persona confirma.

### Usa los diagramas también para explicar

Cuando la persona pregunte «¿qué es un hook?», «¿tool o MCP?», «¿por qué una skill?», responde con el diagrama correspondiente de `references/diagramas.md` y la tabla de `references/conceptos.md`, y aterrízalo en su agente. Al entregar, vuelve a dibujar el plano con lo que de verdad quedó.

## 2. Decide las piezas

Referencias que debes abrir antes de escribir código, según lo elegido:

| Necesitas | Abre |
|---|---|
| Un punto de partida para la idea (tools, MCP reales con URL y auth, skill, guardrail) | `references/ideas.md` |
| Código verificado de cada pieza, en el lenguaje elegido | `references/ejemplos/README.md` → `ejemplos/python/0N_*.py` o `ejemplos/typescript/0N_*.ts` |
| System prompts, esquemas de tools y datos de ejemplo de nueve agentes pequeños | `references/ejemplos/managed_agents_ideas.py` |
| Elegir entre tool, MCP, skill, subagente y hook | `references/conceptos.md` |
| Subagentes, MCP por stdio, `resume`, correr sin humano | `references/piezas.md` |
| Un error en la corrida | `references/gotchas.md` |

- **Tools nativas** (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebSearch`, `WebFetch`): declara en `tools` solo las que el objetivo exige. `tools=[]` deja al agente sin manos.
- **Tool propia**: para datos o acciones de tu código. Una función con nombre, descripción y esquema. Va dentro de un servidor MCP en proceso (`create_sdk_mcp_server` / `createSdkMcpServer`) y se llama `mcp__<servidor>__<tool>`.
- **MCP externo**: tools que hizo otro. Decláralo inline en `mcp_servers`. No lo pongas en `.mcp.json`: con `strict_mcp_config` ese archivo se ignora.
- **Skill**: un procedimiento que el agente debe seguir igual cada vez. `workspace/.claude/skills/<nombre>/SKILL.md`. Exige `setting_sources=["project"]`, `skills=["<nombre>"]` y `"Skill"` dentro de `tools`; sin la tool `Skill` el agente ve la skill y no puede abrirla.
- **Datos de ejemplo**: crea tú los archivos en `workspace/datos/` (8–12 filas, con dos o tres trampas que obliguen al agente a leer de verdad) y dilo en la entrega. El sistema real se conecta después.
- **Subagente**: solo cuando una parte del trabajo llena el contexto de papeles que el principal no necesita (leer veinte archivos para devolver una línea). Detalles en `references/piezas.md`.

## 3. Genera los archivos

Copia la plantilla del lenguaje elegido y rellena las marcas `TODO`:

- Python: `assets/agente.py` + `assets/observar.py` + `assets/pyproject.toml`
- TypeScript: `assets/agente.ts` + `assets/observar.ts` + `assets/package.json` + `assets/tsconfig.json`
- Skill del agente (si aplica): `assets/SKILL.plantilla.md` → `workspace/.claude/skills/<nombre>/SKILL.md`

Estructura de salida, en una carpeta nueva con el nombre del agente:

```
<nombre-del-agente>/
  agente.py | agente.ts
  observar.py | observar.ts       # la bitácora: cópiala tal cual de assets/
  pyproject.toml | package.json + tsconfig.json
  workspace/.claude/skills/<skill>/SKILL.md
  salidas/<fecha-hora>/           # eventos.jsonl + transcript.md, una carpeta por corrida
```

Dentro del kit del workshop no crees proyecto nuevo: deja el archivo junto a los `0N_*.py` o `0N_*.ts` y reutiliza su `pyproject.toml` o `package.json`.

## 4. Reglas que no se negocian

0. **Observabilidad siempre**: estos agentes son para aprender. Cada corrida guarda TODOS los eventos del SDK, crudos, en `eventos.jsonl` (se escribe evento por evento, así una caída no borra nada) y un `transcript.md` que muestra, llamada por llamada al LLM, qué papeles nuevos entraron al contexto, cuántos tokens leyó y qué respondió. Nunca generes un agente sin la `Bitacora`, nunca filtres eventos antes de guardarlos y nunca la quites para «simplificar».
1. **Topes siempre**: `max_turns` y `max_budget_usd` (`maxTurns`, `maxBudgetUsd`). Empieza en 12 turns y USD 0.25.
2. **Aislamiento siempre**: `strict_mcp_config=True` y `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` en `env`. Sin lo primero, con sesión de suscripción el agente carga los conectores reales de claude.ai (Gmail, Drive) de quien lo corre. En TypeScript `env` reemplaza el entorno entero: esparce `...process.env`.
3. **`setting_sources` explícito**: `[]` si no hay skills; `["project"]` si las hay. Nunca heredes la configuración personal.
4. **Tres listas distintas**: `tools` define qué existe; `allowed_tools` qué corre sin preguntar; `disallowed_tools` qué nunca corre. `allowed_tools` no restringe nada.
5. **Nunca `bypassPermissions`** en un agente generado. Para correr sin humano usa `permission_mode="dontAsk"`: lo que no esté aprobado se niega y el agente busca otra ruta.
6. **Hook cuando la regla depende de los argumentos** (qué archivo, qué id, qué comando). El motivo del `deny` lo lee el LLM: escríbelo como instrucción. Un hook que devuelve `allow` no salta las reglas `deny`.
7. **Modelo**: `claude-sonnet-5` por defecto. Subagentes baratos con `haiku`.
8. **El system prompt dice qué no adivinar**. El modelo conoce la fecha real y la usa si no le exiges pedirla por tool.
9. **Credenciales**: nunca escribas una API key en el archivo. El SDK usa la sesión de Claude Code o `ANTHROPIC_API_KEY` del entorno. Producción va con API key.
10. **Notebooks**: `await` directo; `asyncio.run` falla dentro de Jupyter.

## 5. Corre y verifica

```
uv sync && uv run python agente.py          # Python
npm install && npx tsx agente.ts            # TypeScript
```

Comprueba en la salida, en este orden:

1. El `init` lista exactamente las tools y servidores MCP que declaraste, ninguno más. Si aparecen conectores de claude.ai, falta `strict_mcp_config`.
2. El agente usó las tools esperadas (líneas `->`).
3. El recibo final: `subtype` `success`, turns y costo por debajo de los topes.
4. Existe `salidas/<fecha-hora>/` con `eventos.jsonl` y `transcript.md`. Abre el transcript y léelo: cada tool result debe aparecer como papel nuevo en la llamada siguiente, y los tokens leídos deben crecer de llamada en llamada.

Si falla, lee `references/gotchas.md` antes de cambiar código. No declares el agente terminado sin una corrida exitosa; si no se puede correr (sin sesión, sin red), dilo y deja el comando exacto.

## 6. Entrega

Responde con: la ruta de los archivos, el comando para correrlo, la ruta del `transcript.md` con la invitación a leerlo llamada por llamada, el recibo de la corrida (turns, llamadas al LLM, segundos, USD) y una tabla de tres filas con el system prompt, las tools y los guardrails que quedaron. Sugiere un único siguiente paso.
