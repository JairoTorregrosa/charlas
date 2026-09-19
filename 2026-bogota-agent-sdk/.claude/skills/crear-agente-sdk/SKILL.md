---
name: crear-agente-sdk
description: Crea un agente nuevo con la Claude Agent SDK, en Python o en TypeScript, a partir de un objetivo. Úsala cuando pidan "crea un agente", "hazme un agente que...", "agente con el Agent SDK", "claude-agent-sdk", "automatiza esto con un agente" o /crear-agente-sdk. Genera el archivo del agente, su carpeta de trabajo con skills, sus tools, sus guardrails (permisos, hook, topes) y lo corre una vez. No la uses para Claude Managed Agents, para llamadas sueltas a la Messages API ni para configurar subagentes de Claude Code (.claude/agents).
---

# Crear un agente con la Claude Agent SDK

Tú no escribes el loop: lo pone el SDK. Escribes tres cosas.

| Pieza | Qué es | Dónde queda |
|---|---|---|
| System prompt | quién es el agente y qué no debe adivinar | constante en el archivo del agente |
| Tools y workspace | tools nativas, tools propias, MCP, skills y archivos | opciones del `query()` y `workspace/` junto al agente |
| Guardrails | permisos, hooks y topes | opciones del `query()` |

## 1. Entrevista (una sola ronda, máximo cinco preguntas)

Si la idea es vaga («un agente de ventas», «automatizar mi trabajo»), abre `references/ideas.md`: trae las ocho categorías que más se repiten, con un primer agente pequeño, tools, MCP reales, skill y guardrail para cada una. Propón esa versión pequeña y pregunta solo lo que no venga ya en el pedido:

1. **Objetivo**: qué pregunta o tarea resuelve, en una frase. De ahí sale el prompt por defecto.
2. **Lenguaje**: Python o TypeScript. Si ya hay un `pyproject.toml` o un `package.json` en la carpeta, usa ese y no preguntes.
3. **Qué necesita tocar**: archivos locales, shell, web, un servicio externo (MCP), datos propios (tool propia).
4. **Qué no debe hacer nunca**: esto se vuelve `disallowed_tools` o un hook.
5. **Cómo corre**: una vez y sale (por defecto), o conversación de varios turnos.

Si el objetivo se resuelve con pasos fijos y conocidos, dilo: eso es un script o un workflow, y un agente sale más caro y menos predecible. Sigue solo si la persona confirma.

## 2. Decide las piezas

- **Tools nativas** (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebSearch`, `WebFetch`): declara en `tools` solo las que el objetivo exige. `tools=[]` deja al agente sin manos.
- **Tool propia**: para datos o acciones de tu código. Una función con nombre, descripción y esquema. Va dentro de un servidor MCP en proceso (`create_sdk_mcp_server` / `createSdkMcpServer`) y se llama `mcp__<servidor>__<tool>`.
- **MCP externo**: tools que hizo otro. Decláralo inline en `mcp_servers`. No lo pongas en `.mcp.json`: con `strict_mcp_config` ese archivo se ignora.
- **Skill**: un procedimiento que el agente debe seguir igual cada vez. `workspace/.claude/skills/<nombre>/SKILL.md`. Exige `setting_sources=["project"]`, `skills=["<nombre>"]` y `"Skill"` dentro de `tools`; sin la tool `Skill` el agente ve la skill y no puede abrirla.
Para elegir entre tool, MCP, skill, subagente y hook: `references/conceptos.md`.

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
